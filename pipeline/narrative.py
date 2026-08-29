"""
(6) narrative.py — the shot list: schema, scaffold, and validator.

The creative fill (composition lines, which character is in which shot, caption
wording) is done by the operator/LLM using the prompt in
references/prompt_templates.md. This module:

  * `scaffold()` — lay the narrative template's beats across the aligned VO
    timeline, honouring `shot_hold_seconds_min`, producing a valid starting
    shot_list.json the operator then edits.
  * `validate()` — hard gate before any image generation: schema, timing,
    minimum hold, known characters, resolvable backgrounds, caption coverage.
"""
from __future__ import annotations

from . import config, util
from .tone import Tone


class ShotListError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# scaffold
# --------------------------------------------------------------------------- #
def _expand_beats(template: dict, n_shots_hint: int) -> list[dict]:
    beats = template["beats"]
    fixed = [b for b in beats if not b.get("repeatable")]
    rep = [b for b in beats if b.get("repeatable")]
    if not rep:
        return list(beats)
    extra = max(1, n_shots_hint - len(fixed))
    out: list[dict] = []
    for b in beats:
        if b.get("repeatable"):
            out.extend({**b, "id": f"{b['id']}{i+1}"} for i in range(extra))
        else:
            out.append(b)
    return out


def scaffold(project: "config.Project", tone: Tone, words: list[dict],
             audio_duration: float) -> dict:
    hold = tone.shot_hold_seconds_min
    max_shots = max(1, int(audio_duration // hold))
    beats = _expand_beats(project.narrative_template, max_shots)
    if len(beats) > max_shots:
        # merge tail beats so no shot is shorter than the minimum hold
        beats = beats[:max_shots - 1] + [beats[max_shots - 1]]
    weights = [float(b.get("weight", 1.0)) for b in beats]
    wsum = sum(weights)

    def caption_slice(a: float, b: float) -> list[dict]:
        segs = [w for w in words if w["end"] > a + 0.01 and w["start"] < b - 0.01]
        pops = []
        mw = tone.caption_style["max_words_per_pop"]
        for i in range(0, len(segs), mw):
            grp = segs[i:i + mw]
            if grp:
                pops.append({"text": " ".join(w["word"] for w in grp),
                             "start": round(grp[0]["start"], 3),
                             "end": round(grp[-1]["end"], 3)})
        return pops

    bg_names = [b["name"] for b in project.backgrounds]
    chars = [c["name"] for c in project.characters]
    shots, clock = [], 0.0
    for i, beat in enumerate(beats):
        end = audio_duration if i == len(beats) - 1 else round(clock + audio_duration * weights[i] / wsum, 2)
        end = max(end, clock + hold)
        end = min(end, audio_duration)
        shots.append({
            "shot_id": f"s{i+1:02d}",
            "beat": beat["id"],
            "start": round(clock, 2),
            "end": round(end, 2),
            "characters": chars[:1],
            "background": bg_names[i % len(bg_names)] if bg_names else "auto",
            "background_query": [],
            "composition": f"[{beat['purpose']}] — describe the frame: who is in it, "
                           f"where they stand, what they are doing, camera framing",
            "motion": {"type": "ken_burns", "direction": "in" if i % 2 == 0 else "out"},
            "captions": caption_slice(clock, end),
        })
        clock = end
    return {
        "project": project.name,
        "audio_duration": round(audio_duration, 3),
        "narrative_template": project.narrative_template["id"],
        "shots": shots,
    }


# --------------------------------------------------------------------------- #
# validate
# --------------------------------------------------------------------------- #
def validate(shot_list: dict, project: "config.Project", tone: Tone, *,
             audio_duration: float | None = None, strict: bool = True) -> list[str]:
    config.validate(shot_list, "shot_list", where="shot_list.json")
    errs: list[str] = []
    warn: list[str] = []

    dur = audio_duration if audio_duration is not None else shot_list["audio_duration"]
    hold = tone.shot_hold_seconds_min
    known_chars = {c["name"] for c in project.characters}
    known_bgs = {b["name"] for b in project.backgrounds}
    mw = tone.caption_style["max_words_per_pop"]

    shots = shot_list["shots"]
    prev_end = 0.0
    for s in shots:
        sid = s["shot_id"]
        length = s["end"] - s["start"]
        if s["start"] < prev_end - 0.05:
            errs.append(f"{sid}: starts at {s['start']}s, before previous shot ended ({prev_end}s)")
        if s["start"] > prev_end + 0.35:
            warn.append(f"{sid}: {s['start'] - prev_end:.2f}s gap before this shot")
        if length < hold * 0.9:
            errs.append(f"{sid}: {length:.2f}s hold < tone minimum {hold}s "
                        f"({tone.id} must not cut faster than this)")
        if s["end"] > dur + 0.25:
            errs.append(f"{sid}: ends at {s['end']}s, past the {dur:.2f}s voice-over")
        for c in s["characters"]:
            if c not in known_chars:
                errs.append(f"{sid}: character '{c}' not in the bible ({sorted(known_chars)})")
        if len(s["characters"]) > 3:
            warn.append(f"{sid}: {len(s['characters'])} characters — reference-conditioned "
                        "gen gets unreliable past 3")
        bg = s["background"]
        if bg not in ("auto",) and bg not in known_bgs:
            if known_bgs:
                errs.append(f"{sid}: background '{bg}' not in the library ({sorted(known_bgs)})")
        if bg == "auto" and not s.get("background_query") and known_bgs:
            warn.append(f"{sid}: background 'auto' with no background_query — will pick the first")
        if s["motion"]["type"] == "pose_crossfade" and not s["motion"].get("pose_b"):
            errs.append(f"{sid}: motion pose_crossfade needs motion.pose_b")
        # caption coverage + width
        caps = s["captions"]
        for cpt in caps:
            if cpt["start"] < s["start"] - 0.05 or cpt["end"] > s["end"] + 0.3:
                warn.append(f"{sid}: caption '{cpt['text'][:20]}…' outside the shot window")
            if len(cpt["text"].split()) > mw:
                errs.append(f"{sid}: caption '{cpt['text']}' has >{mw} words "
                            f"(tone {tone.id} caps at {mw}/pop)")
        if not caps:
            warn.append(f"{sid}: no captions")
        prev_end = s["end"]

    if shots and shots[0]["start"] > 0.05:
        errs.append(f"first shot starts at {shots[0]['start']}s — cover from 0")
    if shots and abs(shots[-1]["end"] - dur) > 1.0:
        warn.append(f"last shot ends {shots[-1]['end']}s vs {dur:.2f}s VO — trailing gap/overrun")

    for w in warn:
        util.log(w, level="warn")
    if errs and strict:
        raise ShotListError("shot list invalid:\n  - " + "\n  - ".join(errs))
    return errs
