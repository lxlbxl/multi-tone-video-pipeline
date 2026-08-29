"""
tts.py — voice-over from the script using the tone profile's voice, pacing and
delivery settings.

Two backends, picked automatically:

  * **Direct ElevenLabs** — used when ELEVENLABS_API_KEY is set (and
    MTVP_TTS_VIA_KIE is not). Full voice library, finer control, and it returns
    native word timestamps, which are written straight to work/words.json so
    the `align` stage can skip the estimate.
  * **kie-cli** (`elevenlabs_tts`) — the zero-setup fallback. Still ElevenLabs
    under the hood, but only the 21 preset voices and no timestamps.

Long scripts are split on sentence boundaries into <=4500-char chunks and
concatenated so pacing/voice stay identical across the whole read.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
from pathlib import Path

from . import kie, util
from .tone import Tone

_MAX_CHARS = 4500
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# ElevenLabs voice_id for each name kie-cli exposes (so a tone profile written
# for the kie backend still resolves under the direct backend).
_ELEVEN_IDS = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM", "Aria": "9BWtsMINqrJLrRacOk9x",
    "Roger": "CwhRBWXzGAHq8TQ4Fs17", "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Laura": "FGY2WhTYpPnrIDTdsKH5", "Charlie": "IKne3meq5aSn9XLyUdCD",
    "George": "JBFqnCBsd6RMkjVDRZzb", "Callum": "N2lVS1w4EtoT3dr4eOWO",
    "River": "SAz9YHcvj6GT2YYXdXww", "Liam": "TX3LPaxmHKxFdv7VOQHJ",
    "Charlotte": "XB0fDUnXU5powFXDhCwa", "Alice": "Xb7hH8MSUJpSbSDYk0k2",
    "Matilda": "XrExE9yKIg1WjnnlVkGX", "Will": "bIHbv24MWmeRgasZH58o",
    "Jessica": "cgSgspJ2msm6clMCkdW9", "Eric": "cjVigY5qzO86Huf0OWal",
    "Chris": "iP95p4xoKVk53GoZ742B", "Brian": "nPczCjzI2devNBz1zQrb",
    "Daniel": "onwK4e9ZLuTAKqWW03F9", "Lily": "pFZP5JQG7iQjIQuC4Bku",
    "Bill": "pqHfZKP75CvOlQylNhV4",
}


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


def _use_direct() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY")) and not util.env_flag("MTVP_TTS_VIA_KIE")


def _resolve_voice_id(tone: Tone) -> str:
    v = tone.tts_voice_id
    if re.fullmatch(r"[A-Za-z0-9]{20}", v):        # already an ElevenLabs id
        return v
    if v in _ELEVEN_IDS:
        return _ELEVEN_IDS[v]
    return _ELEVEN_IDS.get(tone.eleven_voice, _ELEVEN_IDS["Rachel"])


def _words_from_alignment(al: dict, offset: float) -> list[dict]:
    chars = al.get("characters") or []
    starts = al.get("character_start_times_seconds") or []
    ends = al.get("character_end_times_seconds") or []
    words: list[dict] = []
    cur, w_start = "", None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                words.append({"word": cur, "start": round(w_start + offset, 3),
                              "end": round(prev_e + offset, 3)})
                cur, w_start = "", None
            continue
        if not cur:
            w_start = s
        cur += ch
        prev_e = e
    if cur:
        words.append({"word": cur, "start": round(w_start + offset, 3),
                      "end": round(prev_e + offset, 3)})
    return words


def _eleven_direct(script_text: str, tone: Tone, *, out_wav: Path, work: Path) -> list[dict]:
    key = os.environ["ELEVENLABS_API_KEY"]
    vid = _resolve_voice_id(tone)
    model = "eleven_multilingual_v2" if tone.tts_model == "multilingual" else "eleven_turbo_v2_5"
    util.log(f"tts: direct ElevenLabs voice={vid} model={model}")

    parts: list[Path] = []
    all_words: list[dict] = []
    offset = 0.0
    for i, chunk in enumerate(_chunks(script_text)):
        body = json.dumps({
            "text": chunk,
            "model_id": model,
            "voice_settings": {
                "stability": tone.tts_stability,
                "similarity_boost": 0.75,
                "style": tone.tts_style,
                "speed": tone.tts_speed,
                "use_speaker_boost": True,
            },
        }).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps",
            data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
        mp3 = work / f"vo_{i:02d}.mp3"
        mp3.write_bytes(base64.b64decode(resp["audio_base64"]))
        parts.append(mp3)
        al = resp.get("alignment") or resp.get("normalized_alignment") or {}
        chunk_words = _words_from_alignment(al, offset)
        all_words.extend(chunk_words)
        offset += util.probe_duration(mp3)

    _concat_to_wav(parts, out_wav, work)
    return all_words


def _concat_to_wav(parts: list[Path], out_wav: Path, work: Path) -> None:
    if len(parts) == 1:
        util.ffmpeg(["-i", parts[0], "-ar", "48000", "-ac", "1",
                     "-c:a", "pcm_s16le", out_wav])
        return
    listf = work / "vo_concat.txt"
    listf.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts),
                     encoding="utf-8")
    util.ffmpeg(["-f", "concat", "-safe", "0", "-i", listf,
                 "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out_wav])


def synthesize(script_text: str, tone: Tone, *, out_wav: str | Path,
               work_dir: str | Path) -> Path:
    out_wav = Path(out_wav)
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    if _use_direct():
        words = _eleven_direct(script_text, tone, out_wav=out_wav, work=work)
        if words:
            util.write_json(work / "words.json",
                            {"audio_duration": util.probe_duration(out_wav),
                             "words": words, "source": "elevenlabs"})
            util.log(f"tts: wrote {len(words)} native word timestamps", level="ok")
    else:
        parts: list[Path] = []
        for i, chunk in enumerate(_chunks(script_text)):
            mp3 = work / f"vo_{i:02d}.mp3"
            kie.generate("elevenlabs_tts", dest=mp3, timeout=300, text=chunk,
                         voice=tone.eleven_voice, model=tone.tts_model,
                         speed=tone.tts_speed, stability=tone.tts_stability,
                         style=tone.tts_style, similarity_boost=0.75)
            parts.append(mp3)
        _concat_to_wav(parts, out_wav, work)

    dur = util.probe_duration(out_wav)
    vlabel = _resolve_voice_id(tone) if _use_direct() else tone.eleven_voice
    util.log(f"tts: {out_wav.name}  {dur:.1f}s  voice={vlabel}  "
             f"speed={tone.tts_speed}", level="ok")
    return out_wav
