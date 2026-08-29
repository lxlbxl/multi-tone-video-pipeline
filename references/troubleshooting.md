# Troubleshooting

## Preflight

```bash
python scripts/preflight.py            # offline checks
python scripts/preflight.py --ping     # + verify KIE_API_KEY against the API
```

## kie-cli drift

kie.ai renames models and shuffles flags between `kie-cli` releases. Symptoms
and fixes:

| Symptom | Fix |
|---|---|
| `submit(...)` → "non-JSON response" | `kie-cli <tool> --help` — a flag was renamed. Update the `opts` in `pipeline/imagegen.py` / `tts.py` / `music.py`. |
| `no task_id in response` | The tool now returns `taskId` under a different key, or errored. Run the raw command with `--json` and inspect. |
| image tool rejects `--input_urls` | Confirm the flag name; GPT Image 2 uses `input_urls` (array). |
| `wait_for_task` unknown | Older kie-cli — use `get_task_status` in a poll loop, or upgrade: `npm i -g kie-cli`. |

The wrapper only ever calls: `gpt_image_2`, `elevenlabs_tts`,
`suno_generate_music`, `wait_for_task`. Keep those four working.

## Upload failures (reference images → public URL)

`pipeline/kie.py::upload` POSTs to
`https://kieai.redpandaai.co/api/file-base64-upload` with a browser User-Agent
(Cloudflare blocks the default urllib UA → `error code: 1010`).

- `403 / 1010` — UA header missing or changed; the wrapper already sets one.
  If it still 403s, the endpoint moved — check kie.ai's File Upload API docs.
- `KIE_API_KEY not set` — export it; uploads are authenticated.
- URLs are on `tempfile.redpandaai.co` and expire. Generate shots in the same
  run as the upload; don't leave `work/` half-done for days.

## Alignment

- Captions drift late/early across the whole video → you're on the proportional
  fallback. `pip install faster-whisper` for real timing, or
  `MTVP_ALIGN_GEMINI=1` (needs `GEMINI_API_KEY`).
- `faster-whisper` install fails on Windows → it needs `ctranslate2` wheels;
  `pip install --upgrade pip` first. It is optional — proportional is fine for
  1–2 word pops.
- A single caption is wildly off → edit its `start`/`end` in
  `shots/shot_list.json` directly and re-run `--from render`.

## FFmpeg

- **concat shows a stutter / colour pop at a cut** — `render._concat`
  re-encodes (not `-c copy`) for exactly this reason. If you changed it back,
  revert.
- **`ass=` filter: "Unable to parse option"** on Windows — the path colon isn't
  escaped. `captions.burn` does `C:/x` → `C\:/x`. Keep the `.ass` path free of
  spaces and non-ASCII.
- **caption font is wrong / falls back to a serif** — `caption_style.font_family`
  isn't installed. Install the TTF or set it to `Arial`.
- **Ken Burns looks like it's vibrating** — the still is smaller than
  1080×1920. GPT Image 2 at 1K is 1024-ish on the short side; the oversample
  handles it, but a hand-supplied tiny image won't. Regenerate at ≥1K.
- **`zoompan`** is deliberately not used — the animated `crop` approach avoids
  its sub-pixel jitter.

## Generation quality

- **Character looks different between shots** — the reference wasn't passed, or
  too many characters in one shot. Keep `characters` ≤ 3 per shot; check
  `shots/sNN.json` lists the ref URLs.
- **Background ignored** — GPT Image 2 weights the first `input_urls` entry
  most; the wrapper puts the background first. If it's still off, make the
  composition line name the setting explicitly.
- **Style drift** — someone edited `render_prefix` mid-project. The prefix must
  be identical for refs, backgrounds, and shots. Re-lock refs with
  `--force-refs` if you changed it on purpose.
- **On-image text appears** — add `"in-image text"` / `"text labels"` to the
  style pack's `forbidden`; it's emitted as a negative.

## Checkpoints won't advance

- `script` stage exits 2 with "No script yet" — that's by design. Draft
  `<name>_PROMPT.txt`'s ask, save as the `script` path, re-run.
- `shotlist` stage exits 2 with "wrote a SCAFFOLD" — fill the composition lines,
  re-run. `--auto` skips this and renders placeholder compositions (only useful
  for a plumbing test).

## Credits

`--dry-run` prints an estimate. Rough per-call: GPT Image 2 1K ≈ 12, 2K ≈ 18;
ElevenLabs TTS ≈ 6; Suno ≈ 30. A 6-shot 2-character video with music ≈ 150–200.
`chat/credit` endpoint: `curl -H "Authorization: Bearer $KIE_API_KEY"
https://api.kie.ai/api/v1/chat/credit`.
