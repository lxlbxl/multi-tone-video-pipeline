"""
(11) cli.py — run the pipeline against a project config.

    python -m pipeline --project projects/<name>/project.json
    python -m pipeline --project … --stage shots        # one stage
    python -m pipeline --project … --from animate        # this stage onward
    python -m pipeline --project … --dry-run             # plan only, no API calls

Stages, in order:
    validate  script  tts  align  refs  backgrounds  shotlist  shots
    animate   render

`script` and `shotlist` are checkpoints: if the artifact is missing the CLI
writes a scaffold / prints the drafting prompt and stops so a human (or Claude)
can do the creative pass, unless --auto is given.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import align, animate, backgrounds, captions, characters, config
from . import imagegen, narrative, render, tts, util
from .tone import Tone, load as load_tone

STAGES = ["validate", "script", "tts", "align", "refs", "backgrounds",
          "shotlist", "shots", "animate", "render"]

# rough credit cost per Kie call (order-of-magnitude, for the pre-flight prompt)
_COST = {"image_1k": 12, "image_2k": 18, "tts": 6, "music": 30}


def _artifacts(p: "config.Project") -> dict[str, Path]:
    w = p.work_dir
    return {
        "script": (p.script_path or p.root / "scripts" / f"{p.name}.txt"),
        "vo": w / "vo.wav",
        "words": w / "words.json",
        "shotlist": p.shots_dir / "shot_list.json",
        "final": p.output_dir / f"{p.name}_final.mp4",
    }


def _estimate(p: "config.Project", sl: dict | None) -> int:
    img = "image_2k" if p.resolution == "2K" else "image_1k"
    n = len(p.characters) + len(p.backgrounds)
    if sl:
        n += sum(2 if s["motion"]["type"] == "pose_crossfade" else 1 for s in sl["shots"])
    else:
        n += 6
    total = n * _COST[img] + _COST["tts"]
    if p.tone_profile.get("music", {}).get("enabled"):
        total += _COST["music"]
    return total


def _confirm(msg: str, yes: bool) -> None:
    if yes:
        return
    if not sys.stdin.isatty():
        util.die(f"{msg}\nRe-run with --yes to proceed non-interactively.")
    if input(f"{msg}\nProceed? [y/N] ").strip().lower() not in ("y", "yes"):
        raise SystemExit("aborted")


def run(args: argparse.Namespace) -> int:
    proj = config.load_project(args.project)
    tone: Tone = load_tone(proj.tone_profile)
    art = _artifacts(proj)
    for d in (proj.work_dir, proj.shots_dir, proj.output_dir):
        d.mkdir(parents=True, exist_ok=True)

    if args.stage:
        todo = [args.stage]
    else:
        start = args.from_stage or "validate"
        todo = STAGES[STAGES.index(start):]

    print(config.summarize(proj))
    print(f"\nstages: {' -> '.join(todo)}")

    # ---- validate --------------------------------------------------------
    if "validate" in todo:
        util.log("validate: project config OK", level="ok")

    # ---- script ---------------------------------------------------------
    script_path = proj.script_path or art["script"]
    if "script" in todo:
        if script_path.exists():
            util.log(f"script: using {script_path}")
        elif args.dry_run:
            util.log("script: (dry-run) would need a script here", level="warn")
        else:
            _write_script_prompt(proj, tone, script_path)
            util.die(f"No script yet. A drafting prompt was written next to "
                     f"{script_path.name}. Draft the script, save it as "
                     f"{script_path}, then re-run.", code=2)
    script_text = _clean_script(util.read_text(script_path)) if script_path.exists() else ""

    if args.dry_run:
        est = _estimate(proj, _load_sl(art["shotlist"]))
        print(f"\n[dry-run] estimated Kie cost ~ {est} credits. No calls made.")
        return 0

    # ---- tts ----------------------------------------------------------
    if "tts" in todo and (not art["vo"].exists() or args.force):
        _confirm(f"TTS: synthesize {len(script_text.split())} words "
                 f"(~{_COST['tts']} credits).", args.yes)
        tts.synthesize(script_text, tone, out_wav=art["vo"], work_dir=proj.work_dir)

    # ---- align ------------------------------------------------------
    if "align" in todo and (not art["words"].exists() or args.force):
        words = align.align_words(art["vo"], script_text, method=args.align_method)
        util.write_json(art["words"], {"audio_duration": util.probe_duration(art["vo"]),
                                       "words": words})
        util.log(f"align: {len(words)} words", level="ok")
    words_doc = util.read_json(art["words"]) if art["words"].exists() else {"words": [], "audio_duration": 0.0}
    audio_dur = words_doc.get("audio_duration") or util.probe_duration(art["vo"]) if art["vo"].exists() else 0.0

    # ---- refs -------------------------------------------------------
    if "refs" in todo:
        _confirm(f"Character refs: generate/lock {len(proj.characters)} images.", args.yes)
        characters.ensure_all(proj.characters, proj.style_pack, aspect=proj.aspect,
                              resolution=proj.resolution, force=args.force_refs)

    # ---- backgrounds ----------------------------------------------
    if "backgrounds" in todo and proj.backgrounds:
        _confirm(f"Backgrounds: generate {len(proj.backgrounds)} images.", args.yes)
        backgrounds.ensure_all(proj.backgrounds, proj.style_pack, proj.name,
                               aspect=proj.aspect, resolution=proj.resolution,
                               force=args.force)

    # ---- shotlist ------------------------------------------------
    if "shotlist" in todo:
        if art["shotlist"].exists() and not args.force:
            sl = _load_sl(art["shotlist"])
            narrative.validate(sl, proj, tone, audio_duration=audio_dur)
            util.log("shotlist: existing shot_list.json is valid", level="ok")
        else:
            sl = narrative.scaffold(proj, tone, words_doc["words"], audio_dur or proj.target_seconds)
            util.write_json(art["shotlist"], sl)
            narrative.validate(sl, proj, tone, audio_duration=audio_dur, strict=False)
            if not args.auto:
                util.die(f"shotlist: wrote a SCAFFOLD to {art['shotlist']}. Fill in the "
                         f"composition lines (and pose_b for any pose_crossfade), then "
                         f"re-run. Use --auto to render straight from the scaffold.", code=2)
    needs_sl = any(s in todo for s in ("shots", "animate", "render"))
    sl = _load_sl(art["shotlist"])
    if needs_sl and sl is None:
        util.die("no shot_list.json — run the shotlist stage first")

    # ---- shots (imagegen) --------------------------------------
    if "shots" in todo:
        narrative.validate(sl, proj, tone, audio_duration=audio_dur)
        _confirm(f"Shots: generate images for {len(sl['shots'])} shots "
                 f"(~ {_estimate(proj, sl)} credits total).", args.yes)
        shot_images = imagegen.generate_all(sl, proj, force=args.force)
        util.write_json(proj.work_dir / "shot_images.json", shot_images)
    shot_images = util.read_json(proj.work_dir / "shot_images.json") \
        if (proj.work_dir / "shot_images.json").exists() else {}

    # ---- animate ---------------------------------------------
    if "animate" in todo:
        if not shot_images:
            util.die("no shot images — run the shots stage first")
        clips = animate.animate_all(sl, shot_images, tone,
                                    work_dir=proj.work_dir / "anim",
                                    out_dir=proj.work_dir / "clips")
        util.write_json(proj.work_dir / "clips.json", [str(c) for c in clips])
    clips = [Path(c) for c in util.read_json(proj.work_dir / "clips.json")] \
        if (proj.work_dir / "clips.json").exists() else []

    # ---- render --------------------------------------------
    if "render" in todo:
        if not clips:
            util.die("no animated clips — run the animate stage first")
        out = render.render(proj, tone, animated_clips=clips, shot_list=sl,
                            vo_wav=art["vo"])
        print(f"\nOK  {out}")
    return 0


def _load_sl(path: Path):
    return util.read_json(path) if Path(path).exists() else None


def _clean_script(raw: str) -> str:
    """Drop leading '#' comment lines (e.g. the '# motivation:' line the draft
    prompt asks for) and surrounding blank lines; keep the spoken text."""
    lines = raw.splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    return "\n".join(lines).strip() + "\n"


def _write_script_prompt(proj: "config.Project", tone: Tone, script_path: Path) -> None:
    nt = proj.narrative_template
    n_words = int(proj.target_seconds / 60 * tone.pacing_wpm)
    beats = "\n".join(f"  {i+1}. {b['id']}: {b['purpose']}"
                      for i, b in enumerate(nt["beats"]))
    disc = ("Every claim must be defensible; include a spoken disclaimer or leave "
            "room for the end-card." if tone.disclaimers_required
            else "No disclaimer needed.")
    txt = f"""SCRIPT DRAFTING PROMPT - {proj.name}
