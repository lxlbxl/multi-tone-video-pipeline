# multi-tone-video-pipeline

A config-driven script-to-video pipeline and Claude Code skill. **One engine
produces a serious B2B explainer for one venture and a playful consumer short
for another** — the only things that change are four JSON files.

**No video-generation model anywhere.** Every shot is a still from GPT Image 2
(reference-conditioned so characters and environments stay consistent),
animated procedurally with FFmpeg (Ken Burns / parallax / pose-crossfade),
over an ElevenLabs voice-over with kinetic captions, mixed for social and
delivered as a 9:16 MP4.

**Start here: [SKILL.md](SKILL.md)** — the entry point and full workflow.

## Why config-driven

Four things stay strictly separate, so the pipeline code never changes:

| | |
|---|---|
| **Style pack** | *how* things are drawn — line weight, palette, forbidden list. Never *who*. |
| **Character bible** | the actual characters, each built inside one style pack, each with a **locked** reference image. |
| **Background library** | reusable, tagged environments, generated once. |
| **Tone/brand profile** | serious vs playful: voice, pacing, caption style, motion intensity, disclaimer flag, narrative template. |

```
projects/consumer_promo_01/project.json
  → style_pack:  "stick_figure_v1"
  → tone_profile:"playful_consumer"
  → characters:  ["hoodie_guy", "coach_woman", "future_guy"]
  → backgrounds: ["city_sidewalk", "small_bedroom", "coffee_shop"]
  → script:      "scripts/promo.txt"
```

Swap `stick_figure_v1` → `flat_corporate_v1` and `playful_consumer` →
`serious_finance` and the same modules produce a completely
different-feeling video.

## Layout

```
SKILL.md                     entry point / workflow
pipeline/                    the engine (import-safe Python package)
  config  style_packs  characters  backgrounds  tone  narrative
  imagegen  animate  captions  render  cli          the 11 spec modules
  kie  tts  align  music  util                       support
schemas/                     JSON Schema for every config type
style_packs/                 stick_figure_v1, mascot_animal_v1, flat_corporate_v1
tone_profiles/               serious_finance, playful_consumer, authoritative_b2b
narrative_templates/         problem_mechanism_payoff, myth_bust, before_after, listicle
references/                  scriptcraft · config authoring · prompt templates · viral playbook · motion & captions · troubleshooting
projects/
  example_playful_app/       worked example B (myth-bust, 3 chars, high motion)
  example_finance/           worked example A (explainer, 2 chars, disclaimer)
  smoke_test/                tiny end-to-end proof + a project-local tone override
scripts/preflight.py         environment check
INSTALL.md                   full installation guide (skill + standalone)
tests/                       42 tests, Kie stubbed, real ffmpeg
```

## Installation

Full step-by-step (both as a Claude Code skill and as a standalone CLI, with
per-OS notes) is in **[INSTALL.md](INSTALL.md)**. The short version:

```bash
# prerequisites: Python 3.10+, FFmpeg 6+ with libass, Node/npm
git clone https://github.com/lxlbxl/multi-tone-video-pipeline.git
cd multi-tone-video-pipeline
python -m pip install -r requirements.txt
npm install -g kie-cli
export KIE_API_KEY="..."                      # https://kie.ai/api-key
python scripts/preflight.py --ping             # every line should be [ OK ]
```

Install it as a Claude Code skill by cloning into your skills directory:

```bash
git clone https://github.com/lxlbxl/multi-tone-video-pipeline.git \
  ~/.claude/skills/multi-tone-video-pipeline
```

## Quick start

```bash
python -m pipeline --project projects/example_playful_app/project.json --dry-run
python -m pipeline --project projects/example_playful_app/project.json
```

`script` and `shotlist` are checkpoints — the CLI stops for the creative pass,
then you re-run. See [SKILL.md](SKILL.md) for the full workflow.

## Requirements

- Python 3.10+ with `jsonschema`, `Pillow` (`faster-whisper` optional, for
  tighter caption sync)
- `ffmpeg` / `ffprobe` 6+ with libass (bundled in gyan.dev / BtbN builds)
- `kie-cli` on PATH and a `KIE_API_KEY` with credits

## Tests

```bash
python -m pytest        # 42 tests; Kie is stubbed, ffmpeg is real (~3 min)
```

## Credits

`references/scriptcraft.md` synthesises two open Claude-skill packs, adapted to
this pipeline's format:

- storytelling — [artemnovitckii/content-skills](https://github.com/artemnovitckii/content-skills)
- viral-content-framework — [mohitagw15856/pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills)

## License

MIT — see [LICENSE](LICENSE).
