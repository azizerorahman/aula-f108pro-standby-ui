"""Supersampled shapes, category glyphs and square menu tiles."""
import sys, os, io, re, base64, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
FD = str(Path(__file__).resolve().parents[2] / "assets/fonts")
SHAPE = "square"
S = 8
INTER = os.path.join(FD, "Inter-VF.ttf")
def snap(c):
    r5, g6, b5 = round(c[0] * 31 / 255), round(c[1] * 63 / 255), round(c[2] * 31 / 255)
    return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))
BAYER8 = (np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                    [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) + 0.5) / 64.0
def quant(a):
    a = np.clip(a, 0, 255); h, w = a.shape[:2]; th = np.tile(BAYER8, (h // 8 + 1, w // 8 + 1))[:h, :w]; out = []
    for ch, n in ((0, 31), (1, 63), (2, 31)):
        lv = a[..., ch] * n / 255; q = np.rint(lv)
        q = np.where(np.abs(lv - q) < 0.06, q, np.floor(lv + th)); q = np.clip(q, 0, n).astype(np.uint16)
        out.append((q << 3) | (q >> 2) if n == 31 else (q << 2) | (q >> 4))
    return Image.fromarray(np.stack(out, -1).astype(np.uint8), "RGB")

WHITE, BLACK = (255, 255, 255), (0, 0, 0)
TER = snap((100, 100, 100))
CAT = {"connect": (10, 132, 255), "system": (142, 142, 147), "effect": (191, 90, 242), "colour": (255, 55, 95),
       "brightness": (255, 159, 10), "speed": (48, 209, 88), "volume": (255, 69, 58), "language": (94, 92, 230)}
PAGES = [("connect", "system"), ("effect", "colour"), ("brightness", "speed"), ("volume", "language")]
NAMES = {"connect": "Connect", "system": "System", "effect": "Effect", "colour": "Colour", "brightness": "Brightness",
         "speed": "Speed", "volume": "Volume", "language": "Language"}
SLOTS = [(76, 60), (164, 60)]
R_SEL, R_REST = 29, 25
DOTS_Y = 121

class Canvas:
    def __init__(s, w=240, h=135):
        s.w, s.h = w, h; s.a = np.zeros((h, w, 3), np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); s.yy, s.xx = yy + 0.5, xx + 0.5
    def _hi(s):
        m = Image.new("L", (s.w * S, s.h * S), 0); return m, ImageDraw.Draw(m)
    def _lo(s, m): return np.asarray(m.reduce(S), np.float32) / 255.0
    def paint(s, k, col, alpha=1.0):
        k = (k * alpha)[..., None] if np.ndim(k) == 2 else k * alpha
        s.a = s.a * (1 - k) + np.asarray(col, np.float32) * k
    def paint_field(s, k, field):                       # per-pixel colour (h, w, 3)
        k = k[..., None]; s.a = s.a * (1 - k) + field * k
    def rrect(s, x0, y0, x1, y1, r):
        m, d = s._hi(); d.rounded_rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], radius=max(0, r) * S, fill=255); return s._lo(m)
    def circle(s, cx, cy, r):
        m, d = s._hi(); d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S - 1, (cy + r) * S - 1], fill=255); return s._lo(m)
    def ellipse(s, cx, cy, rx, ry):
        m, d = s._hi(); d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S - 1, (cy + ry) * S - 1], fill=255); return s._lo(m)
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
        bx0 = max(0, int(np.floor(P[:, 0].min() / S)) - 1); bx1 = min(s.w, int(np.ceil(P[:, 0].max() / S)) + 1)
        by0 = max(0, int(np.floor(P[:, 1].min() / S)) - 1); by1 = min(s.h, int(np.ceil(P[:, 1].max() / S)) + 1)
        ys, xs = np.mgrid[by0 * S:by1 * S, bx0 * S:bx1 * S] + 0.5
        inside = np.zeros(xs.shape, bool)
        for i in range(n):
            (x1, y1), (x2, y2) = P[i], P[(i + 1) % n]
            if y1 == y2:
                continue
            cond = ((y1 <= ys) & (ys < y2)) | ((y2 <= ys) & (ys < y1))
            inside ^= cond & (xs < x1 + (ys - y1) * (x2 - x1) / (y2 - y1))
        out = np.zeros((s.h, s.w), np.float32)
        out[by0:by1, bx0:bx1] = inside.reshape(by1 - by0, S, bx1 - bx0, S).mean(axis=(1, 3))
        return out
    def ring(s, cx, cy, r0, r1): return np.clip(s.circle(cx, cy, r1) - s.circle(cx, cy, r0), 0, 1)
    def squircle(s, cx, cy, a, n=5.0):
        """Superellipse |x|^n + |y|^n <= a^n: the smooth 'continuous' corner used for phone app icons."""
        bx0 = max(0, int(cx - a) - 1); bx1 = min(s.w, int(cx + a) + 2); by0 = max(0, int(cy - a) - 1); by1 = min(s.h, int(cy + a) + 2)
        ys, xs = np.mgrid[by0 * S:by1 * S, bx0 * S:bx1 * S].astype(np.float32) + 0.5
        u = np.abs(xs / S - cx) / a; v = np.abs(ys / S - cy) / a
        out = np.zeros((s.h, s.w), np.float32)
        out[by0:by1, bx0:bx1] = ((u ** n + v ** n) <= 1.0).reshape(by1 - by0, S, bx1 - bx0, S).mean(axis=(1, 3))
        return out
    def sq_ring(s, cx, cy, a0, a1): return np.clip(s.squircle(cx, cy, a1) - s.squircle(cx, cy, a0), 0, 1)
    def sq_norm(s, cx, cy, n=5.0):
        return (np.abs(s.xx - cx) ** n + np.abs(s.yy - cy) ** n) ** (1.0 / n)

