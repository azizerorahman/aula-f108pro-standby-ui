"""Illustrated lighting thumbnails; not captures or simulations of device firmware."""
import math, colorsys
import numpy as np
from PIL import Image, ImageDraw
PALETTE=[(55,215,222),(81,133,255),(169,106,244),(239,104,175)]
def mix(a,b,t):return tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3))
def rgb(h):return tuple(round(v*255) for v in colorsys.hsv_to_rgb(h%1,.72,1))
def field(effect,row,col):
    x=(col-5.5)/5.5;y=(row-1.5)/1.5
    radius=math.hypot(x,y*.65)
    if effect==0:return (66,72,81),.18
    if effect==1:return PALETTE[0],.82
    if effect==2:return PALETTE[0],max(.05,math.exp(-((col-4)**2+(row-2)**2)*1.35))
    if effect==3:return PALETTE[1],.82*(1-.94*math.exp(-((col-6)**2+(row-1)**2)*1.3))
    if effect==4:
        v=((col*17+row*31)%19)
        return ((242,238,255) if v<3 else PALETTE[2]),(.95 if v<3 else .13)
    if effect==5:
        lead=(col*7)%5
        return PALETTE[1],max(.07,math.exp(-abs(row-lead)*1.1))
    if effect==6:return rgb(col*.14+row*.19),.78
    if effect==7:return PALETTE[2],.2+.75*math.exp(-radius*radius*1.5)
    if effect==8:return rgb(col/12),.86
    if effect==9:return PALETTE[0],.1+.85*math.exp(-((radius-.6)/.2)**2)
    if effect==10:return PALETTE[1],.08+.88*math.exp(-((col-4)/2)**2)
    if effect==11:return (84,221,156),.08+.9*math.exp(-((row-1.1)/.8)**2)
    if effect==12:return rgb(math.atan2(y*.7,x)/(2*math.pi)+.6),.28+.6*(1-min(1,radius/1.6))
    if effect==13:
        angle=math.atan2(y,x)
        return (255,148,160),.08+.88*max(0,math.cos(angle*5))**4*math.exp(-radius*.65)
    if effect==14:return (228,195,255),.07+.92*math.exp(-((col-8)/1.1)**2)*(.45+.55*(1-row/3))
    if effect==15:return PALETTE[0],.08+.86*(.5+.5*math.cos(radius*15))**3
    if effect==16:
        band=1.5+math.sin(col*.65)
        return rgb(.48+col*.018),.1+.84*math.exp(-((row-band)/.7)**2)
    if effect==17:
        dist=min(abs(col-2),abs(col-6),abs(col-10))
        return PALETTE[3],.1+.82*math.exp(-dist*dist/.9)
    if effect==18:return (255,179,90),.08+.9*math.exp(-((col-3-row*2)/1.8)**2)
    return PALETTE[1] if row<2 else PALETTE[2],.1+.86*math.exp(-((col-(3 if row<2 else 8))/1.9)**2)
CACHE={}
def draw_thumbnail(c,effect,cx,cy,selected):
    key=(effect,selected)
    if key not in CACHE:
        s=8;im=Image.new("RGBA",(104*s,42*s));d=ImageDraw.Draw(im)
        def rect(box,r,fill):
            d.rounded_rectangle(tuple(round(v*s) for v in box),radius=round(r*s),fill=tuple(fill)+(255,))
        rect((6,7,98,35),4,(24,28,34) if selected else (20,23,28))
        keyw,keyh,gapx,gapy=5.9,4.3,1.5,1.6
        width=12*keyw+11*gapx;height=4*keyh+3*gapy
        x0,y0=(104-width)/2,(42-height)/2
        for row in range(4):
            col=0
            while col<12:
                span=4 if row==3 and col==4 else 1
                sample=col+(span-1)/2
                hue,level=field(effect,row,sample)
                colour=mix((42,47,56),hue,level)
                if not selected:colour=tuple(round(v*.62) for v in colour)
                x=x0+col*(keyw+gapx);y=y0+row*(keyh+gapy)
                rect((x,y,x+span*keyw+(span-1)*gapx,y+keyh),1.1,colour)
                col+=span
        CACHE[key]=im.resize((104,42),Image.Resampling.LANCZOS)
    image=np.asarray(CACHE[key],np.float32)
    x0,y0=round(cx-52),round(cy-21)
    alpha=image[:,:,3:4]/255
    c.a[y0:y0+42,x0:x0+104]=c.a[y0:y0+42,x0:x0+104]*(1-alpha)+image[:,:,:3]*alpha
