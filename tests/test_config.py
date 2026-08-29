import json

import pytest

from pipeline import config


def test_loads_example(example_project):
    p = config.load_project(example_project)
    assert p.name == "example_playful_app"
    assert p.style_pack["id"] == "stick_figure_v1"
    assert p.tone_profile["id"] == "playful_consumer"
    assert p.narrative_template["id"] == "myth_bust"
    assert [c["name"] for c in p.characters] == ["hoodie_guy", "coach_woman", "future_guy"]
    assert len(p.backgrounds) == 3
    assert all(b["tags"] for b in p.backgrounds)
    assert p.script_path and p.script_path.exists()


def test_finance_example(repo_root):
    p = config.load_project(repo_root / "projects" / "example_finance" / "project.json")
    assert p.tone_profile["disclaimers_required"] is True
    assert p.disclaimer_text  # inherited from the tone profile
    assert p.style_pack["id"] == "flat_corporate_v1"


def _write(tmp_path, obj):
    d = tmp_path / "projects" / "p"
    (d / "scripts").mkdir(parents=True)
    (d / "scripts" / "s.txt").write_text("hi there friend", encoding="utf-8")
    (d / "project.json").write_text(json.dumps(obj), encoding="utf-8")
    return d / "project.json"


BASE = {
    "name": "p", "style_pack": "stick_figure_v1", "tone_profile": "playful_consumer",
    "script": "scripts/s.txt",
    "characters": [{"name": "a", "style_pack": "stick_figure_v1", "role": "lead",
                    "description": "red shirt"}],
    "backgrounds": [{"name": "bg", "description": "a plain room", "tags": ["indoor"]}],
}


def test_character_style_mismatch_rejected(tmp_path):
    bad = json.loads(json.dumps(BASE))
    bad["characters"][0]["style_pack"] = "mascot_animal_v1"
    with pytest.raises(config.ConfigError, match="style_pack"):
        config.load_project(_write(tmp_path, bad))


def test_untagged_background_rejected(tmp_path):
    bad = json.loads(json.dumps(BASE))
    bad["backgrounds"][0]["tags"] = []
    with pytest.raises(config.ConfigError):
        config.load_project(_write(tmp_path, bad))


def test_missing_script_is_warning_not_error(tmp_path):
    ok = json.loads(json.dumps(BASE))
    ok.pop("script")
    p = config.load_project(_write(tmp_path, ok))
    assert any("no script" in w for w in p.warnings)


def test_unknown_style_pack_errors(tmp_path):
    bad = json.loads(json.dumps(BASE))
    bad["style_pack"] = "does_not_exist"
    bad["characters"][0]["style_pack"] = "does_not_exist"
    with pytest.raises(config.ConfigError, match="not found"):
        config.load_project(_write(tmp_path, bad))
