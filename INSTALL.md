# Installation

There are two ways to use this project. Pick one (or both — they share the
same code).

- **A. As a Claude Code skill** — Claude runs the pipeline for you, doing the
  script and shot-list passes itself.
- **B. Standalone CLI** — you run `python -m pipeline …` directly.

Both need the same three things on your machine: **Python 3.10+**, **FFmpeg 6+
with libass**, and **`kie-cli` + a Kie API key**.

---

## 1. Prerequisites

### 1.1 Python 3.10+

```bash
python --version        # must be >= 3.10
```

Install the Python dependencies (from the repo root):

```bash
python -m pip install -r requirements.txt
```

That installs `jsonschema` and `Pillow` (runtime) and `pytest` (tests).
Optionally, for tighter caption timing:

```bash
python -m pip install faster-whisper
```

Without it, caption timing falls back to a proportional estimate — fine for
the 1–3-word caption "pops" this pipeline uses.

### 1.2 FFmpeg 6+ **with libass**

`ffmpeg` and `ffprobe` must be on your `PATH`, and the build must include the
`ass` filter (used to burn in captions). Most "full" builds do.

| OS | Install |
|----|---------|
| **Windows** | `winget install "FFmpeg (Essentials Build)"` or download a full build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) / [BtbN](https://github.com/BtbN/FFmpeg-Builds). The "essentials"/"full" builds include libass. |
| **macOS** | `brew install ffmpeg` |
| **Linux** | `sudo apt install ffmpeg` (Debian/Ubuntu) — or your distro's package |

Verify:

```bash
ffmpeg -hide_banner -filters | grep " ass "     # should print a line
```

### 1.3 kie-cli + API key

```bash
npm install -g kie-cli
export KIE_API_KEY="sk-..."        # get one at https://kie.ai/api-key
```

- On **Windows**, npm installs `kie-cli.cmd`; the pipeline resolves it
  automatically (don't worry about the shim).
- `KIE_AI_API_KEY` is also accepted as the variable name.
- No uploader/`KIE_UPLOAD_CMD` is needed — reference images are uploaded to a
  public URL through Kie's own file endpoint, built in.
- Check your balance: `curl -H "Authorization: Bearer $KIE_API_KEY" https://api.kie.ai/api/v1/chat/credit`

### 1.4 Fonts (captions)

Captions render in whatever `caption_style.font_family` the tone profile names
(default **Arial**, present on Windows/macOS). On Linux install it
(`sudo apt install ttf-mscorefonts-installer`) or change the tone profiles to
a font you have (e.g. `DejaVu Sans`).

---

## 2. Get the code

```bash
git clone https://github.com/lxlbxl/multi-tone-video-pipeline.git
cd multi-tone-video-pipeline
```

---

## 3. Verify

```bash
python scripts/preflight.py --ping
```

Every line should be `[ OK ]`. Then run the test suite (Kie is stubbed, FFmpeg
is real, ~3 minutes):

```bash
python -m pytest
```

42 tests should pass. Finally, a no-cost plan of a real project:

```bash
python -m pipeline --project projects/example_playful_app/project.json --dry-run
```

You're installed.

---

## A. Install as a Claude Code skill

Clone (or symlink) the repo into your skills directory so Claude discovers it:

```bash
git clone https://github.com/lxlbxl/multi-tone-video-pipeline.git \
  ~/.claude/skills/multi-tone-video-pipeline
```

- **Windows:** `~/.claude/skills/` is `C:\Users\<you>\.claude\skills\`.
- Restart Claude Code (or start a new session) so it picks up the new skill.
- Update later with `git -C ~/.claude/skills/multi-tone-video-pipeline pull`.
- The prerequisites in §1 still apply — the skill shells out to `python`,
  `ffmpeg`, and `kie-cli` on your machine.

Then just ask Claude for a narrated explainer / promo / myth-bust / before-after
/ listicle short, or say "use the multi-tone-video-pipeline skill". Claude reads
[SKILL.md](SKILL.md) and drives the stages, doing the script and shot-list
creative passes itself and stopping for your review at each checkpoint.

---

## B. Standalone CLI

```bash
python -m pipeline --project projects/<name>/project.json            # full run
python -m pipeline --project projects/<name>/project.json --dry-run   # plan + credit estimate
python -m pipeline --project projects/<name>/project.json --stage tts # one stage
python -m pipeline --project projects/<name>/project.json --from animate
```

Optionally install it as a console command:

```bash
python -m pip install -e .      # gives you `mtvp --project …`
```

### Making your first video

1. Copy `projects/example_playful_app/` to `projects/my_video/` and edit
   `project.json` (see [references/config_authoring.md](references/config_authoring.md)).
2. `python -m pipeline --project projects/my_video/project.json --dry-run` —
   fix any config error it reports.
3. Run without `--dry-run`. At the **script** checkpoint it writes a drafting
   prompt; write the script, save it where told, re-run.
4. At the **shotlist** checkpoint it writes a scaffold to
   `projects/my_video/shots/shot_list.json`; fill in the `composition` lines
   (prompt in [references/prompt_templates.md](references/prompt_templates.md)),
   re-run.
5. Output lands in `projects/my_video/output/my_video_final.mp4` with a
   manifest.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `preflight: kie-cli not on PATH` | `npm install -g kie-cli`; reopen the shell |
| `preflight: 'ass' filter not found` | Install a full FFmpeg build (gyan.dev / BtbN / `brew`) |
| `KIE_API_KEY not set` | `export KIE_API_KEY=...` (or set it in your shell profile) |
| Captions render in a serif fallback | The tone's `font_family` isn't installed — install it or edit the tone profile |
| `FileNotFoundError` calling `kie-cli` on Windows | Upgrade to the current version of this repo — it resolves the `.cmd` shim |
| Upload `403 / error code: 1010` | Transient Cloudflare block; the wrapper retries. If persistent, check Kie's status |
| Captions drift across the whole video | You're on the proportional fallback — `pip install faster-whisper` |

More in [references/troubleshooting.md](references/troubleshooting.md).
