# Prompt templates for the creative passes

Two steps need judgement, not code: writing the script and filling the shot
list. The CLI stops at each so a human or Claude can do them. These are the
prompts.

---

## 1. Script draft

The CLI writes `<name>_PROMPT.txt` pre-filled with the specifics. Its shape:

```
You are writing the spoken voice-over for a <target_seconds>s vertical video.
Brief: <brief>
Voice / tone: <tone.voice_style>
Length: ~<N> words at <pacing_wpm> wpm.
Narrative template: <template.id>
Hook rule: <template.hook_rules>

Beats to cover, in order:
  1. <beat.id>: <beat.purpose>
  2. ...

Rules:
- The FIRST SENTENCE is the hook. No "in this video", no "today I want to
  talk about", no greeting. Land the stakes / the myth / the before-state
  immediately.
- Spoken words only — no stage directions, no scene labels, no emojis.
- One idea per sentence. Short sentences. Contractions.
- Read it aloud; if you stumble, rewrite it.
- Land on ONE takeaway / CTA: "<cta>"
- <disclaimer instruction, if the tone requires one>

Output: just the script text, nothing else.
```

Save the result at the path the prompt names, then re-run the pipeline.

---

## 2. Shot list fill

After `tts` + `align`, run `--stage shotlist`. It writes a **scaffold** to
`projects/<name>/shots/shot_list.json`: beats already spread across the VO
timeline, timings that respect `shot_hold_seconds_min`, captions already sliced
from the aligned words. You fill the creative fields.

Prompt:

```
You are turning this scaffold shot list into a shootable one. Keep every
`start`/`end` as-is unless a shot clearly needs to be longer (then push later
shots later too, never past `audio_duration`). For each shot set:

- composition: ONE vivid sentence. Who is in frame, where they stand, what
  they are doing, the camera framing (wide / medium / close). Present tense.
  Name only characters from the bible: <character names>.
  No copyrighted characters, no real people, no brand logos, no on-image text.

- characters: the subset of the bible actually visible this shot (<= 3).

- background: a library name (<background names>) OR "auto" with
  background_query tags (e.g. ["indoor","calm"]) to auto-match.

- motion.type:
    ken_burns      one still, slow push/pan. Default.
    parallax       one still, stronger dual-rate drift. Use for a "reveal".
    pose_crossfade two stills (set motion.pose_b to the second composition).
                   Use when a character visibly changes pose/expression.
    hold           near-static. Use for a dense caption / disclaimer moment.
  motion.direction: in|out|left|right|up|down

- captions: tighten the wording (the scaffold split raw words). Keep each pop
  <= <max_words_per_pop> words. Set "emphasis": true on the ONE word per shot
  that should punch (the number, the payoff, the "WRONG").

Match beat intent:
  <beat.id>: <beat.purpose>
  ...

Then STOP. The next re-run validates and starts generating images (costs
credits).
```

Re-run `--stage shotlist` to validate. It hard-fails on: cut faster than the
tone minimum, a character not in the bible, a background not in the library, a
caption over the word cap, a shot ending past the VO, a `pose_crossfade`
without `pose_b`.

---

## 3. Composition line patterns that generate cleanly

GPT Image 2 with reference images is most reliable when the composition:

- puts **one action verb** front and centre ("gestures at", "slumps onto",
  "holds up", "points to")
- gives **screen position** ("centre-left", "lower third", "entering from
  frame right")
- states **framing** once ("medium shot", "wide", "tight on the face")
- ends by deferring identity to the refs: the pipeline auto-appends *"Match
  every provided character reference exactly …"* — you don't write that.

Good: `Medium shot, hoodie_guy slumps onto the edge of the unmade bed, phone
face-down in his hand, staring at the floor.`

Weak: `hoodie_guy is sad about his habits` (no framing, no action, no position).
