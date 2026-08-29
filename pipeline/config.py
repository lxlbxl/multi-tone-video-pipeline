"""
(1) config.py — load project.json, resolve every reference, validate.

A project points at one style pack, one tone profile, one narrative template,
1..N characters and 0..N backgrounds, plus (optionally) a script. This module
turns that into a fully-resolved `Project` object and refuses to continue if
anything is inconsistent:

  * every character belongs to the project's declared style pack
  * every background carries at least one tag
  * the tone profile and narrative template exist and validate
  * the script path (if given) exists

Library docs are looked up in this order:
  projects/<name>/<kind>/<id>.json   (project-local override)
  <repo_root>/<kind>/<id>.json       (shared library)
  $MTVP_LIB_DIR/<kind>/<id>.json     (extra search dir, optional)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from . import util

SCHEMA_DIR = util.REPO_ROOT / "schemas"


# --------------------------------------------------------------------------- #
# schema helpers
# --------------------------------------------------------------------------- #
_SCHEMA_CACHE: dict[str, dict] = {}


def _schema(name: str) -> dict:
    if name not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[name] = util.read_json(SCHEMA_DIR / f"{name}.schema.json")
    return _SCHEMA_CACHE[name]


def validate(doc: Any, schema_name: str, *, where: str) -> None:
    try:
        jsonschema.validate(doc, _schema(schema_name))
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "(root)"
        raise ConfigError(f"{where}: schema violation at {path}: {e.message}") from None


class ConfigError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# resolved project
# --------------------------------------------------------------------------- #
@dataclass
class Project:
    name: str
    root: Path                      # projects/<name>/
    raw: dict
    style_pack: dict
    tone_profile: dict
    narrative_template: dict
    characters: list[dict]
    backgrounds: list[dict]
    script_path: Path | None
    aspect: str = "9:16"
    resolution: str = "1K"
    seed: int = 7
    target_seconds: float = 30.0
    brief: str = ""
    cta: str = ""
    disclaimer_text: str = ""
    warnings: list[str] = field(default_factory=list)

    # convenient derived dirs -------------------------------------------------
    @property
    def work_dir(self) -> Path:
        return self.root / "work"

    @property
    def shots_dir(self) -> Path:
        return self.root / "shots"

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    def character(self, name: str) -> dict | None:
        return next((c for c in self.characters if c["name"] == name), None)

    def background(self, name: str) -> dict | None:
        return next((b for b in self.backgrounds if b["name"] == name), None)


# --------------------------------------------------------------------------- #
# lookup
# --------------------------------------------------------------------------- #
def _search_dirs(project_root: Path, kind: str) -> list[Path]:
    dirs = [project_root / kind, util.REPO_ROOT / kind]
    extra = os.environ.get("MTVP_LIB_DIR")
    if extra:
        dirs.append(Path(extra) / kind)
    return dirs


def _load_library(project_root: Path, kind: str, ident: str, schema_name: str) -> dict:
    for d in _search_dirs(project_root, kind):
        p = d / f"{ident}.json"
        if p.exists():
            doc = util.read_json(p)
            validate(doc, schema_name, where=str(p))
            return doc
    searched = ", ".join(str(d) for d in _search_dirs(project_root, kind))
    raise ConfigError(f"{kind}/{ident}.json not found (searched: {searched})")


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def load_project(project_json: str | Path) -> Project:
    pj = Path(project_json).resolve()
    if not pj.exists():
        raise ConfigError(f"project file not found: {pj}")
    root = pj.parent
    raw = util.read_json(pj)
    validate(raw, "project", where=str(pj))

    warnings: list[str] = []
    style_id = raw["style_pack"]
    style_pack = _load_library(root, "style_packs", style_id, "style_pack")

    # tone + narrative template ------------------------------------------------
    tone = _load_library(root, "tone_profiles", raw["tone_profile"], "tone_profile")
    nt_id = raw.get("narrative_template") or tone["narrative_template"]
    narrative_template = _load_library(root, "narrative_templates", nt_id, "narrative_template")

    # characters ------------------------------------------------------------
    characters: list[dict] = []
    for entry in raw["characters"]:
        if isinstance(entry, str):
            ch = _load_library(root, f"characters/{style_id}", entry, "character")
        else:
            ch = dict(entry)
            ch.setdefault("style_pack", style_id)
            validate(ch, "character", where=f"{pj} characters[{entry.get('name','?')}]")
        if ch["style_pack"] != style_id:
            raise ConfigError(
                f"character '{ch['name']}' declares style_pack "
                f"'{ch['style_pack']}' but the project uses '{style_id}' — "
                "every character must be built inside the project's style pack"
            )
        ch.setdefault(
            "reference_image",
            f"characters/{style_id}/{ch['name']}_ref.png",
        )
        characters.append(ch)

    names = [c["name"] for c in characters]
    if len(names) != len(set(names)):
        raise ConfigError(f"duplicate character names: {names}")

    # backgrounds ---------------------------------------------------------
    backgrounds: list[dict] = []
    for entry in raw.get("backgrounds", []):
        if isinstance(entry, str):
            bg = _load_library(root, f"backgrounds/{raw['name']}", entry, "background")
        else:
            bg = dict(entry)
            bg.setdefault("project", raw["name"])
            validate(bg, "background", where=f"{pj} backgrounds[{entry.get('name','?')}]")
        if not bg.get("tags"):
            raise ConfigError(f"background '{bg['name']}' has no tags — the shot-list "
                              "generator selects backgrounds by tag, so every one must be tagged")
        bg.setdefault("image", f"backgrounds/{raw['name']}/{bg['name']}.png")
        backgrounds.append(bg)

    if not backgrounds:
        warnings.append("no backgrounds declared — shots will be generated on a plain "
                        "style-pack backdrop only")

    # script --------------------------------------------------------------
    script_path: Path | None = None
    if raw.get("script"):
        sp = (root / raw["script"]).resolve()
        if not sp.exists():
            raise ConfigError(f"script not found: {sp}")
        script_path = sp
    else:
        warnings.append("no script supplied — draft one with the prompt in "
                        "references/prompt_templates.md and save it, then re-run")

    for w in warnings:
        util.log(w, level="warn")

    return Project(
        name=raw["name"],
        root=root,
        raw=raw,
        style_pack=style_pack,
        tone_profile=tone,
        narrative_template=narrative_template,
        characters=characters,
        backgrounds=backgrounds,
        script_path=script_path,
        aspect=raw.get("aspect", "9:16"),
        resolution=raw.get("resolution", "1K"),
        seed=int(raw.get("seed", 7)),
        target_seconds=float(raw.get("target_seconds", 30.0)),
        brief=raw.get("brief", ""),
        cta=raw.get("cta", ""),
        disclaimer_text=raw.get("disclaimer_text") or tone.get("disclaimer_text", ""),
        warnings=warnings,
    )


def summarize(p: Project) -> str:
    lines = [
        f"project        {p.name}",
        f"brief          {p.brief or '—'}",
        f"style pack     {p.style_pack['id']}  ({p.style_pack.get('line_weight','?')} line)",
        f"tone profile   {p.tone_profile['id']}  wpm={p.tone_profile['pacing_wpm']} "
        f"motion={p.tone_profile['motion_intensity']} "
        f"disclaimer={'yes' if p.tone_profile['disclaimers_required'] else 'no'}",
        f"narrative      {p.narrative_template['id']}  "
        f"({len(p.narrative_template['beats'])} beats)",
        f"characters     {', '.join(c['name'] for c in p.characters)}",
        f"backgrounds    {', '.join(b['name'] for b in p.backgrounds) or '—'}",
        f"script         {p.script_path.name if p.script_path else '(to be drafted)'}",
        f"format         {p.aspect} @ {p.resolution}, seed {p.seed}",
    ]
    return "\n".join(lines)
