"""
brand.py — burn brand logos into the top corners and a text hook over the
opening seconds. Driven by project.json:

    "hook_text": "PCOS/PMOS and you quit every reset by day 9? Same.",
    "logos": { "top_left": "brand/ojg.png", "top_right": "brand/pcos_care.png" }

The hook is a sound-off scroll-stopper — keep it short and, for paid social,
name the audience in it so the platform can target on it. Logo paths resolve
against the asset root (util.resolve_asset). Both are optional; with neither
set, `apply()` returns the input unchanged.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config, util

CW, CH = util.CANVAS
FPS = util.FPS
_CREAM = (244, 233, 220)
_LOGO_H = 108
_INSET_X, _INSET_Y = 44, 148
_PILL_PAD, _PILL_RAD = 20, 24
_HOOK_SECS = 3.2


def _font(px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for n in (("arialbd.ttf",) if bold else ("arial.ttf",)):
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            pass
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", px)
    except OSError:
        return ImageFont.load_default()


def _lockup(logo_path: Path, out: Path) -> None:
    logo = Image.open(logo_path).convert("RGBA")
    w = round(_LOGO_H * logo.width / logo.height)
    logo = logo.resize((w, _LOGO_H), Image.LANCZOS)
    pw, ph = w + 2 * _PILL_PAD, _LOGO_H + 2 * _PILL_PAD
    card = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=_PILL_RAD,
                                           fill=_CREAM + (150,))
    card.alpha_composite(logo, (_PILL_PAD, _PILL_PAD))
    card.save(out)


def _wrap(d, text: str, f, maxw: int) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def _hook_png(text: str, out: Path) -> None:
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    maxw = CW - 150
    px, lines = 72, [text]
    for px in (72, 66, 60, 54):
        lines = _wrap(d, text, _font(px), maxw)
        if len(lines) <= 3:
            break
    f = _font(px)
    lh = int(px * 1.24)
    top = 470 if len(lines) >= 3 else 520
    box_w = max(d.textlength(ln, font=f) for ln in lines) + 96
    d.rounded_rectangle([(CW - box_w) / 2, top - 34,
                         (CW + box_w) / 2, top + lh * len(lines) + 34 - (lh - px)],
                        radius=30, fill=(20, 24, 22, 150))
    y = top
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((CW - w) / 2, y), ln, font=f, fill=(255, 255, 255, 255),
               stroke_width=9, stroke_fill=(12, 20, 16, 255))
        y += lh
    img.save(out)


def apply(body: Path, project: "config.Project", *, work: Path) -> Path:
    """Overlay logos + hook onto a (video-only) body clip. Returns a new path,
    or `body` unchanged if the project declares neither."""
    hook = str(project.raw.get("hook_text", "")).strip()
    logos = project.raw.get("logos") or {}
    tl = logos.get("top_left")
    tr = logos.get("top_right")
    if not hook and not (tl and tr):
        return body

    inputs = ["-i", str(body)]
    fc_parts, idx = [], 1
    over = "[0:v]"
    if tl and tr:
        lk_tl, lk_tr = work / "lockup_tl.png", work / "lockup_tr.png"
        _lockup(util.resolve_asset(tl), lk_tl)
        _lockup(util.resolve_asset(tr), lk_tr)
        inputs += ["-i", str(lk_tl), "-i", str(lk_tr)]
        fc_parts += [f"[{idx}]format=rgba[tl]", f"[{idx+1}]format=rgba[tr]",
                     f"{over}[tl]overlay={_INSET_X}:{_INSET_Y}[a]",
                     f"[a][tr]overlay=W-w-{_INSET_X}:{_INSET_Y}[b]"]
        over, idx = "[b]", idx + 2
    if hook:
        hk = work / "hook.png"
        _hook_png(hook, hk)
        inputs += ["-loop", "1", "-t", f"{_HOOK_SECS + 0.4}", "-i", str(hk)]
        fc_parts += [f"[{idx}]format=rgba,fade=t=in:st=0.1:d=0.35:alpha=1,"
                     f"fade=t=out:st={_HOOK_SECS - 0.5:.2f}:d=0.5:alpha=1[hk]",
                     f"{over}[hk]overlay=0:0:eof_action=pass[v]"]
        over = "[v]"

    out = work / "body_branded.mp4"
    util.ffmpeg([*inputs, "-filter_complex", ";".join(fc_parts),
                 "-map", over, "-an", "-c:v", "libx264", "-preset", "medium",
                 "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    util.log(f"brand: logos={'yes' if tl and tr else 'no'} hook={'yes' if hook else 'no'}",
             level="ok")
    return out