Save the finished script as:  {script_path.name}
(See references/scriptcraft.md for the full method this prompt operationalises.)

Brief:            {proj.brief or '(none given)'}
Voice / tone:     {tone.voice_style}
Length:           EXACTLY ~{n_words} words  ({tone.pacing_wpm} wpm x {proj.target_seconds:.0f}s).
                  Running long is the #1 failure. Cut beats, never the lens or the last line.
Narrative:        {nt['id']}
Hook rule:        {nt.get('hook_rules', '')}
Hook formula:     {nt.get('hook_formula', 'pattern_interrupt_question')} (scriptcraft.md section 7)
Connector rule:   {nt.get('connector_rule', "BUT / THEREFORE between every beat - never 'and then'.")}
Last line:        {nt.get('last_dab', 'A shareable one-liner that loops back into the hook on replay.')}

Beats, in order (put a BUT or THEREFORE between each):
{beats}

Method (do in order):
 1. LENS - pick the ONE non-obvious angle on this brief before writing. Not
    "struggled then succeeded". Invert the villain / find the asset in the
    failure / jump to the second-order effect.
 2. ENDS FIRST - write the last line (the "last dab") and a working first line;
    leave the middle blank.
 3. DANCE - fill the beats; BUT/THEREFORE between each; kill every "and then";
    >= 2 open loops in the first 30s.
 4. RHYTHM - one sentence per line; vary lengths (short, short, long); jagged
    left edge; read aloud.
 5. TONE - rewrite anything that sounds like a speech into something said to one
    friend; match the voice/tone above.
 6. HOOK - finalise line 1 with the hook formula; punchy, plot-indicative; no
    "in this video", no greeting, no "wait till you see this".
 7. LENGTH - trim to ~{n_words} words.

