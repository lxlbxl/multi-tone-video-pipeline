"""
(7) imagegen.py — reference-conditioned shot generation.

For each shot: upload the background image + each present character's locked
reference to public URLs, then call GPT Image 2 image-to-image with the style
pack's render_prefix + the shot's composition line. The references keep the
characters and environment consistent; the prefix keeps the whole project in
one visual language.

pose_crossfade shots produce two stills (a / b).
"""
from __future__ import annotations

from pathlib import Path

from . import backgrounds as bg_mod
from . import characters as ch_mod
from . import config, kie, style_packs, util

_REF_CONSISTENCY = ("Match every provided character reference exactly — same face, "
                    "hair, outfit, colours, proportions. Match the provided environment "
                    "reference for the setting. Single coherent illustration.")


def _upload_refs(shot: dict, project: "config.Project") -> list[str]:
    urls: list[str] = []
    # background first so it reads as the base layer
    bg_name = shot["background"]
    if bg_name == "auto":
        picked = bg_mod.select(project.backgrounds, shot.get("background_query", []))
        bg_name = picked["name"] if picked else None
    if bg_name:
        bg = project.background(bg_name)
        if bg:
            p = util.resolve_asset(bg["image"])
            if p.exists():
                urls.append(kie.upload(p, subdir=f"mtvp/{project.name}/bg"))
    for cname in shot["characters"]:
        ch = project.character(cname)
        if not ch:
            continue
        rp = util.resolve_asset(ch["reference_image"])
        if rp.exists():
            urls.append(kie.upload(rp, subdir=f"mtvp/{project.name}/char"))
    return urls


def _prompt(shot: dict, project: "config.Project", *, variant: str | None = None) -> str:
    comp = shot["composition"]
    if variant == "b" and shot["motion"].get("pose_b"):
        comp = shot["motion"]["pose_b"]
    present = ", ".join(shot["characters"]) or "no characters"
    instruction = f"{comp}. Characters present: {present}. {_REF_CONSISTENCY}"
    return style_packs.build_prompt(project.style_pack, instruction, kind="shot")


def generate_shot(shot: dict, project: "config.Project", *, force: bool = False) -> list[Path]:
    project.shots_dir.mkdir(parents=True, exist_ok=True)
    variants = ["a", "b"] if shot["motion"]["type"] == "pose_crossfade" else [None]
    refs = None
    out: list[Path] = []
    for v in variants:
        suffix = f"_{v}" if v else ""
        dest = project.shots_dir / f"{shot['shot_id']}{suffix}.png"
        if dest.exists() and not force:
            util.log(f"{shot['shot_id']}{suffix}: cached")
            out.append(dest)
            continue
        if refs is None:
            refs = _upload_refs(shot, project)
        prompt = _prompt(shot, project, variant=v)
        util.log(f"{shot['shot_id']}{suffix}: generating ({len(refs)} refs)")
        kie.generate("gpt_image_2", dest=dest, prompt=prompt,
                     input_urls=refs or None,
                     aspect_ratio=project.aspect, resolution=project.resolution,
                     timeout=600)
        util.write_json(dest.with_suffix(".json"),
                        {"shot_id": shot["shot_id"], "variant": v, "prompt": prompt,
                         "refs": refs})
        out.append(dest)
    return out


def generate_all(shot_list: dict, project: "config.Project", *, force: bool = False) -> dict:
    made: dict[str, list[str]] = {}
    for shot in shot_list["shots"]:
        paths = generate_shot(shot, project, force=force)
        made[shot["shot_id"]] = [str(p) for p in paths]
    util.log(f"imagegen: {len(made)} shots ready", level="ok")
    return made
