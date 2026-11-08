"""Clock layout, English/Chinese typography and example states."""
import sys, os, io, re, base64, datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
FD = str(Path(__file__).resolve().parents[2] / "assets/fonts")
S = 8
INTER, NOTO = os.path.join(FD, "Inter-VF.ttf"), os.path.join(FD, "NotoSansSC-VF.ttf")

def snap(c):
    r5, g6, b5 = round(c[0] * 31 / 255), round(c[1] * 63 / 255), round(c[2] * 31 / 255)
    return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))
def quant(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint16)
    r, g, b = (a[..., 0] * 31 + 127) // 255, (a[..., 1] * 63 + 127) // 255, (a[..., 2] * 31 + 127) // 255
    return Image.fromarray(np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.uint8), "RGB")

# Match the reference text metrics even when a Pillow build includes optional RAQM.
_fc = {}
def inter(px, w=600):
    k = ("i", px, w)
    if k not in _fc:
        f = ImageFont.truetype(INTER, px, layout_engine=ImageFont.Layout.BASIC); f.set_variation_by_axes([min(32, max(14, px)), w]); _fc[k] = f
    return _fc[k]
def noto(px, w=500):
    k = ("n", px, w)
    if k not in _fc:
        f = ImageFont.truetype(NOTO, px, layout_engine=ImageFont.Layout.BASIC); f.set_variation_by_axes([w]); _fc[k] = f
    return _fc[k]

# ---------------- tokens ----------------
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
SEC, TER = snap((150, 150, 150)), snap((100, 100, 100))
ORANGE, YELLOW, RED, GREEN = snap((255, 159, 10)), snap((255, 214, 10)), snap((255, 69, 58)), snap((48, 209, 88))
M = 10                 # side margins
TOP_BASE, TOP_CY = 20, 15.5
BOT_BASE, BOT_CY = 124, 119.5
PILL = (8, 24)         # caps pill rows
TIME_MID = 69.5        # centre of the band between the pill (24) and the bottom row cap height (115)

# ---------------- canvas ----------------
class Canvas:
    def __init__(s):
        s.a = np.zeros((135, 240, 3), np.float32)
    def _hi(s):
        m = Image.new("L", (240 * S, 135 * S), 0); return m, ImageDraw.Draw(m)
    def _lo(s, m): return np.asarray(m.reduce(S), np.float32) / 255.0
    def paint(s, k, col, alpha=1.0):
        k = (k * alpha)[..., None]; s.a = s.a * (1 - k) + np.asarray(col, np.float32) * k
    def rrect(s, x0, y0, x1, y1, r):
        m, d = s._hi(); d.rounded_rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], radius=max(0, r) * S, fill=255); return s._lo(m)
    def circle(s, cx, cy, r):
        m, d = s._hi(); d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S - 1, (cy + r) * S - 1], fill=255); return s._lo(m)
    def chord(s, x0, y0, x1, y1, a0, a1):
        m, d = s._hi(); d.chord([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], a0, a1, fill=255); return s._lo(m)
    def arc(s, cx, cy, r, w, a0, a1):
        m, d = s._hi(); R = r + w / 2
        d.arc([(cx - R) * S, (cy - R) * S, (cx + R) * S - 1, (cy + R) * S - 1], a0, a1, fill=255, width=max(1, round(w * S))); return s._lo(m)
    def line(s, pts, w, cap=True):
        m, d = s._hi(); P = [(x * S, y * S) for x, y in pts]
        d.line(P, fill=255, width=max(1, round(w * S)), joint="curve")
        if cap:
            r = w * S / 2
            for px, py in (P[0], P[-1]):
                d.ellipse([px - r, py - r, px + r - 1, py + r - 1], fill=255)
        return s._lo(m)
    def poly(s, pts):
        P = np.array([(x * S, y * S) for x, y in pts], float); n = len(P)
        ys, xs = np.mgrid[0:135 * S, 0:240 * S] + 0.5
        inside = np.zeros(xs.shape, bool)
        for i in range(n):
            (x1, y1), (x2, y2) = P[i], P[(i + 1) % n]
            if y1 == y2:
                continue
            cond = ((y1 <= ys) & (ys < y2)) | ((y2 <= ys) & (ys < y1))
            inside ^= cond & (xs < x1 + (ys - y1) * (x2 - x1) / (y2 - y1))
        return inside.reshape(135, S, 240, S).mean(axis=(1, 3)).astype(np.float32)
    def text(s, x, base, txt, font):
        m = Image.new("L", (240, 135), 0); ImageDraw.Draw(m).text((round(x), round(base)), txt, font=font, fill=255, anchor="ls")
        return np.asarray(m, np.float32) / 255.0

