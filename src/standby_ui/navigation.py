"""Segmented navigation, isolated from the icon artwork."""
from PIL import Image, ImageDraw
S = 8
def quantize(im):
    # RGB565, expanded to RGB888 for a normal PNG.
    return Image.merge("RGB", tuple(ch.point(
        lambda v, n=n: ((round(v*n/255)<<3)|(round(v*n/255)>>2)) if n==31
        else ((round(v*n/255)<<2)|(round(v*n/255)>>4)))
        for ch,n in zip(im.split(),(31,63,31))))
def render(src, page, mode):
    out = src.copy().convert("RGB")
    # Navigation is isolated from the accepted icon artwork.
    out.paste((0,0,0),(0,110,240,135))
    nav = Image.new("RGB",(240*S,25*S))
    d = ImageDraw.Draw(nav)
    def rr(box, radius, fill):
        d.rounded_rectangle(tuple(round(x*S) for x in box),radius=round(radius*S),fill=fill)
    def line(points,fill,width=1.5):
        pts = [(round(x*S),round(y*S)) for x,y in points]
        d.line(pts,fill=fill,width=round(width*S),joint="curve")
    white = (230,230,230)
    if mode in ("track","arrows"):
        x0 = 92 if mode=="track" else 100
        width = 56 if mode=="track" else 40
        rr((x0,9,x0+width,13),2,(40,40,40))
        slot = width/4
        x = x0+slot*page
        rr((x,9,x+slot,13),2,white)
        if mode=="arrows":
            line([(83,8),(80,11),(83,14)],(108,108,108))
            line([(157,8),(160,11),(157,14)],(108,108,108))
    else:
        for i in range(4):
            x = 91+15*i
            rr((x,9,x+12,13),2,white if i==page else (49,49,49))
    nav = quantize(nav.resize((240,25),Image.Resampling.LANCZOS))
    out.paste(nav,(0,110))
    assert out.crop((0,0,240,110)).tobytes()==src.convert("RGB").crop((0,0,240,110)).tobytes()
    return out
