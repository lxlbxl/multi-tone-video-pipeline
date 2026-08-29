"""
(3) characters.py — one reference image per character bible entry, generated
once, locked on disk, and reused for every shot. Never regenerated mid-project
(pass force=True to deliberately rebuild one).

Supports N characters per project; each is generated independently but always
through the project's style pack, so they visually belong together.
"""
from __future__ import annotations

from pathlib import Path

from . import kie, style_packs, util


def _ref_path(character: dict, style_id: str) -> Path:
    rel = character.get("reference_image") or f"characters/{style_id}/{character['name']}_ref.png"
    return util.resolve_asset(rel)


def instruction_for(character: dict) -> str:
    bits = [character["description"].strip().rstrip(".")]
    if character.get("role"):
        bits.append(f"role: {character['role'].strip().rstrip('.')}")
    if character.get("prompt_extra"):
        bits.append(character["prompt_extra"].strip().rstrip("."))
    return ". ".join(bits)


def ensure_reference(character: dict, style_pack: dict, *, aspect: str = "9:16",
                     resolution: str = "1K", force: bool = False) -> Path:
    style_id = style_pack["id"]
    dest = _ref_path(character, style_id)
    if dest.exists() and not force:
        util.log(f"character '{character['name']}': ref locked ({dest.name})")
        return dest

    prompt = style_packs.build_prompt(style_pack, instruction_for(character),
                                      kind="character_ref")
    util.log(f"character '{character['name']}': generating reference")
    kie.generate("gpt_image_2", dest=dest, prompt=prompt,
                 aspect_ratio=aspect, resolution=resolution, timeout=600)
    try:
        rel = str(dest.relative_to(util.asset_root()))
    except ValueError:
        rel = str(dest)
    util.write_json(dest.with_suffix(".json"), {
        "name": character["name"],
        "style_pack": style_id,
        "prompt": prompt,
        "reference_image": rel,
    })
    util.log(f"character '{character['name']}': locked -> {dest.name}", level="ok")
    return dest


def ensure_all(characters: list[dict], style_pack: dict, **kw) -> dict[str, Path]:
    return {c["name"]: ensure_reference(c, style_pack, **kw) for c in characters}
