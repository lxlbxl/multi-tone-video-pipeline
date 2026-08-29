"""
(3-adjacent) tts.py — voice-over from the script using the tone profile's
voice, pacing and delivery settings, via `kie-cli elevenlabs_tts`.

Long scripts are split on sentence boundaries into <=4500-char chunks,
synthesised separately and concatenated, so pacing/voice stay identical across
the whole read.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import kie, util
from .tone import Tone

_MAX_CHARS = 4500
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _chunks(text: str) -> list[str]:
    text = " ".join(text.split())
    if len(text) <= _MAX_CHARS:
        return [text]
    out, cur = [], ""
    for sent in _SENT_SPLIT.split(text):
        if len(cur) + len(sent) + 1 > _MAX_CHARS and cur:
            out.append(cur.strip())
            cur = ""
        cur += sent + " "
    if cur.strip():
        out.append(cur.strip())
    return out


def synthesize(script_text: str, tone: Tone, *, out_wav: str | Path,
               work_dir: str | Path) -> Path:
    out_wav = Path(out_wav)
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    parts: list[Path] = []
    for i, chunk in enumerate(_chunks(script_text)):
        mp3 = work / f"vo_{i:02d}.mp3"
        kie.generate(
            "elevenlabs_tts",
            dest=mp3,
            timeout=300,
            text=chunk,
            voice=tone.eleven_voice,
            model=tone.tts_model,
            speed=tone.tts_speed,
            stability=tone.tts_stability,
            style=tone.tts_style,
            similarity_boost=0.75,
        )
        parts.append(mp3)

    if len(parts) == 1:
        util.ffmpeg(["-i", parts[0], "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out_wav])
    else:
        listf = work / "vo_concat.txt"
        listf.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts),
                         encoding="utf-8")
        util.ffmpeg(["-f", "concat", "-safe", "0", "-i", listf,
                     "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out_wav])

    dur = util.probe_duration(out_wav)
    util.log(f"tts: {out_wav.name}  {dur:.1f}s  voice={tone.eleven_voice} "
             f"speed={tone.tts_speed}", level="ok")
    return out_wav
