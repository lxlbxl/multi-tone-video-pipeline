import copy

import pytest

from pipeline import config, narrative
from pipeline.tone import load as load_tone


def _proj():
    return config.load_project(config.util.REPO_ROOT / "projects" /
                               "example_playful_app" / "project.json")


def _words(dur=30.0, n=90):
    step = dur / n
    return [{"word": f"w{i}", "start": round(i * step, 3),
             "end": round((i + 1) * step, 3)} for i in range(n)]


def test_scaffold_respects_min_hold():
    p = _proj()
    t = load_tone(p.tone_profile)          # shot_hold_seconds_min = 3
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    for s in sl["shots"]:
        assert s["end"] - s["start"] >= t.shot_hold_seconds_min - 0.01
    assert sl["shots"][0]["start"] == 0.0
    assert abs(sl["shots"][-1]["end"] - 30.0) < 0.1


def test_scaffold_validates():
    p = _proj()
    t = load_tone(p.tone_profile)
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    narrative.validate(sl, p, t, audio_duration=30.0, strict=False)


def test_validate_flags_fast_cut():
    p = _proj()
    t = load_tone(p.tone_profile)
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    sl["shots"][0]["end"] = sl["shots"][0]["start"] + 1.0   # too short
    sl["shots"][1]["start"] = sl["shots"][0]["end"]
    with pytest.raises(narrative.ShotListError, match="hold"):
        narrative.validate(sl, p, t, audio_duration=30.0)


def test_validate_flags_unknown_character():
    p = _proj()
    t = load_tone(p.tone_profile)
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    sl["shots"][0]["characters"] = ["nobody"]
    with pytest.raises(narrative.ShotListError, match="not in the bible"):
        narrative.validate(sl, p, t, audio_duration=30.0)


def test_validate_flags_caption_overflow():
    p = _proj()
    t = load_tone(p.tone_profile)          # max_words_per_pop = 1
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    sl["shots"][0]["captions"] = [{"text": "way too many words here",
                                   "start": 0.1, "end": 1.0}]
    with pytest.raises(narrative.ShotListError, match="words"):
        narrative.validate(sl, p, t, audio_duration=30.0)


def test_validate_flags_overrun_past_audio():
    p = _proj()
    t = load_tone(p.tone_profile)
    sl = narrative.scaffold(p, t, _words(30), 30.0)
    sl["shots"][-1]["end"] = 45.0
    with pytest.raises(narrative.ShotListError, match="past the"):
        narrative.validate(sl, p, t, audio_duration=30.0)
