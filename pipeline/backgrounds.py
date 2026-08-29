"""
(4) backgrounds.py — one image per background library entry, generated once,
tagged, reused across shots (and across projects when `shared: true`).

`select()` lets the shot-list step ask for "an outdoor neutral background" and
get an existing match instead of generating a new one every time.
"""
from __future__ import annotations

from pathlib import Path

from . import kie, style_packs, util


def _img_path(bg: dict, project_name: str) -> Path:
    rel = bg.get("image") or f"backgrounds/{project_name}/{bg['name']}.png"
    return util.resolve_asset(rel)


def ensure_background(bg: dict, style_pack: dict, project_name: str, *,
                      aspect: str = "9:16", resolution: str = "1K",
                      force: bool = False) -> Path:
    dest = _img_path(bg, project_name)
    if dest.exists() and not force:
        util.log(f"background '{bg['name']}': cached ({dest.name})")
        return dest
    prompt = style_packs.build_prompt(style_pack, bg["description"], kind="background")
    util.log(f"background '{bg['name']}': generating")
    kie.generate("gpt_image_2", dest=dest, prompt=prompt,
                 aspect_ratio=aspect, resolution=resolution, timeout=600)
    util.write_json(dest.with_suffix(".json"),
                    {**{k: bg[k] for k in ("name", "description", "tags") if k in bg},
                     "project": project_name, "prompt": prompt})
    util.log(f"background '{bg['name']}': ready -> {dest.name}", level="ok")
    return dest


def ensure_all(backgrounds: list[dict], style_pack: dict, project_name: str,
               **kw) -> dict[str, Path]:
    return {b["name"]: ensure_background(b, style_pack, project_name, **kw)
            for b in backgrounds}


def select(backgrounds: list[dict], query_tags: list[str]) -> dict | None:
    """Best tag-overlap match. Exact superset wins; otherwise highest overlap;
    None only if the library is empty."""
    if not backgrounds:
        return None
    q = {t.lower() for t in query_tags}
    if not q:
        return backgrounds[0]
    scored = []
    for b in backgrounds:
        tags = {t.lower() for t in b.get("tags", [])}
        scored.append((len(q & tags) + (10 if q <= tags else 0), b))
    scored.sort(key=lambda s: s[0], reverse=True)
    return scored[0][1] if scored[0][0] > 0 else backgrounds[0]