Hard rules:
- Real material only. Never invent numbers, events, or biography.
- {disc}
- Spoken words only - no stage directions, scene labels, or emojis.
- End on ONE takeaway / CTA{': ' + proj.cta if proj.cta else '.'}
- First line of the file: "# motivation: <identity|utility|emotion|tribe|status|
  validation>" - the target reason someone would share this. Script below it.

Output: the "# motivation:" line, then the script. Nothing else.
"""
    p = script_path.with_name(script_path.stem + "_PROMPT.txt")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")
    util.log(f"wrote drafting prompt -> {p}", level="warn")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser("pipeline", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, help="path to projects/<name>/project.json")
    ap.add_argument("--stage", choices=STAGES, help="run exactly one stage")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, help="run from this stage onward")
    ap.add_argument("--dry-run", action="store_true", help="plan + cost estimate, no API calls")
    ap.add_argument("--auto", action="store_true",
                    help="don't stop at the shotlist checkpoint — render from the scaffold")
    ap.add_argument("--yes", "-y", action="store_true", help="skip all confirmations")
    ap.add_argument("--force", action="store_true", help="regenerate stage artifacts even if present")
    ap.add_argument("--force-refs", action="store_true", help="rebuild locked character references")
    ap.add_argument("--align-method", default="auto",
                    choices=["auto", "whisper", "gemini", "proportional"])
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except (config.ConfigError, narrative.ShotListError) as e:
        util.die(str(e))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