_ink = {}
def ink(txt, font):
    k = (txt, id(font))
    if k not in _ink:
        m = Image.new("L", (520, 260), 0); ImageDraw.Draw(m).text((80, 190), txt, font=font, fill=255, anchor="ls")
        ys, xs = np.nonzero(np.asarray(m) > 40)
        _ink[k] = (xs.min() - 80, ys.min() - 190, xs.max() + 1 - 80, ys.max() + 1 - 190)
    return _ink[k]
def tw(txt, font, track=0.0): return sum(font.getlength(c) for c in txt) + track * max(0, len(txt) - 1)
def tracked(c, x, base, txt, font, col, track=0.0):
    for ch in txt:
        c.paint(c.text(x, base, ch, font), col); x += font.getlength(ch) + track
    return x - track
def runs(txt):
    out = []
    for ch in txt:
        k = ord(ch) > 0x2E7F
        if out and out[-1][1] == k:
            out[-1][0] += ch
        else:
            out.append([ch, k])
    return out
def mixed_w(txt, px, wl=600, wc=500): return sum(noto(px, wc).getlength(r) if k else inter(px, wl).getlength(r) for r, k in runs(txt))
def mixed(c, x, base, txt, px, col, wl=600, wc=500):
    for r, k in runs(txt):
        f = noto(px, wc) if k else inter(px, wl)
        c.paint(c.text(x, base, r, f), col); x += f.getlength(r)
    return x

# ---------------- icons ----------------
def ic_bt(c, cx, cy, k, col):
    c.paint(c.line([(cx - 3 * k, cy - 3 * k), (cx + 3 * k, cy + 2.6 * k), (cx, cy + 5.4 * k), (cx, cy - 5.4 * k), (cx + 3 * k, cy - 2.6 * k), (cx - 3 * k, cy + 3 * k)], 1.4 * k), col)
def ic_usb(c, cx, cy, k, col):
    c.paint(c.line([(cx, cy - 3.6 * k), (cx, cy + 3.6 * k)], 1.3 * k, cap=False), col)
    c.paint(c.poly([(cx - 2.2 * k, cy - 2.7 * k), (cx, cy - 6 * k), (cx + 2.2 * k, cy - 2.7 * k)]), col)
    c.paint(c.circle(cx, cy + 3.9 * k, 1.6 * k), col)
    c.paint(c.line([(cx, cy + 2 * k), (cx - 3.1 * k, cy - 0.4 * k), (cx - 3.1 * k, cy - 1.4 * k)], 1.15 * k), col)
    c.paint(c.circle(cx - 3.1 * k, cy - 2 * k, 1.2 * k), col)
    c.paint(c.line([(cx, cy + 0.5 * k), (cx + 3.1 * k, cy - 1.5 * k), (cx + 3.1 * k, cy - 2.2 * k)], 1.15 * k), col)
    c.paint(c.rrect(cx + 2 * k, cy - 4.4 * k, cx + 4.2 * k, cy - 2.2 * k, 0.2), col)
