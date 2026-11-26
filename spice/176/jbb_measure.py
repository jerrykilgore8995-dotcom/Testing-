import pathlib,re,subprocess,json
import numpy as np
p=pathlib.Path(__file__).resolve().parent
base=(p/'powered.cir').read_text()
for freq in (20,50,100):
 for ratio in (2,4,8,12):
  for attack in (.5,.99,1):
   for loss in (0,10,20):
    pair=[]
    for on in (0,1):
     deck=base
     for k,v in dict(FREQ=freq,RATIO=ratio,ATTACK=attack,LOSSDB=loss,LIMITING=on).items():
      deck=re.sub(r'(?<=\b'+k+r'=)[^\s]+',str(v),deck,count=1)
     (p/'jbb-run.cir').write_text(deck)
     log=p/f'jbb-{freq}-{ratio}-{attack}-{loss}-{on}.log'
     with log.open('w') as out: subprocess.run(['ngspice','-b','jbb-run.cir'],cwd=p,stdout=out,stderr=subprocess.STDOUT,check=True)
     z=np.loadtxt(p/'powered.txt',skiprows=1)
     if z[-1,0]<4.999: raise RuntimeError('Incomplete transient')
     t=np.arange(4,5,1/44100); y=np.column_stack([np.interp(t,z[:,0],z[:,j]) for j in range(1,z.shape[1])])
     a=np.array([2*abs(np.mean(y[:,5]*np.exp(-2j*np.pi*k*freq*t))) for k in range(1,21)])
     if a[0]<1e-10: raise RuntimeError('Zero fundamental')
     pair.append(dict(limit=on,fundamental_vpk=float(a[0]),thd_pct=float(100*np.linalg.norm(a[1:])/a[0]),cv_mVpp=float(1000*np.ptp(y[:,4])),rectifier_mVpp=float(1000*np.ptp(y[:,6])),bias_mVpp=float(1000*np.ptp(y[:,7])),cv_2f_mVpk=float(2000*abs(np.mean(y[:,4]*np.exp(-4j*np.pi*freq*t)))),harmonics_db=(20*np.log10(np.maximum(a[1:]/a[0],1e-15))).tolist()))
    row=dict(freq=freq,ratio=ratio,attack=attack,loss=loss,gr_db=float(20*np.log10(pair[0]['fundamental_vpk']/pair[1]['fundamental_vpk'])),results=pair)
    with (p/'jbb-results.jsonl').open('a') as fp: fp.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
