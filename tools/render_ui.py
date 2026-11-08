"""Regenerate the complete UI offline into build/rendered/."""
from pathlib import Path
import sys, os, json, hashlib, math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from standby_ui import drawing, clock, navigation, effects, icons
OUT=ROOT/'build/rendered';ASSETS=OUT/'screens';ASSETS.mkdir(parents=True,exist_ok=True)
FD=ROOT/'assets/fonts'
Canvas,quant,CAT,GLYPH=drawing.Canvas,drawing.quant,drawing.CAT,drawing.GLYPH
BLACK=(0,0,0); WHITE=(255,255,255); SEC=(150,150,150); DIM=(60,60,63)
ORANGE=CAT["brightness"]; GREEN=CAT["speed"]; RED=CAT["volume"]; BLUE=CAT["connect"]
FONT_CACHE={}
def font(size,cn=False,weight=600):
    key=(size,cn,weight)
    if key not in FONT_CACHE:
        f=ImageFont.truetype(str(FD/("NotoSansSC-VF.ttf" if cn else "Inter-VF.ttf")),size)
        f.set_variation_by_axes([weight] if cn else [min(32,max(14,size)),weight])
        FONT_CACHE[key]=f
    return FONT_CACHE[key]
TEXT_BOUNDS=[]
def text(c,x,y,value,size=13,colour=WHITE,cn=False,weight=600,align="center"):
    f=font(size,cn,weight)
    m=Image.new("L",(240,135))
    d=ImageDraw.Draw(m)
    anchor={"center":"ms","left":"ls","right":"rs"}[align]
    box=d.textbbox((round(x),round(y)),value,font=f,anchor=anchor)
    if box[0]<0 or box[1]<0 or box[2]>240 or box[3]>135:
        raise AssertionError(("clipped text",value,box))
    TEXT_BOUNDS.append({"text":value,"bounds":box,"size":size})
    d.text((round(x),round(y)),value,font=f,fill=255,anchor=anchor)
    c.paint(np.asarray(m,dtype=np.float32)/255,colour)
def icon(c,key,x,y,k=.65,col=SEC):
    GLYPH[key](c,x,y,k,col,BLACK)
def rr(c,box,r,col):
    c.paint(c.rrect(*box,r),col)
def focus(c,box,r,col=WHITE):
    x0,y0,x1,y1=box
    outer=c.rrect(x0,y0,x1,y1,r)
    inner=c.rrect(x0+1.5,y0+1.5,x1-1.5,y1-1.5,max(0,r-1.5))
    c.paint(np.clip(outer-inner,0,1),col)
def pages(c,page,count):
    width=count*12+(count-1)*3
    for i in range(count):
        x=(240-width)/2+i*15
        rr(c,(x,123,x+12,127),2,(230,230,230) if i==page else (49,49,49))