def ic_waves(c, cx, cy, k, col):
    c.paint(c.circle(cx, cy, 1.4 * k), col)
    for r in (3.4 * k, 6.0 * k):
        c.paint(c.arc(cx, cy, r, 1.3, -42, 42), col); c.paint(c.arc(cx, cy, r, 1.3, 138, 222), col)
ICON = {"bt": (ic_bt, 7.0), "usb": (ic_usb, 8.6), "24g": (ic_waves, 14.4)}
def ic_lock(c, cx, cy, k, col):
    c.paint(c.rrect(cx - 3.6 * k, cy - 0.6 * k, cx + 3.6 * k, cy + 4.6 * k, 1.1 * k), col)
    c.paint(c.arc(cx, cy - 1.6 * k, 2.2 * k, 1.25 * k, 180, 360), col)
    for sx in (-1, 1):
        c.paint(c.line([(cx + sx * 2.2 * k, cy - 1.6 * k), (cx + sx * 2.2 * k, cy)], 1.25 * k, cap=False), col)
def ic_caps(c, cx, cy, k, col):
    c.paint(c.poly([(cx, cy - 6 * k), (cx + 5.5 * k, cy - 0.2 * k), (cx + 2.2 * k, cy - 0.2 * k), (cx + 2.2 * k, cy + 2.6 * k),
                    (cx - 2.2 * k, cy + 2.6 * k), (cx - 2.2 * k, cy - 0.2 * k), (cx - 5.5 * k, cy - 0.2 * k)]), col)
    c.paint(c.rrect(cx - 2.2 * k, cy + 4.2 * k, cx + 2.2 * k, cy + 6 * k, 0.4), col)
def ic_bolt(c, cx, cy, k, col):
    c.paint(c.poly([(cx + 1.3 * k, cy - 5.2 * k), (cx - 3.6 * k, cy + 0.9 * k), (cx - 0.3 * k, cy + 0.9 * k), (cx - 1.3 * k, cy + 5.2 * k),
                    (cx + 3.6 * k, cy - 0.9 * k), (cx + 0.3 * k, cy - 0.9 * k)]), col)
def os_glyph(c, kind, cx, cy, col):
    if kind == "win":
        for dx in (-4.5, 0.5):
            for dy in (-4.5, 0.5):
                c.paint(c.rrect(cx + dx, cy + dy, cx + dx + 4, cy + dy + 4, 0.5), col)
    elif kind in ("mac", "ios"):
        txt, f = ("⌘", inter(14, 600)) if kind == "mac" else ("iOS", inter(12, 650))
        x0, y0, x1, y1 = ink(txt, f); c.paint(c.text(round(cx - (x0 + x1) / 2), round(cy - (y0 + y1) / 2), txt, f), col)
    else:
        c.paint(c.chord(cx - 5.5, cy - 3, cx + 5.5, cy + 8, 180, 360), col)
        for ex in (cx - 2.4, cx + 2.4):
            c.paint(c.circle(ex, cy - 0.3, 0.75), BLACK)
        c.paint(c.line([(cx - 3.4, cy - 2.6), (cx - 4.6, cy - 4.6)], 1.0), col); c.paint(c.line([(cx + 3.4, cy - 2.6), (cx + 4.6, cy - 4.6)], 1.0), col)
OS_W = {"win": 9, "mac": 12, "ios": 18, "android": 11}

# ---------------- dates ----------------
WD_S = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MO_S = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WD_CS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
DATE_F = lambda: inter(13, 600)
DATE_TRK = 0.1
def date_width(lang, d):
    if lang == "en":
        return tw(WD_S[d.weekday()], DATE_F(), DATE_TRK) + 6 + tw(f"{d.day} {MO_S[d.month - 1]}", DATE_F(), DATE_TRK)
    return mixed_w(f"{d.month}月{d.day}日", 12) + 6 + mixed_w(WD_CS[d.weekday()], 12)
