# Viral playbook

This pipeline makes *stills that move*, not generated video. That is a
constraint and an advantage: the frame is always on-model, the text is always
legible, and you can iterate a hook in minutes. What it does **not** do for you
is earn attention — that is the script and the shot list. This doc is the bar
for the *visual/edit* side; the *script* side is
[scriptcraft.md](scriptcraft.md) (hook formulas, the BUT/THEREFORE dance,
write-the-end-first, rhythm, tone).

## Why anyone shares (name the target motivation in the brief)

High reach = **strong hook × valuable substance × easy shareability** — all
three. Every video should be built to trigger one or two of these:

| Motivation | Trigger it by | Typical fit |
|---|---|---|
| **Identity** | make the viewer look smart/principled for sharing | playful/consumer |
| **Utility** | one actionable thing with an immediate result | explainer, B2B |
| **Emotion** | surprise, delight, righteous anger, nostalgia | consumer, story |
| **Tribe** | speak to one tight community, specifically | niche B2B, community |
| **Status** | contrarian take, insider info, "ahead of the curve" | thought-leadership |
| **Validation** | say what the viewer believes but couldn't articulate | opinion, finance |

Serious/finance usually plays **Utility + Validation**; playful/consumer usually
**Emotion + Identity**. If you can't name why someone would send it to a
friend, the video isn't done.

## The first 1.5 seconds decide everything

- **Frame 1 is a scroll-stopper, not a title card.** Open mid-scene, mid-action,
  mid-expression. The scaffold's first shot is the hook beat — make its
  composition the single most arresting image in the video.
- **The first spoken sentence contains the tension.** The myth stated as truth
  ("You think you failed because you're lazy"). The cost ("One car repair is
  why most investing plans fall apart"). The before-state at its worst. Never a
  greeting, never "in this video", never a throat-clear.
- **A caption is on screen by frame 10.** Sound-off viewers need the hook in
  text immediately. The hook caption should be readable in isolation.

## Retention

- **Cut on the idea, not the clock** — but never slower than the tone's
  `shot_hold_seconds_min`. Playful: every new sentence is a new shot. Serious:
  hold through a full thought, let the Ken Burns carry it.
- **One `emphasis: true` word per shot.** The number, the payoff, the "WRONG".
  It scales up on pop-in — that motion is a micro pattern-interrupt that resets
  the viewer's attention clock.
- **No dead air.** Every shot has motion (even `hold` has a 0.25× breathe) and a
  caption. A static, silent half-second is a swipe.
- **Front-load the payoff in a listicle.** Item 1 is the strongest. Assume most
  viewers leave after it; reward the ones who don't.

## Sound-on design

- Music bed **on** for playful/consumer (`tone.music.enabled`), ducked 12:1
  under the VO, whole mix normalised to **−14 LUFS** (platform target).
- Music **off or −26 dB** for serious/finance — a bed under a compliance
  explainer reads as manipulative.
- The VO voice *is* the brand. Keep `tts_voice_id` fixed across a venture's
  whole library, exactly like the character reference.

## Loopability

- End on a line that could precede the first line. "…let the streak carry you"
  → "You think you failed at every habit…". A clean loop doubles watch time for
  free.
- Last shot ends within ~1s of the VO. No trailing logo card unless a
  disclaimer is legally required (`disclaimers_required`).

## Format hygiene

- **9:16, 1080×1920, 30 fps.** Captions live in the middle 80% (safe from the
  UI chrome top and bottom). `caption_style.position: center` for playful,
  `lower_third` for serious.
- **1K generation is enough** for 1080p delivery — GPT Image 2 at 1K upscales
  cleanly through the Ken Burns oversample. Use 2K only for `hold` shots where
  a caption sits over fine detail.
- Thumbnail test: pause on the hook frame, shrink to 120px wide. If you can't
  tell what's happening, the hook fails.

## Iterating a hook cheaply

Character refs and backgrounds are locked, so re-rolling just the hook is:
```bash
# edit shots/shot_list.json — shot s01 composition + caption only
python -m pipeline --project … --stage shots --force   # regenerates all shots
```
To regenerate a single shot, delete `shots/s01.png` and run `--stage shots`
(cached shots are skipped). Then `--from animate`.

## What virality tooling can tell you

If the Kie/creative MCP `virality_predictor` is available, run the finished MP4
through it before publishing — it scores hook strength, attention retention
risk, and audio. Treat a weak-hook score as a signal to re-roll shot s01 and
the first sentence, not to add more shots.
