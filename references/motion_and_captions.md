# Motion and captions

Both are driven entirely by `tone_profile.motion_intensity` and
`tone_profile.caption_style`. No per-shot styling knobs — the shot list only
picks a motion *type* and *direction*.

## motion_intensity → FFmpeg params (`pipeline/tone.py::_MOTION`)

| | `zoom_per_s` | `pan_pct` | `xfade_s` | `pop_ms` |
|---|---|---|---|---|
| low | 0.010 | 2% | 0.60 | 130 |
| medium | 0.020 | 5% | 0.40 | 90 |
| high | 0.033 | 9% | 0.25 | 60 |

- `zoom_per_s` — zoom added per second of shot, capped at 0.6 total.
- `pan_pct` — max drift as a fraction of the oversampled frame width.
- `xfade_s` — crossfade duration for `pose_crossfade`.
- `pop_ms` — caption fade/scale-in time.

## Motion types (`pipeline/animate.py`)

- **ken_burns** — one still. Oversample 2×, then a per-frame animated `crop`
  (size shrinks/grows for zoom, offset drifts for pan), scaled back to
  1080×1920. Smooth, no `zoompan` jitter. `direction: in|out` gets a faint
  diagonal drift; `left/right/up/down` pans that way while zooming slightly in.
- **parallax** — same mechanism, 1.6× zoom and 1.8× pan, plus a 0.6px blur on
  the oversample so the push reads as depth. Best for a "reveal" beat. True
  layered parallax needs a depth matte — a future enhancement; this is a
  convincing approximation for flat illustration.
- **pose_crossfade** — two stills (`shots/sNN_a.png`, `shots/sNN_b.png` from
  `motion.pose_b`). Each gets a half-length micro Ken Burns, then `xfade=fade`.
  Total duration is exact. Use when a character visibly changes.
- **hold** — Ken Burns at 0.25× zoom, no pan. For dense-caption or disclaimer
  moments.

Every clip is rendered to the same contract — 1080×1920, 30 fps, yuv420p,
libx264 CRF 18, no audio — so `render.py` concatenates without artefacts.

## Captions → ASS (`pipeline/captions.py`)

Word groups (≤ `max_words_per_pop`, sentence-aware) become one ASS `Dialogue`
line each, timed from the aligned words.

Style mapping:

| caption_style | ASS |
|---|---|
| `color` | `PrimaryColour` (hex → `&HAABBGGRR`) |
| `stroke` + `stroke_px` | `OutlineColour` + `Outline` width, `BorderStyle: 1` |
| `font_weight` ≥ semibold | `Bold: 1` |
| `font_family` | `Fontname` (must be installed; Arial is safe on Windows) |
| `position` | `MarginV`: lower_third 260 / center 780 / upper_third 1250, `Alignment: 2` |
| `max_words_per_pop` | font size: 1→118, 2→104, 3→92, else 84 |
| `uppercase` | text upper-cased |

Pop-in:
- **low** intensity → `\fad(pop_ms, pop_ms)` only (calm).
- **medium/high** → `\fad` + scale bounce: start at 114–128%, settle to 100%
  over `pop_ms + 90`ms. `emphasis: true` groups start bigger (128%).

Burned in with `-vf ass=…` (libass, bundled in modern FFmpeg). On Windows the
filter path has its drive colon escaped (`C\:/…`).

### Changing the caption look

Edit the tone profile. To use a brand font, install the `.ttf` system-wide (or
into a dir on the font path) and set `caption_style.font_family` to its exact
family name. There is no per-project font-file bundling yet — add the `.ttf` to
`assets/fonts/` and an `fontconfig` dir if you need it portable.
