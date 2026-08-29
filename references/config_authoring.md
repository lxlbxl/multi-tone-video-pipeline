# Config authoring

Every knob that makes a serious B2B video different from a playful consumer
short lives in JSON. Schemas are in `schemas/`; the CLI validates against them
and refuses to run on a violation.

## Lookup order

For any library doc (`style_packs/`, `tone_profiles/`, `narrative_templates/`,
`characters/<style_pack>/`, `backgrounds/<project>/`):

1. `projects/<name>/<kind>/<id>.json` — project-local override
2. `<repo_root>/<kind>/<id>.json` — shared library
3. `$MTVP_LIB_DIR/<kind>/<id>.json` — extra dir (optional)

`projects/smoke_test/tone_profiles/playful_consumer.json` is a working example
of a project-local override (music turned off for a cheaper test run).

---

## project.json

```jsonc
{
  "name": "consumer_promo_01",          // ^[a-z0-9_]+$  — also the output folder
  "brief": "one line: what this video is",
  "style_pack": "stick_figure_v1",       // -> style_packs/stick_figure_v1.json
  "tone_profile": "playful_consumer",    // -> tone_profiles/playful_consumer.json
  "narrative_template": "myth_bust",     // optional; defaults to the tone profile's
  "script": "scripts/promo.txt",         // optional; omit to be prompted to draft one
  "seed": 4412,                          // reused on every generation for stability
  "aspect": "9:16",                      // 9:16 | 1:1 | 16:9 | 4:3 | 3:4
  "resolution": "1K",                    // 1K | 2K | 4K  (GPT Image 2)
  "target_seconds": 30,
  "cta": "Search 'Streakly' and start today",
  "disclaimer_text": "…",                // optional; overrides the tone profile's
  "characters": [ /* names or inline objects — see below */ ],
  "backgrounds": [ /* names or inline objects — see below */ ]
}
```

### characters[]

Either a **string** (`"hoodie_guy"` → `characters/<style_pack>/hoodie_guy.json`)
or an **inline object**:

```jsonc
{
  "name": "hoodie_guy",
  "style_pack": "stick_figure_v1",   // MUST equal the project's style_pack
  "role": "protagonist, relatable everyman",
  "description": "green hoodie, cap worn backwards, sneakers",
  "voice_tag": "casual_male_1",       // free-form label, for your own reference
  "prompt_extra": "always slightly slouched"  // optional extra prompt text
}
```

The reference image lands at `characters/<style_pack>/<name>_ref.png` and is
**locked** — generated once, reused on every shot and every future video that
lists the same character. `--force-refs` rebuilds it deliberately.

### backgrounds[]

String (`"city_sidewalk"` → `backgrounds/<project>/city_sidewalk.json`) or
inline:

```jsonc
{
  "name": "city_sidewalk",
  "description": "generic downtown sidewalk, mid-rise buildings, midday",
  "tags": ["outdoor", "neutral", "urban"],   // REQUIRED — shot list selects by tag
  "shared": true    // optional: generic enough to reuse across projects
}
```

---

## style_packs/*.json  — *how*, never *who*

```jsonc
{
  "id": "stick_figure_v1",
  "render_prefix": "2D stick-figure illustration, …, no realistic faces",
  "line_weight": "bold",
  "palette": ["#F0EAE0", "#8FBFA3", "#2C3E50"],
  "reference_pose": "single character, front three-quarter view, …",  // appended for character refs
  "background_suffix": "empty environment with no characters, …",      // appended for backgrounds
  "forbidden": ["copyrighted characters", "realistic faces", "photographic textures"]
}
```

`render_prefix` is prepended to **every** generation. `forbidden` is emitted as
a "do not include" clause AND checked against every composition line (plus a
built-in named-IP blocklist in `style_packs.py`).

To add a style pack: drop a new `<id>.json` in `style_packs/`, point a project
at it. No code change.

---

## tone_profiles/*.json  — serious vs playful

```jsonc
{
  "id": "serious_finance",
  "voice_style": "measured, low pitch, minimal filler",   // used in the script prompt
  "tts_voice_id": "onyx",            // OpenAI name (auto-mapped) OR an ElevenLabs voice name
  "tts_model": "multilingual",       // turbo | multilingual
  "tts_stability": 0.6,
  "tts_style": 0.15,
  "pacing_wpm": 145,                  // -> TTS speed AND script target length
  "caption_style": {
    "font_family": "Arial",
    "font_weight": "bold",            // regular|medium|semibold|bold|extrabold|black
    "max_words_per_pop": 2,           // 1 = one word at a time (punchy)
    "color": "#FFFFFF",
    "stroke": "#000000",
    "stroke_px": 6,
    "uppercase": false,
    "position": "lower_third"         // lower_third | center | upper_third
  },
  "narrative_template": "problem_mechanism_payoff",
  "shot_hold_seconds_min": 6,         // never cut faster than this (validator-enforced)
  "motion_intensity": "low",          // low | medium | high
  "disclaimers_required": true,
  "disclaimer_text": "This is not financial advice…",
  "music": { "enabled": false, "prompt": "sparse piano underscore", "gain_db": -26 }
}
```

`tts_voice_id` mapping (OpenAI → ElevenLabs, see `pipeline/tone.py`):
`alloy→Sarah  echo→Charlie  fable→Alice  onyx→George  nova→Aria  shimmer→Jessica
ash→Brian  ballad→Will  coral→Laura  sage→River  verse→Liam`. Any of the 21
ElevenLabs names (`Rachel, Aria, …, Bill`) also passes straight through.

---

## narrative_templates/*.json  — a beat sequence the shot list fills

```jsonc
{
  "id": "problem_mechanism_payoff",
  "fits": "serious / explainer",
  "hook_rules": "Open on the cost of the problem, first sentence, no throat-clearing.",
  "cta_beat": "takeaway",
  "beats": [
    { "id": "hook", "purpose": "name the expensive problem in one sentence", "weight": 1.0 },
    { "id": "mechanism", "purpose": "how the fix works, step by step", "weight": 1.6 },
    { "id": "item", "purpose": "…", "weight": 1.0, "repeatable": true }   // listicle-style
  ]
}
```

`weight` = relative share of runtime. `repeatable: true` lets one beat expand
into N shots (listicle items). Add templates freely — it's swappable JSON.
