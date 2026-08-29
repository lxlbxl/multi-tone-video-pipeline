"""
(8) animate.py — turn a still (or a pose pair) into a moving shot with FFmpeg.
No video model: Ken Burns, parallax-style dual-rate drift, and pose-crossfade,
all scaled by the tone profile's `motion_intensity`.

  low     barely-there zoom, long crossfades
  medium  gentle push + drift
  high    snappier moves, faster crossfades, a touch of rotation

Every shot is rendered to the same contract (1080x1920, 30 fps, yuv420p,
libx264, no audio) so `render.py` can concat with -c copy.
"""
from __future__ import annotations

from pathlib import Path

from . import util
from .tone import Tone

CW, CH = util.CANVAS
FPS = util.FPS
OS = 2  # oversample factor — headroom for panning without hitting the edge

_DIR_VEC = {  # unit drift direction in the oversampled frame
    "in": (0.0, 0.0), "out": (0.0, 0.0),
    "left": (-1.0, 0.0), "right": (1.0, 0.0),
    "up": (0.0, -1.0), "down": (0.0, 1.0),
}

_ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]


def _clamp(expr: str, lo: str, hi: str) -> str:
    return f"max({lo}\\,min({expr}\\,{hi}))"


def _kenburns_filter(duration: float, motion: dict, m: dict, *,
                     parallax: bool = False) -> str:
    cw, chh = CW * OS, CH * OS
    direction = motion.get("direction", "in")
    zoom_total = m["zoom_per_s"] * duration * (1.6 if parallax else 1.0)
    zoom_total = min(zoom_total, 0.6)
    if direction == "out":
        z0, z1 = 1.0 + zoom_total, 1.0
    else:
        z0, z1 = 1.0, 1.0 + zoom_total

    pan_px = m["pan_pct"] * cw * (1.8 if parallax else 1.0)
    dvx, dvy = _DIR_VEC.get(direction, (0.0, 0.0))
    if direction in ("in", "out"):  # give in/out a faint diagonal life
        dvx, dvy = 0.3, -0.2
    dx, dy = dvx * pan_px, dvy * pan_px

    prog = f"min(t/{max(duration,0.1):.3f}\\,1)"
    zt = f"({z0:.4f}+({z1 - z0:.4f})*{prog})"
    cropw = f"trunc({cw}/{zt}/2)*2"
    croph = f"trunc({chh}/{zt}/2)*2"
    xexpr = _clamp(f"({cw}-{cropw})/2+({dx:.1f})*{prog}", "0", f"({cw}-{cropw})")
    yexpr = _clamp(f"({chh}-{croph})/2+({dy:.1f})*{prog}", "0", f"({chh}-{croph})")

    chain = [
        f"scale={cw}:{chh}:force_original_aspect_ratio=increase",
        f"crop={cw}:{chh}",
    ]
    if parallax:
        chain.append("gblur=sigma=0.6")
    chain += [
        f"crop=w='{cropw}':h='{croph}':x='{xexpr}':y='{yexpr}'",
        f"scale={CW}:{CH}",
        "setsar=1", f"fps={FPS}", "format=yuv420p",
    ]
    return ",".join(chain)


def _render_move(still: Path, out: Path, duration: float, motion: dict,
                 m: dict, *, parallax: bool = False) -> Path:
    vf = _kenburns_filter(duration, motion, m, parallax=parallax)
    util.ffmpeg(["-loop", "1", "-t", f"{duration:.3f}", "-i", str(still),
                 "-vf", vf, "-t", f"{duration:.3f}", *_ENC, str(out)])
    return out


def animate_shot(stills: list[Path], out: Path, *, duration: float, motion: dict,
                 tone: Tone, work_dir: Path) -> Path:
    """stills: [a] for ken_burns/parallax/hold, [a, b] for pose_crossfade."""
    m = tone.motion
    work_dir.mkdir(parents=True, exist_ok=True)
    mtype = motion["type"]

    if mtype == "pose_crossfade" and len(stills) >= 2:
        x = m["xfade_s"]
        half = (duration + x) / 2.0
        a = _render_move(stills[0], work_dir / f"{out.stem}_a.mp4", half,
                         {"type": "ken_burns", "direction": "in"}, m)
        b = _render_move(stills[1], work_dir / f"{out.stem}_b.mp4", half,
                         {"type": "ken_burns", "direction": "out"}, m)
        off = max(0.0, half - x)
        util.ffmpeg(["-i", str(a), "-i", str(b), "-filter_complex",
                     f"[0:v][1:v]xfade=transition=fade:duration={x:.3f}:offset={off:.3f},"
                     f"format=yuv420p,fps={FPS}",
                     "-t", f"{duration:.3f}", *_ENC, str(out)])
        return out

    if mtype == "hold":
        return _render_move(stills[0], out, duration,
                            {"type": "ken_burns", "direction": "in"},
                            {**m, "zoom_per_s": m["zoom_per_s"] * 0.25, "pan_pct": 0.0})

    return _render_move(stills[0], out, duration, motion, m,
                        parallax=(mtype == "parallax"))


def animate_all(shot_list: dict, shot_images: dict[str, list[str]], tone: Tone,
                *, work_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for s in shot_list["shots"]:
        stills = [Path(p) for p in shot_images[s["shot_id"]]]
        dur = round(s["end"] - s["start"], 3)
        dest = out_dir / f"{s['shot_id']}.mp4"
        animate_shot(stills, dest, duration=dur, motion=s["motion"], tone=tone,
                     work_dir=work_dir)
        got = util.probe_duration(dest)
        util.log(f"animate {s['shot_id']}: {s['motion']['type']} {dur:.2f}s "
                 f"(rendered {got:.2f}s)")
        clips.append(dest)
    util.log(f"animate: {len(clips)} shots", level="ok")
    return clips
