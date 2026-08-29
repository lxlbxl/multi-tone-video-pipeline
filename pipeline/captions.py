"""
(9) captions.py — kinetic captions.

Word groups (already chunked to `max_words_per_pop` by align.group_words or by
the shot list) become an ASS subtitle file styled from the tone profile's
`caption_style`: colour, outline colour/width, weight, case, screen position.
Motion intensity drives the pop-in: a fade for `low`, a scale-bounce for
`high`.

Burned in with libass (`-vf ass=…`), which every modern FFmpeg build ships.
"""
from __future__ import annotations

from pathlib import Path

from . import util
from .tone import Tone

CW, CH = util.CANVAS

_WEIGHT_BOLD = {"regular": 0, "medium": 0, "semibold": 1, "bold": 1,
                "extrabold": 1, "black": 1}
_POS_MARGINV = {"lower_third": 260, "center": 780, "upper_third": 1250}


def _ass_colour(hex_rgb: str, alpha: int = 0) -> str:
    r, g, b = util.hexrgb(hex_rgb)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def _fontsize(cs: dict) -> int:
    return {1: 118, 2: 104, 3: 92}.get(cs["max_words_per_pop"], 84)


def build_ass(groups: list[dict], tone: Tone, out_path: str | Path) -> Path:
    cs = tone.caption_style
    out_path = Path(out_path)
    fs = _fontsize(cs)
    bold = _WEIGHT_BOLD.get(cs["font_weight"], 1)
    primary = _ass_colour(cs["color"])
    outline = _ass_colour(cs["stroke"])
    back = _ass_colour("#000000", alpha=160)
    marginv = _POS_MARGINV.get(cs.get("position", "lower_third"), 260)
    stroke = float(cs.get("stroke_px", 6))
    font = cs.get("font_family", "Arial")
    pop_ms = tone.motion["pop_ms"]
    intensity = tone.motion_intensity

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CW}
PlayResY: {CH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,{font},{fs},{primary},{primary},{outline},{back},{bold},0,0,0,100,100,0.6,0,1,{stroke:.0f},2,2,90,90,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(sec: float) -> str:
        sec = max(0.0, sec)
        h = int(sec // 3600)
        mnt = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h:d}:{mnt:02d}:{s:05.2f}"

    def anim(text: str, emph: bool) -> str:
        if intensity == "low":
            return f"{{\\fad({pop_ms},{pop_ms})}}{text}"
        big = 128 if (emph or intensity == "high") else 114
        settle = pop_ms + 90
        tag = (f"{{\\fad({pop_ms//2},{max(60,pop_ms//2)})"
               f"\\fscx{big}\\fscy{big}\\t(0,{settle},\\fscx100\\fscy100)}}")
        return tag + text

    lines = []
    for g in groups:
        txt = g["text"].strip()
        if not txt:
            continue
        if tone.caption_style.get("uppercase"):
            txt = txt.upper()
        txt = txt.replace("\n", " ").replace("{", "(").replace("}", ")")
        start = ts(g["start"])
        end = ts(max(g["end"], g["start"] + 0.3))
        lines.append(f"Dialogue: 0,{start},{end},Pop,,0,0,0,,{anim(txt, g.get('emphasis', False))}")

    out_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    util.log(f"captions: {len(lines)} pops -> {out_path.name}")
    return out_path


def collect_groups(shot_list: dict) -> list[dict]:
    groups: list[dict] = []
    for s in shot_list["shots"]:
        for c in s.get("captions", []):
            groups.append({"text": c["text"], "start": c["start"], "end": c["end"],
                           "emphasis": c.get("emphasis", False)})
    groups.sort(key=lambda g: g["start"])
    # de-overlap so consecutive pops don't stack
    for i in range(1, len(groups)):
        if groups[i]["start"] < groups[i - 1]["end"]:
            groups[i - 1]["end"] = max(groups[i - 1]["start"] + 0.3,
                                       round(groups[i]["start"] - 0.03, 3))
    return groups


def burn(video_in: str | Path, ass_path: str | Path, video_out: str | Path) -> Path:
    video_out = Path(video_out)
    ass = Path(ass_path).resolve().as_posix()
    # escape for the ffmpeg filter arg (Windows drive colon, backslashes)
    ass_esc = ass.replace("\\", "/").replace(":", "\\:")
    util.ffmpeg(["-i", str(video_in), "-vf", f"ass='{ass_esc}'",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-c:a", "copy", str(video_out)])
    return video_out