def draw_date(c, lang, d):
    if lang == "en":
        x = tracked(c, M, TOP_BASE, WD_S[d.weekday()], DATE_F(), ORANGE, DATE_TRK)
        tracked(c, x + 6, TOP_BASE, f"{d.day} {MO_S[d.month - 1]}", DATE_F(), SEC, DATE_TRK)
    else:
        x = mixed(c, M, TOP_BASE, f"{d.month}月{d.day}日", 12, SEC)
        mixed(c, x + 6, TOP_BASE, WD_CS[d.weekday()], 12, ORANGE)

# ---------------- battery ----------------
BAT_W, BAT_H = 31, 14
BAT_X0 = 240 - M - 3 - BAT_W            # body 196..227, nub 228..230
def bat_col(p, ch): return GREEN if ch else RED if p <= 20 else WHITE
def draw_battery(c, p, ch):
    x0, y0 = BAT_X0, TOP_CY - BAT_H / 2
    body = c.rrect(x0, y0, x0 + BAT_W, y0 + BAT_H, 4.5); c.paint(body, TER)
    c.paint(np.minimum(body, c.rrect(x0, y0, x0 + BAT_W * max(p, 5) / 100, y0 + BAT_H, 0)), bat_col(p, ch))
    c.paint(c.rrect(x0 + BAT_W + 1, TOP_CY - 2.5, x0 + BAT_W + 3, TOP_CY + 2.5, 1), bat_col(p, ch) if p >= 100 else TER)
    f = inter(11, 760); s = str(p); x0i, y0i, x1i, y1i = ink(s, f)
    c.paint(c.text(round(x0 + BAT_W / 2 - (x0i + x1i) / 2), round(TOP_CY - (y0i + y1i) / 2), s, f), BLACK)
    if ch:
        ic_bolt(c, x0 - 7, TOP_CY, 1.0, WHITE)
BAT_LEFT = BAT_X0 - 11                   # leftmost pixel used by the cluster (bolt when charging)

# ---------------- caps pill (joins the status cluster, left of the battery) ----------------
def pill_geom(lang):
    if lang == "en":
        lw = tw("CAPS", inter(10, 760), 0.7)
    else:
        lw = mixed_w("大写", 11, wc=650)
    w = 8 + 9 + 4 + lw + 9
    x1 = BAT_LEFT - 6
    return x1 - w, x1, lw
def draw_pill(c, lang):
    x0, x1, lw = pill_geom(lang)
    c.paint(c.rrect(x0, PILL[0], x1, PILL[1], 8), YELLOW)
    ic_caps(c, x0 + 8 + 4.5, (PILL[0] + PILL[1]) / 2 + 0.2, 0.74, BLACK)
    if lang == "en":
        tracked(c, x0 + 8 + 9 + 4, 19.6, "CAPS", inter(10, 760), BLACK, 0.7)
    else:
        mixed(c, x0 + 8 + 9 + 4, 20, "大写", 11, BLACK, wc=650)

# ---------------- time ----------------
DIG = "0123456789"
def fit_time(maxw=240 - 2 * M, maxcap=60, wght=720, track=-0.02):
    for size in range(140, 30, -1):
        f = inter(size, wght); amax = max(f.getlength(d) for d in DIG)
        x0, y0, x1, y1 = ink("0", f); cap = y1 - y0
        dot = size * (0.072 + (wght - 300) / 400 * 0.058); colon_w = dot + 2 * size * 0.062
        worst = 4 * amax + colon_w + 4 * track * size
        if cap <= maxcap and worst <= maxw:
            return dict(size=size, f=f, cap=cap, y0=y0, y1=y1, dot=dot, colon_w=colon_w, trk=track * size, worst=worst)
TM = fit_time()
TIME_BASE = round(TIME_MID - (TM["y0"] + TM["y1"]) / 2)
def time_width(h, m):
    f = TM["f"]; s = f"{h:02d}{m:02d}"
    return sum(f.getlength(d) for d in s) + TM["colon_w"] + 4 * TM["trk"]
