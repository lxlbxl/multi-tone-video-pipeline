# Prompt templates for the creative passes

Two steps need judgement, not code: writing the script and filling the shot
list. The CLI stops at each so a human or Claude can do them. These are the
prompts.

The script pass is where the video is won or lost — read
[scriptcraft.md](scriptcraft.md) first; this section just operationalises it.

---

## 1. Script draft

The CLI writes `<name>_PROMPT.txt` pre-filled with the specifics. Its shape:

```
You are writing the spoken voice-over for a <target_seconds>s vertical video.
Brief: <brief>
Voice / tone: <tone.voice_style>
Length: EXACTLY ~<N> words (<pacing_wpm> wpm x <target_seconds>s). Running long
        is the #1 failure — cut beats, never the lens or the last line.
Narrative template: <template.id>   ·   Hook rule: <template.hook_rules>
Connector rule: <template.connector_rule>

Beats to cover, in order (put a BUT or THEREFORE between each — never "and then"):
  1. <beat.id>: <beat.purpose>
  2. ...

Method (from scriptcraft.md — do these in order):
1. LENS. Before writing, pick the ONE non-obvious angle on this brief. Not
   "struggled then succeeded". Invert the villain / find the asset in the
   failure / jump to the second-order effect. State the lens in one line.
2. ENDS FIRST. Write the last line — the "last dab": so sharp that hearing only
   that line makes someone share it, and it loops back into the hook on replay.
   Then write a working first line.
3. DANCE. Fill the beats. Between every beat the connector is BUT or THEREFORE.
   If "and then" fits, the beat is boring — cut it. >= 2 open loops in the
   first 30s.
4. RHYTHM. One sentence per line. Vary lengths — short, short, long. The left
   edge must look jagged. Read it aloud.
5. TONE. Rewrite anything that sounds like a speech into something you'd say to
   one friend. Match <tone.voice_style>.
6. HOOK. Finalise line 1 with a formula from scriptcraft.md §7 (match the
   template): contrarian / specific-number / uncomfortable-truth / listicle-
   tease / story / pattern-interrupt-question. Punchy, plot-indicative. No
   "in this video", no greeting, no "wait till you see this".
7. LENGTH. Trim to the word count above.

Hard rules:
- Real material only. Never invent numbers, events, or biography.
  <if disclaimers_required: every claim must be defensible.>
- Spoken words only — no stage directions, no scene labels, no emojis.
- Land on ONE takeaway / CTA: "<cta>"
- <disclaimer instruction, if the tone requires one>
- Name the shareability motivation you're aiming for (identity / utility /
  emotion / tribe / status / validation) on its own comment line at the top,
  prefixed with "# ", then the script below it.

Output: the "# motivation:" line, then the script text. Nothing else.
```

Save the result at the path the prompt names (drop the `# motivation:` line or
leave it — the pipeline strips leading `#` comment lines), then re-run.

### Audit an existing script

Run the checklist at the bottom of [scriptcraft.md](scriptcraft.md). Flag each
offending line specifically: every "and then" / detail-pile beat, a trailing
"follow for more" ending, the obvious lens, a flat rhythm stretch, any line
that performs instead of talks.

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
