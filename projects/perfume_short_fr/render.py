"""Frame-accurate compositor for the perfume short.

python3 render.py SRC.mp4 OUT_video.mp4 [--start N --count K] [--stills t1,t2,...]
"""
import json, math, os, subprocess, sys
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from edit_spec import *

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 24
SW, SH = 720, 1280
ANTON = os.path.join(HERE, "fonts/Anton-Regular.ttf")
MONT = os.path.join(HERE, "fonts/Montserrat.ttf")
N_FRAMES = int((T_END - T0) * FPS)


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out_back(x, s=1.9):
    x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


@lru_cache(None)
def anton(sz): return ImageFont.truetype(ANTON, sz)


@lru_cache(None)
def mont(sz, wt=800):
    f = ImageFont.truetype(MONT, sz)
    try: f.set_variation_by_axes([wt])
    except Exception: pass
    return f


# ---------------------------------------------------------------- compositing
def blend(dst, spr, x, y, alpha=1.0):
    """alpha-composite RGBA uint8 sprite onto float32 RGB dst at top-left (x,y)."""
    if spr is None or alpha <= 0.003: return
    h, w = spr.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    a = s[..., 3:4] * (alpha / 255.0)
    d = dst[y0:y1, x0:x1]
    d *= (1 - a); d += s[..., :3] * a


def blend_c(dst, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if spr is None: return
    if abs(scale - 1) > 1e-3 or abs(rot) > 1e-3:
        h, w = spr.shape[:2]
        if abs(rot) > 1e-3:
            M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
            c, s = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * s + w * c) + 2, int(h * c + w * s) + 2
            M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
            spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        else:
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            spr = cv2.resize(spr, (nw, nh), interpolation=cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    blend(dst, spr, cx - w / 2, cy - h / 2, alpha)


def pil2np(im): return np.array(im.convert("RGBA"))


# ---------------------------------------------------------------- sprites
@lru_cache(None)
def word_sprite(word, style, color=YELLOW):
    """style: normal | active | emph"""
    f = anton(116)
    pad = 30
    l, t, r, b = f.getbbox(word, stroke_width=10)
    w, h = r - l + pad * 2, b - t + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if style == "emph":
        d = ImageDraw.Draw(im)
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(bx)
        bd.rounded_rectangle((8, 14, w - 8, h - 10), 22, fill=hexrgb(color) + (255,))
        sh = bx.filter(ImageFilter.GaussianBlur(10)); sh = Image.eval(sh, lambda v: v)
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); shadow.putalpha(sh.split()[3].point(lambda v: v * 0.55))
        im = Image.alpha_composite(im, shadow); im = Image.alpha_composite(im, bx)
        d = ImageDraw.Draw(im)
        dark = sum(hexrgb(color)) > 520
        d.text((pad - l, pad - t), word, font=f, fill=(15, 15, 20) if dark else (255, 255, 255))
    else:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l, pad - t + 6), word, font=f, fill=(0, 0, 0, 170), stroke_width=12, stroke_fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(7))
        im = Image.alpha_composite(im, sh)
        d = ImageDraw.Draw(im)
        fill = hexrgb(YELLOW) if style == "active" else (255, 255, 255)
        d.text((pad - l, pad - t), word, font=f, fill=fill, stroke_width=10, stroke_fill=(10, 10, 14))
    return pil2np(im)


@lru_cache(None)
def headline_sprite(text, color, size):
    f = anton(size)
    l, t, r, b = f.getbbox(text)
    pad = 60
    w, h = r - l + pad * 2, b - t + pad * 2
    # vertical gradient fill: light tint -> colour
    c = np.array(hexrgb(color), np.float32)
    top = c + (255 - c) * 0.55
    g = np.linspace(0, 1, h)[:, None, None]
    grad = (top * (1 - g) + c * g).astype(np.uint8)
    grad = np.repeat(grad, w, axis=1)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).text((pad - l, pad - t), text, font=f, fill=255)
    fill = Image.fromarray(np.dstack([grad, np.array(mask)]), "RGBA")
    # shadow cast on wall
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.45))
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, -10, 0, 1, -16))
    # thin dark edge for crispness
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(edge).text((pad - l, pad - t), text, font=f, fill=(0, 0, 0, 0), stroke_width=4, stroke_fill=(25, 15, 10, 200))
    out = Image.alpha_composite(Image.alpha_composite(sh, edge), fill)
    return pil2np(out)


