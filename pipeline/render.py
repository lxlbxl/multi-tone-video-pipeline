"""
(10) render.py — final assembly.

  concat animated shots  ->  body.mp4
  burn captions (one ASS over the whole body)
  mix VO (+ optional ducked music), loudnorm -14 LUFS
  mux audio onto the captioned body
  append a disclaimer end-card if the tone profile / project requires one
  write output/<name>_final.mp4 + a manifest
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import brand as brand_mod
from . import captions as cap_mod
from . import config, music, util
from .tone import Tone

CW, CH = util.CANVAS
FPS = util.FPS
_ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-r", str(FPS)]


def _concat(clips: list[Path], out: Path, work: Path) -> Path:
    listf = work / "body_concat.txt"
    listf.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in clips),
                     encoding="utf-8")
    # re-encode (not -c copy): the animated clips share a contract but a stray
    # keyframe/timebase mismatch still breaks stream-copy concat
    util.ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listf),
                 "-vf", f"scale={CW}:{CH},setsar=1,fps={FPS}", *_ENC, "-an", str(out)])
    return out


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def disclaimer_card(text: str, palette: list[str], out: Path, *, seconds: float = 3.5) -> Path:
    bg = palette[0] if palette else "#12222E"
    fg = palette[1] if len(palette) > 1 else "#FFFFFF"
    img = Image.new("RGB", (CW, CH), bg)
    d = ImageDraw.Draw(img)
    font = _font(46)
    small = _font(34)
    lines = _wrap(d, text, font, CW - 200)
    total_h = len(lines) * 60
    y = (CH - total_h) // 2
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((CW - w) / 2, y), ln, font=font, fill=fg)
        y += 60
    tag = "Not financial, legal, or medical advice."
    d.text(((CW - d.textlength(tag, font=small)) / 2, y + 40), tag, font=small, fill=fg)
    png = out.with_suffix(".png")
    img.save(png)
    util.ffmpeg(["-loop", "1", "-t", f"{seconds:.2f}", "-i", str(png),
                 "-f", "lavfi", "-t", f"{seconds:.2f}", "-i", "anullsrc=r=48000:cl=stereo",
                 "-vf", f"scale={CW}:{CH},setsar=1,fps={FPS}",
                 *_ENC, "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)])
    return out


def render(project: "config.Project", tone: Tone, *, animated_clips: list[Path],
           shot_list: dict, vo_wav: Path, out_path: Path | None = None) -> Path:
    work = project.work_dir
    work.mkdir(parents=True, exist_ok=True)
    project.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_path or project.output_dir / f"{project.name}_final.mp4"

    body = _concat(animated_clips, work / "body.mp4", work)

    groups = cap_mod.collect_groups(shot_list)
    if groups:
        ass = cap_mod.build_ass(groups, tone, work / "captions.ass")
        body_cap = cap_mod.burn(body, ass, work / "body_captioned.mp4")
    else:
        body_cap = body

    # brand logos (top corners) + opening text hook, if project.json declares them
    body_cap = brand_mod.apply(body_cap, project, work=work)

    # audio bed
    bed = None
    mconf = tone.music
    if mconf.get("enabled"):
        dur = util.probe_duration(body_cap)
        bed = music.generate_bed(mconf.get("prompt", "subtle background music, no vocals"),
                                 dur, dest=work / "music_bed.wav", work_dir=work)
    final_audio = music.mix(vo_wav, bed, work / "final_audio.wav",
                            bed_gain_db=mconf.get("gain_db", -22.0))

    core = work / "core.mp4"
    util.ffmpeg(["-i", str(body_cap), "-i", str(final_audio),
                 "-map", "0:v:0", "-map", "1:a:0", *_ENC,
                 "-c:a", "aac", "-b:a", "192k", "-shortest", str(core)])

    segments = [core]
    disc_text = project.disclaimer_text
    if (tone.disclaimers_required or project.raw.get("disclaimer_text")) and disc_text:
        from . import style_packs
        card = disclaimer_card(disc_text, style_packs.palette(project.style_pack),
                               work / "disclaimer.mp4")
        segments.append(card)

    if len(segments) == 1:
        util.ffmpeg(["-i", str(core), "-c", "copy", "-movflags", "+faststart", str(out_path)])
    else:
        listf = work / "final_concat.txt"
        listf.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segments),
                         encoding="utf-8")
        util.ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listf),
                     *_ENC, "-c:a", "aac", "-b:a", "192k",
                     "-movflags", "+faststart", str(out_path)])

    dur = util.probe_duration(out_path)
    w, h = util.probe_size(out_path)
    manifest = {
        "project": project.name,
        "output": str(out_path),
        "duration_s": round(dur, 2),
        "resolution": f"{w}x{h}",
        "shots": len(shot_list["shots"]),
        "caption_pops": len(groups),
        "style_pack": project.style_pack["id"],
        "tone_profile": tone.id,
        "music": bool(bed),
        "disclaimer_card": len(segments) > 1,
    }
    util.write_json(project.output_dir / f"{project.name}_manifest.json", manifest)
    util.log(f"render: {out_path.name}  {dur:.1f}s  {w}x{h}", level="ok")
    return out_path
