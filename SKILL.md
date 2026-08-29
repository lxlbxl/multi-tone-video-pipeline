---
name: multi-tone-video-pipeline
description: >
  Config-driven script-to-video pipeline. One engine produces a serious B2B
  explainer for one venture and a playful consumer short for another — the only
  things that change are JSON files (style pack, tone profile, narrative
  template, project). NO video-generation model: every shot is a still from GPT
  Image 2 (reference-conditioned for character + environment consistency),
  animated procedurally with FFmpeg (Ken Burns / parallax / pose-crossfade),
  over an ElevenLabs voice-over with kinetic captions. ALWAYS use this skill
  when the user wants a narrated explainer, promo, myth-bust, before/after, or
  listicle short built from stills rather than generated video — or wants one
  reusable pipeline across multiple brands/tones. Handles config → script →
  VO → shot list → reference images → animation → captions → final 9:16 MP4.
---

# Multi-Style, Multi-Tone Script-to-Video Pipeline

Turn a brief into a finished vertical video by loading a **project config**
instead of hardcoding a character or a voice. Change the style pack and tone
profile, keep the pipeline untouched, get a completely different-feeling video
from the same engine.

## The four things that stay separate

| Thing | What it fixes | File |
|---|---|---|
| **Style pack** | *how* anything is drawn (line weight, palette, forbidden list) — never *who* | `style_packs/<id>.json` |
| **Character bible** | the actual characters, each built inside one style pack, each with a locked reference image | project `characters[]` or `characters/<style_pack>/<name>.json` |
| **Background library** | reusable tagged environments, generated once | project `backgrounds[]` or `backgrounds/<project>/<name>.json` |
| **Tone/brand profile** | serious vs playful: voice, pacing, caption style, motion intensity, disclaimer flag, narrative template | `tone_profiles/<id>.json` |

`projects/<name>/project.json` points at one of each plus the script. See
[references/config_authoring.md](references/config_authoring.md) for every field.

## Prerequisites

```bash
python -m pip install -r requirements.txt      # jsonschema, Pillow, pytest
npm install -g kie-cli                          # GPT Image 2 + ElevenLabs TTS
export KIE_API_KEY="..."                         # https://kie.ai/api-key
ffmpeg -version                                  # 6+ with libass (bundled in gyan builds)
python scripts/preflight.py                      # verify all of the above
```

Optional: `pip install faster-whisper` for tighter caption sync (the pipeline
falls back to Gemini, then to proportional estimation, without it).

## Pipeline stages

```
validate → script → tts → align → refs → backgrounds → shotlist → shots → animate → render
```

Driver:

```bash
python -m pipeline --project projects/<name>/project.json          # full run
python -m pipeline --project projects/<name>/project.json --dry-run # plan + credit estimate
python -m pipeline --project projects/<name>/project.json --from animate
python -m pipeline --project projects/<name>/project.json --stage shots
```

`script` and `shotlist` are **checkpoints**: the CLI stops so you (or Claude) do
the creative pass, then you re-run. `--auto` renders straight from the
scaffold; `--yes` skips confirmations.

## Workflow (what Claude does at each step)

### 1. Author or pick the project config
Copy `projects/example_playful_app/` or `projects/example_finance/` and edit.
Run `python -m pipeline --project … --dry-run` — it prints the resolved config,
the stage list, and a Kie credit estimate. Fix any config error it reports
before spending credits.

### 2. Draft the script (checkpoint)
If `project.json` has no `script`, the CLI writes `<name>_PROMPT.txt` with the
tone's voice, the target word count, and the narrative template's beats. Write
the script (spoken words only), save it where the prompt says, re-run.
Hook rules per template are in `narrative_templates/*.json` and
[references/viral_playbook.md](references/viral_playbook.md) — **the first
sentence is the whole ballgame.**

### 3. TTS + alignment (automatic)
`tts` synthesizes the VO with the tone's voice/pacing. `align` produces word
timings (`work/words.json`).

### 4. Lock character references (one-time)
`refs` generates one reference image per character, through the style pack, and
**locks it on disk**. Never regenerated unless you pass `--force-refs`. Review
`characters/<style_pack>/*_ref.png` — every shot inherits these faces.

### 5. Backgrounds (one-time, tagged)
`backgrounds` generates each library entry. Tagged so the shot list can request
"an outdoor neutral background" and get a match.

### 6. Fill the shot list (checkpoint)
`shotlist` writes a **scaffold** to `projects/<name>/shots/shot_list.json`:
beats laid across the VO timeline, honouring `shot_hold_seconds_min`. Fill in:
- `composition` — who is in frame, where, doing what, camera framing
- `characters` — which bible entries appear (≤3 for reliable gen)
- `background` — a library name, or `"auto"` + `background_query` tags
- `motion.type` — `ken_burns` / `parallax` / `pose_crossfade` (+ `pose_b`) / `hold`
- `captions` — already sliced from the VO; tighten wording, mark `emphasis`

Use the shot-list prompt in
[references/prompt_templates.md](references/prompt_templates.md). Re-run
`--stage shotlist` to re-validate (it hard-fails on fast cuts, unknown
characters, caption overflow, timeline overrun).

### 7. Generate, animate, render
`shots` does reference-conditioned generation (uploads refs → GPT Image 2
image-to-image, style prefix always prepended). `animate` applies motion scaled
by the tone. `render` concatenates, burns captions, mixes VO (+ optional Suno
music bed, ducked, −14 LUFS), and appends a disclaimer end-card if the tone
requires one. Output: `projects/<name>/output/<name>_final.mp4` + a manifest.

## Hard rules

- **`--dry-run` first, every time.** Confirm the resolved config and credit
  estimate before generating anything.
- **Character references are locked.** One reference per character, reused on
  every shot and every future video in the same campaign. `--force-refs` is a
  deliberate reset, not a retry.
- **The style pack's `render_prefix` is prepended to every generation** — refs,
  backgrounds, and shots — so the whole project shares one visual language.
- **Never name copyrighted characters or real people** in a composition line.
  `style_packs.check_instruction` blocks known IP; keep descriptions original.
- **Respect `shot_hold_seconds_min`.** A serious video holds; a playful one
  cuts faster. The validator enforces it.
- **Everything that varies between a serious and a playful video lives in
  JSON** — `project.json`, `style_packs/*.json`, `tone_profiles/*.json`. Never
  edit `pipeline/*.py` to change a look.

## Reference docs

- [config_authoring.md](references/config_authoring.md) — every schema field, how to add a style pack / tone / template
- [prompt_templates.md](references/prompt_templates.md) — script-draft and shot-list prompts for the creative passes
- [viral_playbook.md](references/viral_playbook.md) — hook, retention, caption pacing, sound-on, loopability
- [motion_and_captions.md](references/motion_and_captions.md) — how motion_intensity maps to FFmpeg, ASS caption styling
- [troubleshooting.md](references/troubleshooting.md) — kie-cli drift, upload failures, ffmpeg concat, alignment

## Module map (`pipeline/`)

`config` · `style_packs` · `characters` · `backgrounds` · `tone` · `narrative`
· `imagegen` · `animate` · `captions` · `render` · `cli`  — plus `kie`
(kie-cli + upload wrapper), `tts`, `align`, `music`, `util`.
