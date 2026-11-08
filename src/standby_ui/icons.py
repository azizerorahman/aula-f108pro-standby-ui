"""Small, vector-derived option symbols for the native 240x135 selector screens."""
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
MASKS={}
ICON_BOUNDS=[]
def mark(c,name,cx,cy,w,h,col):
    if name not in MASKS:
        mask=Image.open(ROOT/"assets/icons/raster"/(name+".png")).getchannel("A")
        assert mask.getbbox(),name
        MASKS[name]=mask.crop(mask.getbbox())
    mask=MASKS[name]
    scale=min(w/mask.width,h/mask.height)
    width,height=mask.width*scale,mask.height*scale
    # Match the approved Canvas's eightfold shape rasterization.
    factor=8
    hi,_=c._hi()
    mw,mh=max(1,round(width*factor)),max(1,round(height*factor))
    hi.paste(mask.resize((mw,mh),Image.Resampling.LANCZOS),(round((cx-width/2)*factor),round((cy-height/2)*factor)))
    c.paint(c._lo(hi),col)
    ICON_BOUNDS.append({"symbol":name,"bounds":[cx-width/2,cy-height/2,cx+width/2,cy+height/2]})
def connection_symbol(c,index,x,y,col):
    if index==0:mark(c,"usb",x,y,24,25,col)
    elif index==1:mark(c,"receiver",x,y,26,25,col)
    else:
        # The standard Bluetooth rune, without its enclosing brand badge.
        xx=x-9
        points=[(xx-6,y-7),(xx+6,y+5),(xx,y+11),(xx,y-11),(xx+6,y-5),(xx-6,y+7)]
        c.paint(c.line(points,2.0),col)
        ICON_BOUNDS.append({"symbol":"bluetooth-rune","bounds":[xx-7,y-12,xx+7,y+12]})
def system_symbol(c,index,x,y,col):
    if index==0:mark(c,"windows",x,y,25,25,col)
    elif index==1:mark(c,"apple",x,y,24,27,col)
    elif index==2:mark(c,"ios",x,y,32,24,col)
    else:mark(c,"android",x,y,32,23,col)
