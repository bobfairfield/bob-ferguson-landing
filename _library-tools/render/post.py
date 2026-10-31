import sys
sys.argv=[sys.argv[0],"."]
import reel as R
from reel import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
Y0=285; PHH=1350
bg=cover(R.hero,1.0,0.5,0.62)
arr=np.asarray(bg,dtype=np.float32)
bright=np.clip(arr-110,0,255)
bl=np.asarray(Image.fromarray(bright.astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)),dtype=np.float32)
arr=arr*1.05+bl*0.8
# vignette within window only
arr=darken(arr,1.3,top=False,bot=False)
img=Image.fromarray(np.clip(arr,0,255).astype(np.uint8)).convert("RGBA")
# top and bottom gradient inside window
g=Image.new("RGBA",(W,H),(0,0,0,0));gd=ImageDraw.Draw(g)
for i in range(300):
    a=int(170*(1-i/300)**1.6); gd.line([(0,Y0+i),(W,Y0+i)],fill=(40,4,20,a))
for i in range(520):
    a=int(235*(i/520)**0.9); gd.line([(0,Y0+PHH-520+i),(W,Y0+PHH-520+i)],fill=(40,4,20,a))
img.alpha_composite(g)
img.alpha_composite(text_layer(["SHOWN TO INCREASE"],Y0+55,56,"Bold",ROSE,track=4))
vl=R.L["vo2"]; s=0.52
sc=vl.resize((int(W*s),int(H*s)),Image.LANCZOS)
tmp=Image.new("RGBA",(W,H),(0,0,0,0)); tmp.paste(sc,((W-sc.width)//2,Y0+120-int(655*s)),sc); img.alpha_composite(tmp)
img.alpha_composite(text_layer(["WITHOUT EXERCISE*"],Y0+PHH-330,86,"Black",(255,255,255),track=0))
img.alpha_composite(text_layer(["+3.2 POINTS GREATER VO2 MAX^"],Y0+PHH-215,40,"Bold",ROSE,track=2,shadow=False))
img.alpha_composite(text_layer(["8 YEARS OF CELLULAR AGING ERASED^"],Y0+PHH-160,40,"Bold",(255,255,255),track=2,shadow=False))
f=ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf",21)
d=ImageDraw.Draw(img)
for n,t in enumerate(["*Not evaluated by the FDA. Not intended to diagnose, treat, cure, or prevent any disease.","^Two-month study. Details in post."]):
    tw=d.textlength(t,font=f); d.text(((W-tw)/2,Y0+PHH-66+n*28),t,font=f,fill=(255,225,235,230))
out=img.convert("RGB").crop((0,Y0,W,Y0+PHH))
out.save("fb/Vivix_FB_Post_1080x1350.png"); print(out.size)