def draw_time(c, h, m):
    f = TM["f"]; x = (240 - time_width(h, m)) / 2; s = f"{h:02d}:{m:02d}"
    mid = TIME_BASE + (TM["y0"] + TM["y1"]) / 2; g = TM["cap"] * 0.215; d = TM["dot"]
    for ch in s:
        if ch == ":":
            cx = x + TM["colon_w"] / 2
            for cy in (mid - g, mid + g):
                c.paint(c.rrect(cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2, d * 0.32), ORANGE)
            x += TM["colon_w"] + TM["trk"]
        else:
            c.paint(c.text(round(x), TIME_BASE, ch, f), WHITE); x += f.getlength(ch) + TM["trk"]

# ---------------- bottom row ----------------
def draw_bottom(c, st):
    lang, mode = st["lang"], st["mode"]
    fn, iw = ICON[mode]; fn(c, round(M + iw / 2 - 0.5) + 0.5, BOT_CY, 1.0, SEC)
    lab = {"usb": "USB", "24g": "2.4G", "bt": (f"BT {st['ch']}" if lang == "en" else f"蓝牙 {st['ch']}")}[mode]
    x = mixed(c, M + iw + 6, BOT_BASE, lab, 12, SEC)
    for on, kind in ((st["num"], "num"), (st["win"], "win")):
        if not on:
            continue
        c.paint(c.circle(x + 6.5, BOT_CY, 1.25), TER); x += 13
        if kind == "win":
            ic_lock(c, x + 3.6, BOT_CY - 1, 0.9, SEC); x += 11
            x = mixed(c, x, BOT_BASE, "WIN" if lang == "en" else "Win", 12, SEC, wl=650)
        else:
            x = mixed(c, x, BOT_BASE, "NUM" if lang == "en" else "数字", 12, SEC, wl=650)
    os_glyph(c, st["os"], 240 - M - OS_W[st["os"]] / 2, BOT_CY, SEC)
    return x

def screen(st):
    c = Canvas()
    draw_date(c, st["lang"], st["date"])
    if st["caps"]:
        draw_pill(c, st["lang"])
    draw_battery(c, st["pct"], st["charging"])
    draw_time(c, st["h"], st["m"])
    draw_bottom(c, st)
    return quant(c.a)

TODAY = datetime.date(2026, 11, 7)
def st(lang="en", h=21, m=47, pct=86, charging=False, mode="usb", ch=1, caps=False, num=True, win=False, os_="win", date=TODAY):
    return dict(lang=lang, date=date, h=h, m=m, pct=pct, charging=charging, mode=mode, ch=ch, caps=caps, num=num, win=win, os=os_)
HERO_EN, HERO_CN = screen(st()), screen(st("cn"))
STATES = [("Caps Lock on", "2.4G · 57%", st(h=9, m=41, pct=57, mode="24g", caps=True)),
          ("Bluetooth 2", "Mac · Num Lock off · 72%", st(h=23, m=5, pct=72, mode="bt", ch=2, num=False, os_="mac")),
          ("Gaming", "Win key locked · full", st(h=20, m=16, pct=100, win=True)),
          ("Low battery", "Bluetooth 1 · 18%", st(h=18, m=52, pct=18, mode="bt", ch=1)),
          ("Charging", "USB · 64%", st(h=14, m=30, pct=64, charging=True)),
          ("iOS", "Bluetooth 3 · 41%", st(h=7, m=8, pct=41, mode="bt", ch=3, os_="ios")),
          ("Android", "2.4G · 6% · midnight", st(h=0, m=0, pct=6, mode="24g", os_="android", date=datetime.date(2026, 12, 30))),
          ("中文 · 大写锁定", "2.4G · 57%", st("cn", h=9, m=41, pct=57, mode="24g", caps=True)),
          ("中文 · 低电量", "蓝牙 2 · 18%", st("cn", h=18, m=52, pct=18, mode="bt", ch=2, num=False, win=True))]
STATE_IMGS = [(n, d, screen(s)) for n, d, s in STATES]