# ---------------- bold, filled glyphs (k = 1 for a ~26 px glyph) ----------------
def gl_connect(c, cx, cy, k, col, bg):
    c.paint(c.circle(cx, cy + 6 * k, 3.4 * k), col)
    for r in (8.0 * k, 13.8 * k):
        c.paint(c.arc(cx, cy + 6 * k, r, 3.0 * k, 222, 318), col)
def gl_system(c, cx, cy, k, col, bg):
    pts = []
    for i in range(360):
        a = 2 * math.pi * i / 360; deg = (math.degrees(a) + 22.5) % 45
        r = (13.0 if abs(deg - 22.5) < 10 else 9.8) * k
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    c.paint(c.poly(pts), col); c.paint(c.circle(cx, cy, 4.6 * k), bg)
def gl_effect(c, cx, cy, k, col, bg):
    def star(x, y, R, r):
        return [(x + (R if j % 2 == 0 else r) * math.cos(math.pi / 4 * j - math.pi / 2), y + (R if j % 2 == 0 else r) * math.sin(math.pi / 4 * j - math.pi / 2)) for j in range(8)]
    c.paint(c.poly(star(cx - 2.5 * k, cy + 2.5 * k, 12.5 * k, 3.2 * k)), col)
    c.paint(c.poly(star(cx + 8.5 * k, cy - 8.5 * k, 5.4 * k, 1.5 * k)), col)
    c.paint(c.poly(star(cx + 9.5 * k, cy + 7.5 * k, 3.4 * k, 1.0 * k)), col)
def gl_colour(c, cx, cy, k, col, bg):
    c.paint(c.circle(cx, cy, 12.5 * k), col)
    c.paint(c.circle(cx + 5.6 * k, cy + 5.4 * k, 3.8 * k), bg)                      # thumb hole
    for (dx, dy), dc in zip(((-5.5, -3.0), (-0.5, -7.2), (5.2, -3.6), (-5.0, 3.6)), ((255, 69, 58), (255, 214, 10), (48, 209, 88), (10, 132, 255))):
        c.paint(c.circle(cx + dx * k, cy + dy * k, 2.5 * k), dc)
def gl_brightness(c, cx, cy, k, col, bg):
    c.paint(c.circle(cx, cy, 6.2 * k), col)
    for i in range(8):
        a = math.pi / 4 * i
        c.paint(c.line([(cx + 9.6 * k * math.cos(a), cy + 9.6 * k * math.sin(a)), (cx + 12.8 * k * math.cos(a), cy + 12.8 * k * math.sin(a))], 2.7 * k), col)
def gl_speed(c, cx, cy, k, col, bg):
    y0 = cy + 4 * k
    c.paint(c.arc(cx, y0, 12.0 * k, 3.0 * k, 180, 360), col)
    t = math.radians(308); c.paint(c.line([(cx, y0), (cx + 9.5 * k * math.cos(t), y0 + 9.5 * k * math.sin(t))], 3.0 * k), col)
    c.paint(c.circle(cx, y0, 3.4 * k), col)
def gl_volume(c, cx, cy, k, col, bg):
    c.paint(c.poly([(cx - 11 * k, cy - 4.2 * k), (cx - 6.5 * k, cy - 4.2 * k), (cx - 0.5 * k, cy - 10 * k), (cx - 0.5 * k, cy + 10 * k), (cx - 6.5 * k, cy + 4.2 * k), (cx - 11 * k, cy + 4.2 * k)]), col)
    for r in (5.8 * k, 10.6 * k):
        c.paint(c.arc(cx - 0.5 * k, cy, r, 2.6 * k, -50, 50), col)