def star_poly(cx, cy, r, inner=0.28):
    pts = []
    for k in range(8):
        ang = k * math.pi / 4 - math.pi / 2
        rr = r if k % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


@lru_cache(None)
def chip_sprite(text, color):
    f = mont(44, 800)
    l, t, r, b = f.getbbox(text)
    tw, th = r - l, b - t
    w, h = tw + 130, 92
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, 20 + w, 26 + h), 46, fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 46, fill=(255, 255, 255, 245))
    d.ellipse((30, 30, 30 + 72, 30 + 72), fill=hexrgb(color) + (255,))
    d.polygon(star_poly(66, 66, 24), fill=(255, 255, 255, 255))
    d.text((20 + 104 - l, 20 + (h - th) / 2 - t), text, font=f, fill=(18, 18, 24))
    return pil2np(im)


@lru_cache(None)
def card_sprite(num, name, sub, color):
    fn, fnum, fs = anton(92), anton(84), mont(36, 700)
    nl, nt, nr, nb = fn.getbbox(name); sl, st, sr, sb = fs.getbbox(sub)
    w = max(nr - nl, sr - sl) + 200 + 70
    h = 196
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 28, 20 + w, 28 + h), 34, fill=(0, 0, 0, 140))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 34, fill=(14, 12, 20, 225))
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), 34, outline=hexrgb(color) + (255,), width=4)
    d.rounded_rectangle((38, 38, 38 + 160, 38 + 160), 26, fill=hexrgb(color) + (255,))
    l, t, r, b = fnum.getbbox(num)
    dark = sum(hexrgb(color)) > 520
    d.text((38 + 80 - (r - l) / 2 - l, 38 + 80 - (b - t) / 2 - t), num, font=fnum, fill=(15, 15, 20) if dark else (255, 255, 255))
    d.text((230 - nl, 44 - nt), name, font=fn, fill=(255, 255, 255))
    d.text((232 - sl, 158 - st), sub, font=fs, fill=hexrgb(color))
    return pil2np(im)


@lru_cache(None)
def hook_sprite(text, color, size):
    f = anton(size)
    l, t, r, b = f.getbbox(text, stroke_width=12)
    pad = 40
    w, h = r - l + 2 * pad, b - t + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad - l, pad - t + 10), text, font=f, fill=(0, 0, 0, 200), stroke_width=14, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=hexrgb(color), stroke_width=12, stroke_fill=(12, 10, 16))
    return pil2np(im)


