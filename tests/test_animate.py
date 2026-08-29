import pytest

from conftest import requires_ffmpeg
from pipeline import animate, util
from pipeline.tone import load as load_tone

PLAYFUL = load_tone(util.read_json(util.REPO_ROOT / "tone_profiles" / "playful_consumer.json"))
FINANCE = load_tone(util.read_json(util.REPO_ROOT / "tone_profiles" / "serious_finance.json"))


@requires_ffmpeg
@pytest.mark.parametrize("mtype,direction", [
    ("ken_burns", "in"), ("ken_burns", "left"), ("parallax", "out"), ("hold", "in"),
])
def test_single_still_moves(tmp_path, fixture_png, mtype, direction):
    out = tmp_path / "clip.mp4"
    animate.animate_shot([fixture_png], out, duration=3.0,
                         motion={"type": mtype, "direction": direction},
                         tone=PLAYFUL, work_dir=tmp_path / "w")
    assert out.exists()
    assert abs(util.probe_duration(out) - 3.0) < 0.25
    assert util.probe_size(out) == (1080, 1920)


@requires_ffmpeg
def test_pose_crossfade(tmp_path, fixture_png):
    out = tmp_path / "pc.mp4"
    animate.animate_shot([fixture_png, fixture_png], out, duration=4.0,
                         motion={"type": "pose_crossfade", "pose_b": "b"},
                         tone=PLAYFUL, work_dir=tmp_path / "w")
    assert abs(util.probe_duration(out) - 4.0) < 0.3


@requires_ffmpeg
def test_animate_all(tmp_path, fixture_png):
    sl = {"shots": [
        {"shot_id": "s01", "start": 0.0, "end": 3.0, "motion": {"type": "ken_burns", "direction": "in"}},
        {"shot_id": "s02", "start": 3.0, "end": 6.5, "motion": {"type": "ken_burns", "direction": "out"}},
    ]}
    imgs = {"s01": [str(fixture_png)], "s02": [str(fixture_png)]}
    clips = animate.animate_all(sl, imgs, FINANCE, work_dir=tmp_path / "w", out_dir=tmp_path / "c")
    assert len(clips) == 2
    assert all(c.exists() for c in clips)
