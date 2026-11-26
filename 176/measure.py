import pathlib, subprocess, tempfile, csv, re
import numpy as np
base=pathlib.Path(__file__).with_name("jbb176-draft.cir").read_text()
rows=[]
for f in (20,50,100):
    for limit in (0,1):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            deck=re.sub(r'F=20 AMP=1.737 RA=1k REL=2.5Meg RATIO=4 LIMIT=1',f'F={f} AMP=1.737 RA=1k REL=2.5Meg RATIO=4 LIMIT={limit}',base)
            (p/'test.cir').write_text(deck)
            run=subprocess.run(['ngspice','-b','test.cir'],cwd=p,capture_output=True,text=True)
            (pathlib.Path(__file__).parent/f'{f}Hz-limit{limit}.log').write_text(run.stdout+run.stderr)
            if run.returncode or not (p/'trace.dat').exists():
                raise RuntimeError(run.stdout+run.stderr)
            a=np.loadtxt(p/'trace.dat',skiprows=1)
            t=a[:,0]
            if t[-1]<7.99: raise RuntimeError('Incomplete transient')
            grid=np.arange(7,8,1/40000)
            y=np.interp(grid,t,a[:,1])
            hs=np.array([2*abs(np.mean(y*np.exp(-2j*np.pi*k*f*grid))) for k in range(1,21)])
            if hs[0]<1e-9: raise RuntimeError('No fundamental')
            cv=np.interp(grid,t,a[:,2]); rect=np.interp(grid,t,a[:,3])
            rows.append([f,limit,100*np.linalg.norm(hs[1:])/hs[0],1000*np.ptp(cv),1000*np.ptp(rect),np.mean(cv),hs[0],*list(20*np.log10(np.maximum(hs[1:]/hs[0],1e-15)))])
with pathlib.Path(__file__).with_name('results.csv').open('w',newline='') as fp:
    w=csv.writer(fp);w.writerow(['Hz','limit','THD_percent_K2_K20','grid_ripple_mVpp','rect_ripple_mVpp','grid_mean_V','fundamental_peak_V',*[f'K{k}_dB_relative' for k in range(2,21)]]);w.writerows(rows)
print(rows)
