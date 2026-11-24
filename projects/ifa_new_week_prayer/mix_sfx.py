import numpy as np, wave, json, sys
sr=44100; E=json.load(open(sys.argv[1])); SRC=E['src_dur']; TOT=SRC+E['outro']; n=int(TOT*sr); t=np.arange(n)/sr
out=np.zeros(n); pad=np.zeros(n)
for f,a in [(73.42,.5),(110,.35),(146.83,.3),(185,.12),(220,.15),(293.66,.06)]:
    pad+=a*np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.07*t))*(0.8+0.2*np.sin(2*np.pi*0.13*t+f))
k=int(sr*0.0006); pad=np.convolve(pad,np.ones(k)/k,'same')
pad*=np.clip(t/3,0,1)*np.where(t<SRC,1.0,1.0+1.8*np.clip((t-SRC)/0.8,0,1))*np.clip((TOT-t)/1.2,0,1)
out+=pad/np.abs(pad).max()*0.07
rng=np.random.default_rng(1)
def add(sig,at,g):
    i=int(at*sr); j=min(n,i+len(sig)); out[i:j]+=g*sig[:j-i]
def whoosh(d=0.7):
    m=int(d*sr); x=rng.standard_normal(m); tt=np.arange(m)/sr; y=np.zeros(m); s=0
    for i in range(m): s+=(0.02+0.25*i/m)*(x[i]-s); y[i]=s
    return y*np.sin(np.pi*tt/d)**2/np.abs(y).max()
def ding(f,d=1.2,b=0.0):
    tt=np.arange(int(d*sr))/sr; return (np.sin(2*np.pi*f*tt)+.4*np.sin(2*np.pi*f*2.01*tt)+.2*np.sin(2*np.pi*f*3*tt))*np.exp(-tt*(4+b))/1.6
def pop():
    tt=np.arange(int(.18*sr))/sr; f=900*np.exp(-tt*18)+250; return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-tt*25)
W=whoosh()
for s in E['sections'][1:]: add(W,s['start']-0.45,0.22)
add(W,SRC-0.45,0.25)
for s in E['stickers']:
    if s['kind']=='orisha': add(ding(784),s['t'],0.12); add(ding(1175),s['t']+.08,0.06)
    else: add(pop(),s['t'],0.35); add(ding(1046,.8,2),s['t']+.04,0.12)
add(ding(1318,1.0,1),0.25,0.08); add(pop(),0.2,0.25)
for i,f in enumerate([587.3,740,880,1174.7]): add(ding(f,2.0),SRC+0.3+i*0.12,0.1)
x=np.clip(out,-1,1); w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
print(TOT)
