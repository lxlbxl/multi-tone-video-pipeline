"""
align.py — word-level timing for the voice-over.

The spec calls this the "Whisper alignment" step. `kie-cli`'s TTS does not
return word timestamps, so this module resolves them with a fallback chain and
always produces *something* usable:

  1. faster-whisper  (pip install faster-whisper) — real forced-ish alignment
  2. Gemini          (GEMINI_API_KEY) — transcription with word offsets
  3. proportional    — distribute the known script across the known audio
                       duration, weighting by token length + punctuation pauses

Captions in this pipeline are 1–3 words per pop, so even the proportional
fallback lands close enough to feel synced. Method 1/2 just make it tighter.

Output: list of {"word": str, "start": float, "end": float} covering the audio.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

from . import util

_WORD_RE = re.compile(r"\S+")
_TRAIL_PUNCT = re.compile(r"[.,!?;:—…\-]+$")


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.replace("\n", " "))


# --------------------------------------------------------------------------- #
# 3. proportional (always available)
# --------------------------------------------------------------------------- #
def _proportional(audio_path: str | Path, script_text: str) -> list[dict]:
    dur = util.probe_duration(audio_path) or _estimate_duration(script_text)
    toks = _tokens(script_text)
    if not toks:
        return []
    weights = []
    for t in toks:
        w = max(1.0, len(_TRAIL_PUNCT.sub("", t)))
        m = _TRAIL_PUNCT.search(t)
        if m:
            w += 5.0 if any(c in m.group(0) for c in ".!?") else 2.5
        weights.append(w)
    total = sum(weights)
    out, clock = [], 0.0
    for tok, wt in zip(toks, weights):
        span = dur * wt / total
        out.append({"word": tok, "start": round(clock, 3), "end": round(clock + span, 3)})
        clock += span
    out[-1]["end"] = round(dur, 3)
    return out


def _estimate_duration(script_text: str, wpm: int = 155) -> float:
    return max(1.0, len(_tokens(script_text)) / wpm * 60.0)


# --------------------------------------------------------------------------- #
# 1. faster-whisper
# --------------------------------------------------------------------------- #
def _faster_whisper(audio_path: str | Path) -> list[dict] | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return None
    model_name = os.environ.get("MTVP_WHISPER_MODEL", "base")
    util.log(f"align: faster-whisper ({model_name})")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
    words: list[dict] = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({"word": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3)})
    return words or None


# --------------------------------------------------------------------------- #
# 2. Gemini
# --------------------------------------------------------------------------- #
def _gemini(audio_path: str | Path) -> list[dict] | None:
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_1")
           or os.environ.get("GOOGLE_API_KEY"))
    if not key:
        return None
    import base64
    model = os.environ.get("MTVP_GEMINI_MODEL", "gemini-2.5-flash")
    raw = Path(audio_path).read_bytes()
    mime = "audio/wav" if str(audio_path).lower().endswith(".wav") else "audio/mpeg"
    prompt = ("Transcribe this audio. Return ONLY compact JSON: "
              '{"words":[{"word":"...","start":<sec>,"end":<sec>}]} '
              "with one entry per spoken word and precise second offsets.")
    body = json.dumps({
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}},
        ]}],
        "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
    }).encode()
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    try:
        util.log("align: gemini transcription")
        resp = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, data=body,
                                   headers={"Content-Type": "application/json"}),
            timeout=120).read().decode())
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
        words = json.loads(text).get("words", [])
        clean = [{"word": str(w["word"]).strip(),
                  "start": float(w["start"]), "end": float(w["end"])}
                 for w in words if w.get("word")]
        return clean or None
    except Exception as e:  # noqa: BLE001
        util.log(f"align: gemini failed ({e}); falling back", level="warn")
        return None


# --------------------------------------------------------------------------- #
# public
# --------------------------------------------------------------------------- #
def align_words(audio_path: str | Path, script_text: str, *,
                method: str = "auto") -> list[dict]:
    """
    method:
      auto         faster-whisper if installed, else proportional
                   (add MTVP_ALIGN_GEMINI=1 to slot Gemini in between)
      whisper      faster-whisper only, else proportional
      gemini       Gemini transcription, else proportional
      proportional force the estimate
    """
    words: list[dict] | None = None
    use_gemini = method == "gemini" or (method == "auto" and util.env_flag("MTVP_ALIGN_GEMINI"))
    if method in ("auto", "whisper"):
        words = _faster_whisper(audio_path)
    if words is None and use_gemini:
        words = _gemini(audio_path)
    if words is None:
        if method not in ("auto", "proportional"):
            util.log("align: requested method unavailable — using proportional estimate",
                     level="warn")
        words = _proportional(audio_path, script_text)
    # clamp to audio, enforce monotonic, non-zero spans
    dur = util.probe_duration(audio_path) or (words[-1]["end"] if words else 0.0)
    clock = 0.0
    for w in words:
        w["start"] = max(clock, min(float(w["start"]), dur))
        w["end"] = max(w["start"] + 0.05, min(float(w["end"]), dur))
        clock = w["end"]
    return words


def group_words(words: list[dict], max_words_per_pop: int) -> list[dict]:
    """Chunk aligned words into caption 'pops' of at most N words, breaking early
    on sentence-final punctuation so a pop never straddles two sentences."""
    groups: list[dict] = []
    buf: list[dict] = []

    def flush() -> None:
        if buf:
            groups.append({
                "text": " ".join(_TRAIL_PUNCT.sub("", w["word"]) if i < len(buf) - 1
                                 else w["word"] for i, w in enumerate(buf)),
                "start": round(buf[0]["start"], 3),
                "end": round(buf[-1]["end"], 3),
            })
            buf.clear()

    for w in words:
        buf.append(w)
        ends_sentence = bool(re.search(r"[.!?]$", w["word"]))
        if len(buf) >= max_words_per_pop or ends_sentence:
            flush()
    flush()
    return groups
