"""
(5) tone.py — read a tone/brand profile and expose it as typed settings:
voice, pacing, caption style, motion intensity, narrative template, disclaimer
flag, optional music bed.

Also maps the spec's OpenAI-style `tts_voice_id` names ("onyx", "echo", …) onto
the ElevenLabs voices that `kie-cli elevenlabs_tts` actually accepts. A value
that is already a valid ElevenLabs voice name passes through untouched.
"""
from __future__ import annotations

from dataclasses import dataclass

# kie-cli elevenlabs_tts --voice choices
_ELEVEN_VOICES = {
    "Rachel", "Aria", "Roger", "Sarah", "Laura", "Charlie", "George", "Callum",
    "River", "Liam", "Charlotte", "Alice", "Matilda", "Will", "Jessica", "Eric",
    "Chris", "Brian", "Daniel", "Lily", "Bill",
}

# OpenAI TTS voice name -> nearest ElevenLabs voice in the kie-cli set
_OPENAI_MAP = {
    "alloy": "Sarah",
    "echo": "Charlie",
    "fable": "Alice",
    "onyx": "George",
    "nova": "Aria",
    "shimmer": "Jessica",
    "ash": "Brian",
    "ballad": "Will",
    "coral": "Laura",
    "sage": "River",
    "verse": "Liam",
}

_MOTION = {
    "low":    {"zoom_per_s": 0.010, "pan_pct": 0.02, "xfade_s": 0.60, "pop_ms": 130, "rotate_deg": 0.0},
    "medium": {"zoom_per_s": 0.020, "pan_pct": 0.05, "xfade_s": 0.40, "pop_ms":  90, "rotate_deg": 0.4},
    "high":   {"zoom_per_s": 0.033, "pan_pct": 0.09, "xfade_s": 0.25, "pop_ms":  60, "rotate_deg": 0.8},
}


@dataclass
class Tone:
    id: str
    voice_style: str
    tts_voice_id: str
    tts_model: str
    tts_stability: float
    tts_style: float
    pacing_wpm: int
    caption_style: dict
    narrative_template: str
    shot_hold_seconds_min: float
    motion_intensity: str
    disclaimers_required: bool
    disclaimer_text: str
    music: dict

    # derived --------------------------------------------------------------
    @property
    def eleven_voice(self) -> str:
        v = self.tts_voice_id
        if v in _ELEVEN_VOICES:
            return v
        return _OPENAI_MAP.get(v.lower(), "Rachel")

    @property
    def tts_speed(self) -> float:
        """Map pacing_wpm onto the ElevenLabs 0.7–1.2 speed range (150 wpm = 1.0)."""
        return round(min(1.2, max(0.7, self.pacing_wpm / 150.0)), 2)

    @property
    def motion(self) -> dict:
        return _MOTION.get(self.motion_intensity, _MOTION["medium"])

    def caption(self, key: str, default=None):
        return self.caption_style.get(key, default)


def load(tone_doc: dict) -> Tone:
    cs = dict(tone_doc["caption_style"])
    cs.setdefault("font_family", "Arial")
    cs.setdefault("stroke_px", 6)
    cs.setdefault("uppercase", False)
    cs.setdefault("position", "lower_third")
    return Tone(
        id=tone_doc["id"],
        voice_style=tone_doc["voice_style"],
        tts_voice_id=tone_doc["tts_voice_id"],
        tts_model=tone_doc.get("tts_model", "multilingual"),
        tts_stability=float(tone_doc.get("tts_stability", 0.5)),
        tts_style=float(tone_doc.get("tts_style", 0.2)),
        pacing_wpm=int(tone_doc["pacing_wpm"]),
        caption_style=cs,
        narrative_template=tone_doc["narrative_template"],
        shot_hold_seconds_min=float(tone_doc["shot_hold_seconds_min"]),
        motion_intensity=tone_doc["motion_intensity"],
        disclaimers_required=bool(tone_doc["disclaimers_required"]),
        disclaimer_text=tone_doc.get("disclaimer_text", ""),
        music=dict(tone_doc.get("music", {"enabled": False})),
    )