IMAGES={};META=[]
def put(key,image,group,label,lang="shared",value=None):
    if key in IMAGES:raise AssertionError("duplicate "+key)
    im=image.convert("RGB") if isinstance(image,Image.Image) else quant(image.a)
    assert im.size==(240,135),(key,im.size)
    a=np.asarray(im,dtype=np.uint16)
    q=[(a[...,i]*n+127)//255 for i,n in ((0,31),(1,63),(2,31))]
    restored=np.stack([(q[0]<<3)|(q[0]>>2),(q[1]<<2)|(q[1]>>4),(q[2]<<3)|(q[2]>>2)],-1)
    assert np.array_equal(a,restored),("not RGB565",key)
    p=ASSETS/(key+".png");im.save(p,optimize=True)
    IMAGES[key]=im
    META.append({"id":key,"group":group,"label":label,"language":lang,"value":value,"file":"screens/"+p.name,
      "width":240,"height":135,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
# Approved artifacts are reused byte-for-byte at the pixel level.
names=["Connect","System","Effect","Colour","Brightness","Speed","Volume","Language"]
for i,name in enumerate(names):
    put("menu_"+str(i),navigation.render(drawing.page_screen(i//2,i%2),i//2,"segments"),"menu",name,value=i)
for lang in ("en","cn"):
    put("clock_"+lang,clock.HERO_EN if lang=="en" else clock.HERO_CN,"clock","Standby",lang)
for i in range(1,10):
    put("clock_state_"+str(i),clock.STATE_IMGS[i-1][2],"clock","Clock state "+str(i))
# Header-free level controls: centre the numeral and segmented bar as one group.
level_top=min(font(62,weight=720).getbbox(str(i),anchor="ms")[1] for i in range(6))
LEVEL_BASE=round((135-level_top-28)/2)
LEVEL_BAR_Y=LEVEL_BASE+20
for kind in ("brightness","speed"):
    for level in range(6):
        c=Canvas()
        text(c,120,LEVEL_BASE,str(level),62,weight=720)
        for i in range(5):
            x=(240-(5*33+4*4))/2+i*37
            rr(c,(x,LEVEL_BAR_Y,x+33,LEVEL_BAR_Y+8),4,CAT[kind] if i<level else DIM)
        put(kind+"_"+str(level),c,kind,"Level "+str(level),value=level)
# User-approved order: vendor language keys 521..540; local menu IDs 0..19.
MODE_DATA=json.loads((ROOT/"assets/effect_modes.json").read_text(encoding="utf-8"))
assert [m['id'] for m in MODE_DATA]==list(range(20))
EFFECTS=[(m['en'],m['cn']) for m in MODE_DATA]
import runpy
EFFECT_ART=vars(effects)
for lang in ("en","cn"):
    for selected in range(20):
        c=Canvas()
        page=selected//4
        for k in range(4):
            index=page*4+k
            x=62+(k%2)*116;y=34+(k//2)*49
            active=index==selected
            rr(c,(x-52,y-21,x+52,y+21),10,(24,28,34) if active else (14,17,21))
            if active:focus(c,(x-54,y-23,x+54,y+23),12)
            EFFECT_ART["draw_thumbnail"](c,MODE_DATA[index]["thumbnail_id"],x,y,active)
        effect_label=EFFECTS[selected][lang=="cn"]
        effect_size=14
        while font(effect_size,lang=="cn").getlength(effect_label)>160:effect_size-=1
        assert effect_size>=12
        text(c,10,126,effect_label,effect_size,cn=lang=="cn",align="left")
        # Five short segments, separate from the single selected-effect label.
        for p in range(5):
            px=178+p*11
            rr(c,(px,120,px+8,124),2,(230,230,230) if p==page else (49,49,49))
        put("effect_"+lang+"_"+str(selected),c,"effect",effect_label,lang,selected)
# Nine colour slots. Slot order is a design proposal pending the on-device enum map.
SWATCHES=[("Red",(255,69,58)),("Orange",ORANGE),("Yellow",(255,214,10)),("Green",GREEN),
 ("Cyan",(50,215,230)),("Blue",BLUE),("Purple",(191,90,242)),("White",WHITE),("Spectrum",None)]
for selected in range(9):
    c=Canvas()
    for i,(name,col) in enumerate(SWATCHES):
        x=30+45*i if i<5 else 52.5+45*(i-5)
        y=45.5 if i<5 else 89.5
        mask=c.circle(x,y,11)
        if col is None:
            import colorsys
            field=np.zeros((135,240,3),np.float32)
            for xx in range(240):field[:,xx]=np.array(colorsys.hsv_to_rgb(((xx-x)/24+.5)%1,.85,1))*255
            c.paint_field(mask,field)
        else:c.paint(mask,col)
        if i==selected:
            c.paint(c.ring(x,y,14,16),WHITE)
            c.paint(c.ring(x,y,11.8,13.4),BLACK)
    put("colour_"+str(selected),c,"colour",SWATCHES[selected][0],value=selected)
import runpy
OPTION_ICONS=vars(icons)
def choice_screen(kind,labels,sel,lang="en"):
    c=Canvas()
    count=len(labels)
    if count==2:
        xs,ys=[65,175],[67.5,67.5];w,h=94,60
    elif count==4:
        # Icon-only System selector: balanced rows, no category header.
        xs,ys=[76,164,76,164],[40,40,95,95];w,h=58,44
    else:
        # Connection option C: choices only, vertically centred.
        xs,ys=[46,120,194,83,157],[42,42,42,94,94];w,h=62,37
    for i,label in enumerate(labels):
        x,y=xs[i],ys[i];on=i==sel
        col=CAT[kind]
        fill=tuple(int(v*.22) for v in col) if on else (21,21,24)
        rr(c,(x-w/2,y-h/2,x+w/2,y+h/2),11,fill)
        if on:focus(c,(x-w/2-2,y-h/2-2,x+w/2+2,y+h/2+2),13)
        glyph_col=WHITE if on else SEC
        if kind=="connect":
            OPTION_ICONS["connection_symbol"](c,i,x,y,glyph_col)
            if i>=2:
                # Essential channel number only; no repeated option name.
                c.paint(c.circle(x+11,y+7,8),tuple(int(v*.4) for v in col) if on else (47,47,51))
                text(c,x+11,y+11,str(i-1),12,glyph_col,weight=650)
        elif kind=="system":
            OPTION_ICONS["system_symbol"](c,i,x,y,glyph_col)
        else:
            cn=any(ord(ch)>127 for ch in label)
            size=22 if cn else 18
            bounds=font(size,cn=cn).getbbox(label,anchor="ms")
            baseline=round(y-(bounds[1]+bounds[3])/2)
            text(c,x,baseline,label,size,glyph_col,cn=cn)
    return c
CONNECT=["USB","2.4G","BT 1","BT 2","BT 3"]
SYSTEM=["Windows","macOS","iOS","Android"]
for i,label in enumerate(CONNECT):
    put("connect_"+str(i),choice_screen("connect",CONNECT,i),"connect",label,value=i)
for i,label in enumerate(SYSTEM):
    put("system_"+str(i),choice_screen("system",SYSTEM,i),"system",label,value=i)
for i in range(2):
    put("language_"+str(i),choice_screen("language",["English","中文"],i),"language",["English","中文"][i],value=i)
# Volume shows action feedback, without inventing a host volume readback.
for value,label in enumerate(("Quieter","Ready","Louder")):
    c=Canvas();y=67.5
    icon(c,"volume",120,y,1.55,WHITE)
    for i,x in enumerate((54,186)):
        active=(value==0 and i==0) or (value==2 and i==1)
        fill=tuple(int(v*.22) for v in RED) if active else (23,23,26)
        rr(c,(x-23,y-22,x+23,y+22),11,fill)
        if active:focus(c,(x-25,y-24,x+25,y+24),13)
        col=WHITE if active else SEC
        c.paint(c.line([(x-7,y),(x+7,y)],2.4),col)
        if i==1:c.paint(c.line([(x,y-7),(x,y+7)],2.4),col)
    put("volume_"+str(value),c,"volume",label,value=value)
# Pairing and result screens: one centred icon, with no on-screen text.
STATUS={
 "pair_bt":("Pairing","蓝牙配对","Select BT on your device","请在设备上选择蓝牙"),
 "pair_radio":("Connecting","正在连接","Insert the USB receiver","请插入无线接收器"),
 "success":("Connected","连接成功","Ready to type","可以开始输入"),
 "timeout":("Not connected","连接超时","Press to try again","按下旋钮重试"),
 "cable":("Connect USB","连接数据线","Use a USB data cable","请连接 USB 数据线"),
 "saved":("Saved","已保存","Press to return","按下旋钮返回")}
for lang in ("en","cn"):
    cn=lang=="cn"
    for kind,msg in STATUS.items():
        frames=3 if kind in ("pair_bt","pair_radio") else 1
        for frame in range(frames):
            c=Canvas();col=GREEN if kind in ("success","saved") else RED if kind=="timeout" else BLUE
            x,y=120,67.5
            c.paint(c.circle(x,y,34),tuple(int(v*.16) for v in col))
            if kind in ("success","saved"):
                c.paint(c.line([(x-15,y),(x-4,y+11),(x+17,y-12)],4),col)
            elif kind=="timeout":
                c.paint(c.line([(x,y-16),(x,y+4)],4),col)
                c.paint(c.circle(x,y+16,2.5),col)
            elif kind=="cable":
                OPTION_ICONS["mark"](c,"usb",x,y,32,38,col)
            else:
                c.paint(c.circle(x,y+12,3),col)
                for ring in range(3):
                    c.paint(c.arc(x,y+12,8+ring*9,3,220,320),col if ring<=frame else (35,35,39))
            put("status_"+lang+"_"+kind+"_"+str(frame),c,"status",msg[1 if cn else 0],lang,kind)
# Unbranded boot reveal: orange colon resolves into the approved clock. 0.8 seconds.
boot=[]
for i in range(20):
    t=i/19
    c=Canvas()
    if t<.45:
        alpha=min(1,t/.22)
        for yy in (57,78):rr(c,(115,yy-5,125,yy+5),3,tuple(int(v*alpha) for v in ORANGE))
    else:
        target=np.asarray(IMAGES["clock_en"],np.float32)
        u=(t-.45)/.55
        c.a=target*(u*u*(3-2*u))
    key="boot_"+str(i).zfill(2)
    put(key,c,"boot","Boot frame "+str(i),value=i)
    boot.append(IMAGES[key])
boot[0].save(OUT/"boot.gif",save_all=True,append_images=boot[1:],duration=[40]*19+[300],disposal=2)

(OUT/"manifest.json").write_text(json.dumps({"screens":META},ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Rendered {len(META)} screens to build/rendered/")
