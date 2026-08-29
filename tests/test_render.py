import wave

from conftest import requires_ffmpeg
from pipeline import music, render, util


def _silent_wav(path, seconds=3.0, rate=48000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))


@requires_ffmpeg
def test_disclaimer_card_is_3s_video(tmp_path):
    out = render.disclaimer_card(
        "This is general information only and not financial advice.",
        ["#12222E", "#FFFFFF", "#4A90A4"], tmp_path / "disc.mp4", seconds=3.0)
    assert out.exists()
    assert abs(util.probe_duration(out) - 3.0) < 0.2
    assert util.probe_size(out) == (1080, 1920)


@requires_ffmpeg
def test_music_mix_without_bed_normalizes(tmp_path):
    vo = tmp_path / "vo.wav"
    _silent_wav(vo, 4.0)
    out = music.mix(vo, None, tmp_path / "mix.wav")
    assert out.exists()
    assert abs(util.probe_duration(out) - 4.0) < 0.3


@requires_ffmpeg
def test_music_mix_with_bed_ducks(tmp_path):
    vo = tmp_path / "vo.wav"
    bed = tmp_path / "bed.wav"
    _silent_wav(vo, 4.0)
    _silent_wav(bed, 4.0)
    out = music.mix(vo, bed, tmp_path / "mix.wav", bed_gain_db=-20)
    assert out.exists()
    assert abs(util.probe_duration(out) - 4.0) < 0.4
