"""
(2) style_packs.py — turn a style pack + a specific instruction into a full
generation prompt, and enforce the forbidden list.

`render_prefix` is prepended to *every* character reference and *every*
reference-conditioned shot edit, so the whole project shares one visual system
— not just successive shots of one character.
"""
from __future__ import annotations

import re

# Named IP that must never appear in a generation instruction, regardless of
# what a style pack lists. The style pack's own `forbidden` array is checked on
# top of this.
_IP_BLOCKLIST = [
    "mickey mouse", "minnie mouse", "disney", "pixar", "marvel", "dc comics",
    "batman", "superman", "spider-man", "spiderman", "iron man", "elsa",
    "pokemon", "pikachu", "nintendo", "mario", "sonic", "hello kitty",
    "star wars", "darth vader", "harry potter", "simpsons", "peppa pig",
    "bluey", "minions", "shrek", "sesame street", "looney tunes", "pjmask",
    "paw patrol", "spongebob", "naruto", "goku", "dragon ball",
]


class ForbiddenContentError(RuntimeError):
    pass


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower())


def check_instruction(instruction: str, style_pack: dict) -> None:
    """Raise ForbiddenContentError if the instruction names blocked content."""
    text = _norm(instruction)
    hits = [name for name in _IP_BLOCKLIST if name in text]
    for term in style_pack.get("forbidden", []):
        t = _norm(term)
        # skip the generic policy phrases — they are guidance for the model,
        # not literal strings we expect to see in an instruction
        if t in ("copyrighted characters", "realistic faces", "photographic textures",
                 "brand logos", "watermarks", "in-image text", "text labels in the image",
                 "competitor logos", "any existing studio mascot's proportions or markings"):
            continue
        if t and t in text:
            hits.append(term)
    if hits:
        raise ForbiddenContentError(
            f"instruction references forbidden content: {sorted(set(hits))}"
        )


def negatives(style_pack: dict) -> str:
    """The 'do not include' clause, from the style pack's forbidden list."""
    return ", ".join(style_pack.get("forbidden", [])) or "photographic textures, brand logos, text"


def build_prompt(style_pack: dict, instruction: str, *, kind: str = "shot",
                 palette_hint: bool = True) -> str:
    """
    kind: "character_ref" | "background" | "shot"
    """
    check_instruction(instruction, style_pack)
    parts = [style_pack["render_prefix"].rstrip(". "), instruction.strip().rstrip(". ")]

    if kind == "character_ref" and style_pack.get("reference_pose"):
        parts.append(style_pack["reference_pose"].rstrip(". "))
    if kind == "background" and style_pack.get("background_suffix"):
        parts.append(style_pack["background_suffix"].rstrip(". "))

    if palette_hint and style_pack.get("palette"):
        pal = ", ".join(c if c.startswith("#") else f"#{c}" for c in style_pack["palette"])
        parts.append(f"colour palette limited to {pal}")

    parts.append(f"do not include: {negatives(style_pack)}")
    return ". ".join(p for p in parts if p) + "."


def palette(style_pack: dict) -> list[str]:
    return [c if c.startswith("#") else f"#{c}" for c in style_pack.get("palette", [])]
