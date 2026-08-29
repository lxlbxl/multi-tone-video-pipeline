from pipeline import tone as tone_mod
from pipeline import util

PLAYFUL = util.read_json(util.REPO_ROOT / "tone_profiles" / "playful_consumer.json")
FINANCE = util.read_json(util.REPO_ROOT / "tone_profiles" / "serious_finance.json")


def test_openai_voice_mapped_to_elevenlabs():
    t = tone_mod.load(PLAYFUL)          # tts_voice_id "echo"
    assert t.eleven_voice == "Charlie"
    f = tone_mod.load(FINANCE)          # "onyx"
    assert f.eleven_voice == "George"


def test_wpm_to_speed():
    assert tone_mod.load(PLAYFUL).tts_speed > 1.0   # 175 wpm
    assert tone_mod.load(FINANCE).tts_speed < 1.0   # 145 wpm


def test_motion_scales_with_intensity():
    hi = tone_mod.load(PLAYFUL).motion
    lo = tone_mod.load(FINANCE).motion
    assert hi["zoom_per_s"] > lo["zoom_per_s"]
    assert hi["xfade_s"] < lo["xfade_s"]


def test_direct_elevenlabs_name_passthrough():
    doc = dict(PLAYFUL, tts_voice_id="Matilda")
    assert tone_mod.load(doc).eleven_voice == "Matilda"
