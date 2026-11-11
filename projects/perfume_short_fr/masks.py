import subprocess,numpy as np,sys,os
from PIL import Image
from rembg import new_session, remove
V=sys.argv[1]; W,H=720,1280
s1=new_session("isnet-general-use"); s2=new_session("u2net_human_seg")
p=subprocess.Popen(["ffmpeg","-v","error","-i",V,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
i=0
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    out=f"masks/{i:05d}.png"
    if i%2==0 and not os.path.exists(out):
        im=Image.fromarray(np.frombuffer(b,np.uint8).reshape(H,W,3))
        m1=np.array(remove(im,session=s1,only_mask=True)); m2=np.array(remove(im,session=s2,only_mask=True))
        Image.fromarray(np.maximum(m1,m2)).resize((360,640),Image.BILINEAR).save(out)
    i+=1
    if i%100==0: print(i,flush=True)
print("done",i)