def gl_language(c, cx, cy, k, col, bg):
    c.paint(c.ring(cx, cy, 10.6 * k, 13.0 * k), col)
    c.paint(np.clip(c.ellipse(cx, cy, 6.2 * k, 13.0 * k) - c.ellipse(cx, cy, 4.0 * k, 10.8 * k), 0, 1), col)
    for dy, half in ((0, 12.0), (-6.2, 9.8), (6.2, 9.8)):
        c.paint(c.rrect(cx - half * k, cy + dy * k - 1.1 * k, cx + half * k, cy + dy * k + 1.1 * k, 1.1 * k), col)
GLYPH = {"connect": gl_connect, "system": gl_system, "effect": gl_effect, "colour": gl_colour, "brightness": gl_brightness,
         "speed": gl_speed, "volume": gl_volume, "language": gl_language}

def mix(a, b, t): return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))
def icon(c, key, cx, cy, r, state):
    """state: 'rest' (dimmed), 'flat' (full colour), 'sel' (full colour, ring + glow)"""
    base = CAT[key]; sq = SHAPE == "square"; rr = r * 0.92 if sq else r     # equal optical weight
    if state == "sel":                                   # soft halo in the item's colour, then a white focus ring
        d = c.sq_norm(cx, cy) if sq else np.hypot(c.xx - cx, c.yy - cy)
        halo = np.clip(np.exp(-((d - (rr + 4)) / 6.5) ** 2) * (d > rr) * 0.55, 0, 1)
        c.paint(halo, base)
        c.paint(c.sq_ring(cx, cy, rr + 3.0, rr + 5.2) if sq else c.ring(cx, cy, r + 3.0, r + 5.2), WHITE, 0.92)
    dim = 0.40 if state == "rest" else 1.0
    top, bot = mix(base, WHITE, 0.22), mix(base, BLACK, 0.18)
    t = np.clip((c.yy - (cy - r)) / (2 * r), 0, 1)[..., None]
    field = (np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t) * dim
    disc = c.squircle(cx, cy, rr) if sq else c.circle(cx, cy, r); c.paint_field(disc, field)
    bg = tuple(float(v) for v in field[int(cy), int(cx)])
    glyph_col = WHITE if state != "rest" else (165, 165, 165)
    GLYPH[key](c, cx, cy, r / 25.0, glyph_col, bg)

def page_screen(page, sel, variant="ring"):
    c = Canvas()
    for i, key in enumerate(PAGES[page]):
        cx, cy = SLOTS[i]
        if variant == "ring":
            icon(c, key, cx, cy, R_SEL if i == sel else R_REST, "sel" if i == sel else "rest")
        elif variant == "overlay":
            icon(c, key, cx, cy, R_SEL, "flat" if i == sel else "rest")
        else:  # ring only
            if i == sel:
                a = R_SEL * 0.92
                c.paint(c.sq_ring(cx, cy, a + 3.0, a + 5.2) if SHAPE == "square" else c.ring(cx, cy, R_SEL + 3.0, R_SEL + 5.2), WHITE, 0.92)
            icon(c, key, cx, cy, R_SEL, "flat")
    for k in range(4):
        c.paint(c.circle(105 + 10 * k, DOTS_Y, 2.2), WHITE if k == page else TER)
    return quant(c.a)

# brightness without a title (title tile drawn black)
SEG_X0, SEG_W, SEG_GAP, SEG_Y0, SEG_H = 30, 33, 4, 98, 8
def inter_f(px, w):
    f = ImageFont.truetype(INTER, px, layout_engine=ImageFont.Layout.BASIC); f.set_variation_by_axes([min(32, max(14, px)), w]); return f
FBIG = inter_f(62, 720)
def brightness(level):
    c = Canvas(); s = str(level)
    m = Image.new("L", (240, 135), 0); d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = d.textbbox((0, 82), s, font=FBIG, anchor="ls")
    d.text((round(120 - (x0 + x1) / 2), 82), s, font=FBIG, fill=255, anchor="ls"); c.paint(np.asarray(m, np.float32) / 255, WHITE)
    for i in range(5):
        x = SEG_X0 + i * (SEG_W + SEG_GAP); c.paint(c.rrect(x, SEG_Y0, x + SEG_W, SEG_Y0 + SEG_H, 4), CAT["brightness"] if i < level else (58, 58, 60))
    gl_brightness(c, 16.5, SEG_Y0 + SEG_H / 2, 0.5, TER, BLACK); gl_brightness(c, 224, SEG_Y0 + SEG_H / 2, 0.72, (150, 150, 150), BLACK)
    return quant(c.a)

