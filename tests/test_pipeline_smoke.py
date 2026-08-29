"""End-to-end with Kie fully stubbed: exercises tts -> align -> refs ->
backgrounds -> shotlist -> shots -> animate -> render on real ffmpeg."""
import json
import os
import shutil
import wave

import pytest

from conftest import requires_ffmpeg
from pipeline import cli, util


def _silent_wav(path, seconds=6.0, rate=48000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))


@requires_ffmpeg
def test_full_run_auto(tmp_path, repo_root, monkeypatch):
    # build a clean minimal project (don't copytree — that would drag in any
    # local work/ or shots/ from a real run)
    proj_src = repo_root / "projects" / "smoke_test"
    proj = tmp_path / "smoke_test"
    (proj / "scripts").mkdir(parents=True)
    (proj / "work").mkdir()
    shutil.copyfile(proj_src / "project.json", proj / "project.json")
    shutil.copyfile(proj_src / "scripts" / "smoke_test.txt", proj / "scripts" / "smoke_test.txt")
    shutil.copytree(proj_src / "tone_profiles", proj / "tone_profiles")

    # stub TTS output so no network + deterministic duration; scaffold will
    # size the shot list to this exact length
    _silent_wav(proj / "work" / "vo.wav", 7.0)

    monkeypatch.setenv("MTVP_FAKE_KIE", "1")
    monkeypatch.setenv("MTVP_SKIP_UPLOAD", "1")
    monkeypatch.setenv("MTVP_FAKE_MEDIA", str(repo_root / "tests" / "fixtures" / "ref.png"))
    # keep generated refs/backgrounds out of the real repo tree
    monkeypatch.setenv("MTVP_ASSET_ROOT", str(proj))

    args = cli.build_parser().parse_args([
        "--project", str(proj / "project.json"),
        "--from", "align", "--auto", "--yes",
    ])
    rc = cli.run(args)
    assert rc == 0

    out = proj / "output" / "smoke_test_final.mp4"
    assert out.exists()
    dur = util.probe_duration(out)
    assert 5.0 < dur < 12.0
    assert util.probe_size(out) == (1080, 1920)

    manifest = json.loads((proj / "output" / "smoke_test_manifest.json").read_text())
    assert manifest["resolution"] == "1080x1920"
    assert manifest["shots"] >= 1


@requires_ffmpeg
def test_dry_run_makes_no_calls(repo_root, capsys):
    args = cli.build_parser().parse_args([
        "--project", str(repo_root / "projects" / "example_playful_app" / "project.json"),
        "--dry-run",
    ])
    assert cli.run(args) == 0
    assert "dry-run" in capsys.readouterr().out.lower()
