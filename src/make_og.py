from PIL import Image, ImageDraw, ImageFont
import math
W,H=1200,630
im=Image.new("RGB",(W,H),(9,11,16)); d=ImageDraw.Draw(im)
for i in range(30):
    base=H/30*i+10; pts=[]
    for x in range(0,W+12,12):
        y=base+math.sin(x*0.0042+i*0.21)*18+math.sin(x*0.0011-i*0.13)*30
        pts.append((x,y))
    a=int(18+40*(i/30)**1.4)
    col=(140,195,160) if i%6==0 else (166,173,185)
    c=tuple(int(9+(v-9)*a/255) for v in col)
    d.line(pts,fill=c,width=1)
F="/usr/share/fonts/opentype/inter/"
def f(n,s): return ImageFont.truetype(F+n,s)
def spaced(xy,t,font,fill,sp):
    x,y=xy
    for ch in t:
        d.text((x,y),ch,font=font,fill=fill); x+=d.textlength(ch,font=font)+sp
spaced((80,70),"NASHIONAL",f("Inter-Bold.otf",30),(238,240,243),10)
spaced((82,112),"INVESTMENTS",f("Inter-Medium.otf",13),(166,173,185),9)
hf=f("Inter-SemiBold.otf",58)
lines=["Fiduciary advice for DSTs,","Opportunity Zones and","tax-driven alternatives."]
y=230
for l in lines:
    d.text((80,y),l,font=hf,fill=(238,240,243)); y+=70
spaced((82,H-80),"TEXAS-REGISTERED INVESTMENT ADVISER  ·  CFP®  ·  CPA  ·  CBDA",f("Inter-Medium.otf",15),(140,195,160),3)
im.save("assets/img/og-default.png",optimize=True)
open("assets/favicon.svg","w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#090B10"/><path d="M18 46V18l28 28V18" fill="none" stroke="#EEF0F3" stroke-width="5" stroke-linecap="square"/><path d="M46 18v6" stroke="#8CC3A0" stroke-width="5"/></svg>')
print("ok")
