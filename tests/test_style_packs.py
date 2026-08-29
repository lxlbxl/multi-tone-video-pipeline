import pytest

from pipeline import style_packs, util

SP = util.read_json(util.REPO_ROOT / "style_packs" / "stick_figure_v1.json")


def test_prompt_has_prefix_and_negatives():
    p = style_packs.build_prompt(SP, "a person waves at a phone", kind="shot")
    assert SP["render_prefix"].split(",")[0] in p
    assert "do not include" in p.lower()
    assert p.endswith(".")


def test_character_ref_adds_pose():
    p = style_packs.build_prompt(SP, "green hoodie", kind="character_ref")
    assert "front three-quarter view" in p


def test_background_adds_suffix():
    p = style_packs.build_prompt(SP, "downtown sidewalk", kind="background")
    assert "no characters" in p


def test_ip_blocklist_blocks_named_characters():
    with pytest.raises(style_packs.ForbiddenContentError):
        style_packs.build_prompt(SP, "Batman fights crime downtown", kind="shot")


def test_ip_blocklist_case_insensitive():
    with pytest.raises(style_packs.ForbiddenContentError):
        style_packs.build_prompt(SP, "a PIKACHU on a skateboard", kind="shot")


def test_clean_instruction_passes():
    style_packs.build_prompt(SP, "an original cartoon fox in a hoodie", kind="shot")
