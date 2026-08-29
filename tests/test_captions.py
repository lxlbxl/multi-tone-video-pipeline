from pipeline import captions
from pipeline import util
from pipeline.tone import load as load_tone

PLAYFUL = load_tone(util.read_json(util.REPO_ROOT / "tone_profiles" / "playful_consumer.json"))
FINANCE = load_tone(util.read_json(util.REPO_ROOT / "tone_profiles" / "serious_finance.json"))


def test_ass_colour_bgr_order():
    # #FFF200 -> &H00 00 F2 FF  (AA BB GG RR)
    assert captions._ass_colour("#FFF200") == "&H0000F2FF"
    assert captions._ass_colour("#000000") == "&H00000000"


def test_build_ass_one_dialogue_per_group(tmp_path):
    groups = [
        {"text": "one", "start": 0.0, "end": 0.6},
        {"text": "two", "start": 0.6, "end": 1.2},
        {"text": "three", "start": 1.2, "end": 1.9},
    ]
    out = captions.build_ass(groups, PLAYFUL, tmp_path / "c.ass")
    body = out.read_text(encoding="utf-8")
    assert body.count("\nDialogue:") == 3
    assert "PlayResX: 1080" in body
    assert "\\fscx" in body            # high intensity -> scale bounce


def test_low_intensity_uses_fade_only(tmp_path):
    out = captions.build_ass([{"text": "calm", "start": 0.0, "end": 1.0}],
                             FINANCE, tmp_path / "c.ass")
    body = out.read_text(encoding="utf-8")
    assert "\\fad(" in body
    assert "\\fscx" not in body


def test_uppercase_applied(tmp_path):
    out = captions.build_ass([{"text": "loud", "start": 0.0, "end": 1.0}],
                             PLAYFUL, tmp_path / "c.ass")
    assert "LOUD" in out.read_text(encoding="utf-8")


def test_collect_groups_deoverlaps():
    sl = {"shots": [
        {"shot_id": "s01", "captions": [{"text": "a", "start": 0.0, "end": 1.0}]},
        {"shot_id": "s02", "captions": [{"text": "b", "start": 0.5, "end": 1.5}]},
    ]}
    g = captions.collect_groups(sl)
    assert g[0]["end"] <= g[1]["start"] + 1e-6
