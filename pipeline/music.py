"""
music.py — optional background music bed (viral factor: sound-on design).

Uses `kie-cli suno_generate_music` when the tone profile enables music, then
sidechain-ducks it under the voice-over and normalises the mix for social
(-14 LUFS). If generation is disabled or fails, the pipeline continues with the
dry voice-over — music is never load-bearing.
"""
from __future__ import annotations

from pathlib import Path

from . import kie, util
from .tone import Tone


def _has_audio(path: str | Path) -> bool:
    try:
        return any(s.get("codec_type") == "audio"
                   for s in util.ffprobe_json(path).get("streams", []))
    except Exception:  # noqa: BLE001
        return False


def generate_bed(prompt: str, duration: float, *, dest: Path, work_dir: Path) -> Path | None:
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        src = work_dir / "music_raw.mp3"
        # kie-cli suno_generate_music: customMode + instrumental are required;
        # pass them as explicit "true"/"false" strings (yargs booleans).
        kie.generate("suno_generate_music", dest=src, timeout=900,
                     prompt=prompt[:490], model="V4_5",
                     customMode="false", instrumental="true")
    except Exception as e:  # noqa: BLE001
        util.log(f"music: generation skipped ({e})", level="warn")
        return None
    # guard: only proceed if we actually got audio
    if not _has_audio(src):
        util.log("music: result had no audio stream — continuing without a bed", level="warn")
        return None
    # loop / trim to length, gentle fades
    util.ffmpeg(["-stream_loop", "-1", "-i", str(src), "-t", f"{duration:.3f}",
                 "-af", f"afade=t=in:st=0:d=0.8,afade=t=out:st={max(0,duration-1.2):.3f}:d=1.2",
                 "-ar", "48000", "-ac", "2", str(dest)])
    return dest


def mix(vo_wav: str | Path, bed: str | Path | None, out_wav: str | Path, *,
        bed_gain_db: float = -22.0, target_lufs: float = -14.0) -> Path:
    out_wav = Path(out_wav)
    if not bed:
        util.ffmpeg(["-i", str(vo_wav), "-af",
                     f"loudnorm=I={target_lufs}:TP=-1.0:LRA=11",
                     "-ar", "48000", "-ac", "2", str(out_wav)])
        return out_wav
    fc = (
        f"[1:a]volume={bed_gain_db}dB,aformat=channel_layouts=stereo[bed];"
        f"[0:a]aformat=channel_layouts=stereo[vo];"
        f"[bed][vo]sidechaincompress=threshold=0.03:ratio=12:attack=15:release=350[ducked];"
        f"[vo][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];"
        f"[mix]loudnorm=I={target_lufs}:TP=-1.0:LRA=11[out]"
    )
    util.ffmpeg(["-i", str(vo_wav), "-i", str(bed), "-filter_complex", fc,
                 "-map", "[out]", "-ar", "48000", "-ac", "2", str(out_wav)])
    return out_wav