@lru_cache(None)
def pill_sprite(text, bg, fg, size=46):
    f = mont(size, 800)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 90, int(size * 2.0)
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((15, 21, 15 + w, 21 + h), h // 2, fill=(0, 0, 0, 130))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + w, 15 + h), h // 2, fill=hexrgb(bg) + (255,))
    d.text((15 + 45 - l, 15 + (h - (b - t)) / 2 - t), text, font=f, fill=hexrgb(fg))
    return pil2np(im)


# ---------------------------------------------------------------- timeline helpers
def env(t, a, b, fin=0.3, fout=0.25):
    if t < a or t > b: return 0.0
    return min(clamp((t - a) / fin), clamp((b - t) / fout))


def headline_at(t):
    for h in HEADLINES:
        if h[0] - 0.5 <= t <= h[1] + 0.5: return h
    return None


def shift_amount(t):
    """how far (px) the subject is pushed down: headline moments, hook, end card."""
    D = 250.0
    wins = [(h[0], h[1]) for h in HEADLINES] + [(HOOK[0] - 1, HOOK[1]), (END_CARD_START, T_END + 1)]
    v = 0.0
    for a, b in wins:
        if a - 0.45 <= t <= b + 0.45:
            v = max(v, min(ease_in_out((t - (a - 0.45)) / 0.45), ease_in_out(((b + 0.45) - t) / 0.45)))
    return D * v


EMPH_TIMES = []
for txt, ts in CAPTIONS:
    for w, tt in zip(txt.split(), ts):
        if w.startswith("*"): EMPH_TIMES.append(tt)
CUT_TIMES = [p[0] for p in PRODUCTS]


def zoom_amount(t):
    z = 1.0
    # slow breathing push-in per section
    secs = [T0, 9.9, 21.8, 40.0, 64.0, 85.7, T_END]
    for a, b in zip(secs, secs[1:]):
        if a <= t < b: z += 0.05 * (t - a) / (b - a)
    for e in EMPH_TIMES:
        if 0 <= t - e < 0.45: z += 0.035 * (1 - ease_out_cubic((t - e) / 0.45)) * ease_out_cubic((t - e) / 0.06)
    for c in CUT_TIMES:
        if 0 <= t - c < 0.6: z += 0.10 * (1 - ease_out_cubic((t - c) / 0.6))
    return z


def product_at(t):
    for p in PRODUCTS:
        if p[0] <= t < p[1]: return p
    return None


def track_box(track, t):
    pts = track[1]
    if t < pts[0][0] - 0.3 or t > pts[-1][0] + 0.35: return None, 0
    a = clamp((t - (pts[0][0] - 0.3)) / 0.3) * clamp((pts[-1][0] + 0.35 - t) / 0.35)
    if t <= pts[0][0]: return pts[0][1], a
    if t >= pts[-1][0]: return pts[-1][1], a
    for (t1, b1), (t2, b2) in zip(pts, pts[1:]):
        if t1 <= t <= t2:
            u = ease_in_out((t - t1) / (t2 - t1))
            return tuple(x1 + (x2 - x1) * u for x1, x2 in zip(b1, b2)), a


# ---------------------------------------------------------------- grading
def make_lut():
    x = np.arange(256) / 255.0
    s = x + 0.10 * np.sin(2 * math.pi * (x - 0.5)) * -0.0  # placeholder
    s = 1 / (1 + np.exp(-(x - 0.5) * 6.0)); s = (s - s.min()) / (s.max() - s.min())
    y = 0.55 * x + 0.45 * s           # gentle S-curve
    y = np.clip((y - 0.035) / 0.95, 0, 1) ** 1.04
    return (y * 255).astype(np.uint8)


LUT = make_lut()
_vy, _vx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = (1 - 0.32 * np.clip(((_vx - W / 2) / (W * 0.72)) ** 2 + ((_vy - H * 0.45) / (H * 0.62)) ** 2, 0, 1) ** 1.3)[..., None].astype(np.float32)
del _vx, _vy


def grade(fr):
    fr = cv2.LUT(fr, LUT).astype(np.float32)
    g = fr.mean(axis=2, keepdims=True)
    fr = g + (fr - g) * 1.15
    fr[..., 0] *= 1.03; fr[..., 2] *= 0.97     # a touch warmer
    return np.clip(fr, 0, 255)


# ---------------------------------------------------------------- masks
MASK_DIR = os.path.join(HERE, "masks")


@lru_cache(maxsize=16)
def raw_mask(i):
    p = os.path.join(MASK_DIR, f"{i:05d}.png")
    if not os.path.exists(p): return None
    return cv2.imread(p, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0


def get_mask(i):
    ms = []
    for j, wgt in ((i - 2, 1), (i - 1, 2), (i, 3), (i + 1, 2), (i + 2, 1)):
        m = raw_mask(j)
        if m is not None: ms.append((m, wgt))
    if not ms: return np.ones((640, 360), np.float32)
    m = sum(a * w for a, w in ms) / sum(w for _, w in ms)
    m = np.clip((m - 0.25) / 0.5, 0, 1)
    return cv2.resize(m, (SW, SH), interpolation=cv2.INTER_LINEAR)


# ---------------------------------------------------------------- main frame
def affine(t):
    S = 1.5 * zoom_amount(t)
    D = shift_amount(t)
    ax, ay = 360.0, 520.0
    M = np.array([[S, 0, 540 - ax * S], [0, S, 780 + D - ay * S]], np.float32)
    return M, S, D


def src_to_canvas(M, x, y):
    return M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]


def caption_layout(t):
    """returns list of (word, style, color, cx, cy, scale) for the active group."""
    idx = None
    for k, (txt, ts) in enumerate(CAPTIONS):
        nxt = CAPTIONS[k + 1][1][0] if k + 1 < len(CAPTIONS) else 1e9
        end = min(nxt, ts[-1] + 1.1)
        if ts[0] - 0.04 <= t < end: idx = k; break
    if idx is None: return []
    txt, ts = CAPTIONS[idx]
    words = txt.split()
    prod = product_at(t)
    ecol = prod[5] if prod else PINK
    items = []
    for w, tt in zip(words, ts):
        emph = w.startswith("*"); w = w.lstrip("*")
        style = "emph" if emph else "normal"
        if not emph:
            # currently-spoken word glows yellow
            k = words.index("*" + w) if ("*" + w) in words else None
            nxt_t = [x for x in ts if x > tt]
            if tt <= t < (nxt_t[0] if nxt_t else tt + 0.6): style = "active"
        spr = word_sprite(w, style, ecol if emph else YELLOW)
        items.append((w, style, ecol, spr, tt))
    # layout into lines (max width 960)
    gap = -26
    lines, cur, cw = [], [], 0
    for it in items:
        ww = it[3].shape[1]
        if cur and cw + gap + ww > 1000: lines.append(cur); cur, cw = [], 0
        cur.append(it); cw += ww + (gap if len(cur) > 1 else 0)
    if cur: lines.append(cur)
    out = []
    lh = 132
    y0 = 1250 - (len(lines) - 1) * lh / 2
    for li, ln in enumerate(lines):
        tw = sum(i[3].shape[1] for i in ln) + gap * (len(ln) - 1)
        x = 540 - tw / 2
        for it in ln:
            ww = it[3].shape[1]
            age = t - it[4]
            if age < -0.02: x += ww + gap; continue
            sc = 0.55 + 0.45 * ease_out_back(age / 0.16, 2.2)
            if it[1] == "emph": sc = 0.4 + 0.6 * ease_out_back(age / 0.2, 2.6)
            rot = -3.0 if it[1] == "emph" else 0.0
            out.append((it[3], x + ww / 2, y0 + li * lh, sc, clamp(age / 0.06 + 0.3), rot))
            x += ww + gap
    return out


def draw_brackets(ov, box, color, a, t, t_start):
    if box is None or a <= 0: return
    x0, y0, x1, y1 = box
    grow = 1 + 0.25 * (1 - ease_out_cubic((t - t_start) / 0.4))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hw, hh = (x1 - x0) / 2 * grow + 18, (y1 - y0) / 2 * grow + 18
    x0, x1, y0, y1 = cx - hw, cx + hw, cy - hh, cy + hh
    x0, y0 = max(x0, 26), max(y0, 26); x1, y1 = min(x1, W - 26), min(y1, H - 26)
    L = int(min(90, (x1 - x0) * 0.25, (y1 - y0) * 0.25))
    col = hexrgb(color)[::-1]  # cv2 on RGB float: we pass RGB
    col = hexrgb(color)
    pts = [((x0, y0), (x0 + L, y0), (x0, y0 + L)), ((x1, y0), (x1 - L, y0), (x1, y0 + L)),
           ((x0, y1), (x0 + L, y1), (x0, y1 - L)), ((x1, y1), (x1 - L, y1), (x1, y1 - L))]
    lay = np.zeros((H, W, 3), np.float32)
    for c, p1, p2 in pts:
        c = tuple(int(v) for v in c)
        cv2.line(lay, c, tuple(int(v) for v in p1), col, 10, cv2.LINE_AA)
        cv2.line(lay, c, tuple(int(v) for v in p2), col, 10, cv2.LINE_AA)
    # sparkles
    rng = np.random.default_rng(int(x0 * 7 + 3))
    for k in range(7):
        ph = rng.random() * 6.28; sp = 2 + rng.random() * 3
        px = x0 + rng.random() * (x1 - x0); py = y0 + rng.random() * (y1 - y0) * 0.6
        tw = max(0.0, math.sin(t * sp + ph)) ** 3
        if tw > 0.05:
            r = 10 + 22 * tw
            cv2.fillPoly(lay, [np.array(star_poly(px, py, r), np.int32)], (255, 255, 255), cv2.LINE_AA)
    glow = cv2.GaussianBlur(lay, (0, 0), 14)
    ov += (lay * 0.9 + glow * 1.6) * a


def render_frame(n, fr, mask_idx):
    t = T0 + n / FPS
    M, S, D = affine(t)
    g = grade(fr)
    base = cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = cv2.warpAffine(get_mask(mask_idx), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    m3 = m[..., None]
    out = base.copy()

    # ---------- behind-subject headline
    h = headline_at(t)
    if h:
        a0, a1, lines, col = h
        ein = ease_out_cubic((t - a0) / 0.45); eout = clamp((a1 - t) / 0.3)
        alpha = clamp((t - a0) / 0.18) * eout
        if alpha > 0:
            layer = out.copy()
            n_l = len(lines)
            size = 300 if n_l == 1 else 250
            head_top = src_to_canvas(M, 0, 282)[1]
            ytot = n_l * size * 0.98
            ybase = head_top + 70 - ytot
            for li, txt in enumerate(lines):
                spr = headline_sprite(txt, col, size)
                maxw = W - 30
                sc = min(1.0, maxw / spr.shape[1]) * (1.18 - 0.18 * ein)
                cy = ybase + li * size * 0.98 + size / 2 + (1 - ein) * 60
                blend_c(layer, spr, 540, cy, sc, 1.0)
            out = out * (1 - alpha) + layer * alpha
            out = out * m3 + (out * (1 - m3))  # (keep)
            out = base * m3 + out * (1 - m3)   # subject in front of headline

    ov = np.zeros((H, W, 3), np.float32)   # additive glow layer

    # ---------- bottle highlight brackets
    for col, pts in BOTTLE_TRACKS:
        box, a = track_box((col, pts), t)
        if box is not None and a > 0:
            x0, y0 = src_to_canvas(M, box[0] * SW, box[1] * SH)
            x1, y1 = src_to_canvas(M, box[2] * SW, box[3] * SH)
            draw_brackets(ov, (x0, y0, x1, y1), col, a, t, pts[0][0] - 0.3)
    out = out + ov

    # ---------- hook
    if HOOK[0] <= t < HOOK[1] + 0.4:
        lt = t - HOOK[0]
        cols = [YELLOW, "#FFFFFF", "#FFFFFF"]
        sizes = [200, 132, 132]
        ys = [330, 520, 660]
        for k, (txt, c, sz, yy) in enumerate(zip(HOOK[2], cols, sizes, ys)):
            st = 0.05 + k * 0.22
            if lt < st: continue
            u = (lt - st)
            sc = 1.9 - 0.9 * ease_out_cubic(u / 0.22)
            out_a = clamp((HOOK[1] + 0.4 - t) / 0.3)
            dx = -900 * ease_in_out((t - HOOK[1]) / 0.4) * (1 if k % 2 == 0 else -1) if t > HOOK[1] else 0
            blend_c(out, hook_sprite(txt, c, sz), 540 + dx, yy, sc, clamp(u / 0.08) * out_a, -2.5 if k == 0 else 0)

    # ---------- product card + chips
    p = product_at(t)
    for pr in PRODUCTS:
        a0, a1, num, name, sub, col, chips = pr
        if not (a0 - 0.1 <= t <= a1 + 0.5): continue
        u_in = ease_out_back((t - a0 - 0.15) / 0.5, 1.4)
        u_out = ease_in_out((t - a1) / 0.4) if t > a1 else 0
        spr = card_sprite(num, name, sub, col)
        if t >= a0 + 0.15 and name != "BONUS":
            x = -spr.shape[1] + (spr.shape[1] + 40) * u_in - (spr.shape[1] + 80) * u_out
            blend(out, spr, x, 1420)
        shown = [c for c in chips if t >= c[0]]
        for k, (ct, ctext) in enumerate(shown):
            cs = chip_sprite(ctext, col)
            cw = cs.shape[1]
            ui = ease_out_back((t - ct) / 0.45, 1.6)
            # max two chips on screen: the oldest slides out when a third arrives
            gone = 0.0
            if len(shown) - k > 2:
                gone = ease_in_out((t - shown[k + 2][0]) / 0.35)
                if gone >= 1: continue
            slot = k - max(0, len(shown) - 2)
            if slot < 0:
                slot = 0
            else:
                prev = shown[-1][0] if len(shown) > 2 else None
                if prev is not None and slot == 0 and k > 0:
                    slot = 1 - ease_in_out((t - prev) / 0.35)  # slide up
            x = W + 10 - (cw + 30) * ui + (cw + 60) * max(u_out, gone)
            y = 905 + slot * 104
            blend(out, cs, x - 0, y)

    # ---------- captions
    if t < END_CARD_START:
        for spr, cx, cy, sc, a, rot in caption_layout(t):
            blend_c(out, spr, cx, cy, sc, a, rot)

    # ---------- end card
    if t >= END_CARD_START:
        lt = t - END_CARD_START
        q = hook_sprite("LEQUEL EST", "#FFFFFF", 130)
        q2 = hook_sprite("POUR TOI ?", YELLOW, 170)
        blend_c(out, q, 540, 340, 1.6 - 0.6 * ease_out_cubic(lt / 0.25), clamp(lt / 0.08))
        if lt > 0.2: blend_c(out, q2, 540, 520, 1.6 - 0.6 * ease_out_cubic((lt - 0.2) / 0.25), clamp((lt - 0.2) / 0.08), -2)
        for k, (num, col) in enumerate([("1", TEAL), ("2", ORANGE), ("3", GOLD)]):
            st = 0.6 + k * 0.15
            if lt > st:
                s = pill_sprite(num, col, "#111111" if col != ORANGE else "#FFFFFF", 64)
                blend_c(out, s, 360 + k * 180, 1250, ease_out_back((lt - st) / 0.35, 2.2), 1)
        if lt > 1.2:
            s = pill_sprite("Écris ton numéro en commentaire", "#FFFFFF", "#111111", 40)
            blend_c(out, s, 540, 1400, ease_out_back((lt - 1.2) / 0.35), 1)
        if lt > 1.6:
            s = pill_sprite("ABONNE-TOI POUR LA SUITE", PINK, "#FFFFFF", 44)
            pulse = 1 + 0.04 * math.sin((lt - 1.6) * 9)
            blend_c(out, s, 540, 1530, ease_out_back((lt - 1.6) / 0.35) * pulse, 1)

    # ---------- flash on product cuts
    for c in CUT_TIMES:
        if 0 <= t - c < 0.22:
            out = out + (255 - out) * (0.55 * (1 - (t - c) / 0.22))

    out = out * VIGNETTE

    # ---------- progress bar
    prog = clamp((t - T0) / (T_END - T0))
    pw = int(W * prog)
    if pw > 0:
        bar = np.linspace(0, 1, W, dtype=np.float32)[:pw, None]
        c1, c2 = np.array(hexrgb(TEAL), np.float32), np.array(hexrgb(PINK), np.float32)
        out[0:9, :pw] = (c1 * (1 - bar) + c2 * bar)[None]
    return np.clip(out, 0, 255).astype(np.uint8)


def frames(src, start=0):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    i = 0
    while True:
        b = p.stdout.read(SW * SH * 3)
        if len(b) < SW * SH * 3: break
        yield i, np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
        i += 1


def main():
    src, outp = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    stills = None; start, count = 0, N_FRAMES
    if "--stills" in args: stills = [float(x) for x in args[args.index("--stills") + 1].split(",")]
    if "--start" in args: start = int(args[args.index("--start") + 1])
    if "--count" in args: count = int(args[args.index("--count") + 1])
    if stills:
        want = {int(round(s * 24)): s for s in stills}
        for i, fr in frames(src):
            if i in want:
                n = int(round((want[i] - T0) * FPS))
                img = render_frame(n, fr, i)
                Image.fromarray(img).resize((540, 960)).save(f"{outp}_{want[i]:.2f}.jpg", quality=88)
            if i > max(want): break
        return
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
    first_src = int(round(T0 * 24))
    for i, fr in frames(src):
        n = i - first_src
        if n < start: continue
        if n >= min(N_FRAMES, start + count): break
        enc.stdin.write(render_frame(n, fr, i).tobytes())
        if n % 120 == 0: print("frame", n, flush=True)
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    main()
