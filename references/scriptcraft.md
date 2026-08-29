# Scriptcraft — hooks, storytelling, shareability

The pipeline is deterministic tooling; the **script is where a video wins or
loses**. This is the craft the `script` checkpoint must apply, before a single
image is generated.

> Synthesised from two open skill packs — the "storytelling" skill
> ([artemnovitckii/content-skills](https://github.com/artemnovitckii/content-skills))
> and the "viral-content-framework" skill
> ([mohitagw15856/pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills)) —
> adapted to this pipeline's stills-plus-motion, tone-profile-driven format.

---

## 1. Use real material — never invent

Pull the actual beats from the brief, the user's notes, or ask. **Never
fabricate biography, numbers, or events.** Invented founder stories and fake
proof destroy the exact trust short-form content is built to earn. Structure is
this skill's job; the truth is the user's. If the real beats aren't there, get
them before writing.

For a `disclaimers_required` tone (finance, health), this is not optional —
every claim in the script must be defensible.

---

## 2. Pick the lens before you write (`§ Story Lens`)

A topic isn't enough — dozens of accounts cover the same topic. The **lens** is
your unique prism on it. Pick it first; it changes every line after.

List the obvious lenses, then push past them:

- **Invert the villain.** The obvious villain (the algorithm, the rent, the
  competitor) usually isn't the real one. What if it was your own assumption?
- **Find the asset in the failure.** The thing you were embarrassed by — the
  empty slots, the "too small" niche — is often the actual product.
- **Jump to the second-order effect.** Don't cover the event; cover what it
  quietly caused that nobody's connecting.
- **Switch the POV.** Tell it from the angle no one takes (the customer's, the
  loser's, the object's).
- **Flip the cost/benefit.** What everyone calls the win was the cost, or
  vice-versa.

Weak lens: "I struggled, then I succeeded" — that's everyone's story.
Sharp lens: "the thing that saved the business is the thing I was embarrassed
to sell."

---

## 3. Write the end first (`§ Direction`)

Decide where you're taking the viewer, then work backward.

- Write the **first line** and the **last line** first. Leave the middle blank.
- The last line is the **"last dab"**: so memorable that if someone heard only
  that line, they'd share it. Not "…and now we're booked. Follow for more."
- Short-form **loops** — write the last line so it hands back into the hook on
  replay.

Then fill the middle with beats that earn that ending.

---

## 4. The Dance — BUT / THEREFORE, never "and then" (`§ The Dance`)

Great narrative alternates **context** (the character is doing something) and
**conflict** (a complication). Conflict opens a loop in the brain; context
closes it, then opens the next. That's what holds a viewer.

**The rule (from the South Park writers):** the connector between every beat is
**BUT** or **THEREFORE** — never "and then." If "and then" fits, the beat is
boring — rewrite it or cut it.

Weak — "and then" piling:
> My rent doubled and then enrollment dropped and then I tried a free class and
> then it sold out and then now I'm booked.

Strong — but/therefore loops:
> My rent doubled. **THEREFORE** I was three months from closing. **BUT** I had
> all these empty evening slots. **THEREFORE** I tried one free date-night class
> — **BUT** I had no idea if a single person would show.
> *(loop held open…)* Twelve couples booked it in a day.

Stack several open loops in the first 30 seconds. When you fill the shot list's
beat sequence, force a BUT or THEREFORE between each beat.

---

## 5. Rhythm — write music, not monotony (`§ Rhythm`)

Same-length sentences in a row drone, and the viewer churns. Vary it: short.
Then medium. Then, once in a while, a longer sentence that builds with energy
and rolls to a close.

**Test:** write every sentence on its own line and look down the left edge. A
**jagged edge** = varied lengths (good). All lines ending near the same column =
monotone — break some up, run some together. Then read it aloud: the real test
is hearing the variation in breath.

> It sold out.
> Couples loved it — two people, one wheel, clay everywhere, laughing.
> So I added more.

---

## 6. Tone — talk to one person (`§ Tone`)

Write and read as if talking to **one close friend**, not "an audience." Type
the script like a voice note to that person. Conversational, direct, no
performing. If a line sounds like a speech, rewrite it as something you'd
actually say. Match the tone profile's `voice_style` on top of this.

**Founder / personal stories may use "I".** First-person on the owner's own
account is fine — the relevance comes from **universal resonance** (the viewer
recognises their own situation in yours), not from literally saying "you." Make
the I-story land on a feeling or lesson the viewer shares.

---

## 7. The hook — first line does the whole job

You have ~1.5 seconds (video) or one sentence. The hook must be **punchy and
indicative of the plot** — never "wait till you see this," never "in this
video," never "hey guys." Start mid-action. For video, lead with a **visual
hook** (shot s01's composition) *and* the verbal hook together — eyes perceive
faster than ears.

### Hook formulas (pick one, match it to the narrative template)

| # | Formula | Shape | Pairs with |
|---|---|---|---|
| 1 | **Contrarian statement** | "[Widely believed thing] is wrong / overrated." | `myth_bust` |
| 2 | **Specific number / result** | "I [result] in [timeframe]. Here's how." | `problem_mechanism_payoff`, `before_after` |
| 3 | **Uncomfortable truth** | "Nobody wants to hear this, but [truth]." | `myth_bust`, `problem_mechanism_payoff` |
| 4 | **Listicle tease** | "[X] things I wish I'd known about [topic]." | `listicle` |
| 5 | **Story hook** | "[Specific moment that sets up a tension]." | `before_after` |
| 6 | **Pattern-interrupt question** | "[Question the audience has never been asked about a familiar topic]." | any |

Weak: "Let's talk about hydration." Strong (Formula 1): "You're not tired
because you need more coffee."

---

## 8. Shareability — why would anyone send this to a friend?

High reach = **strong hook × valuable substance × easy shareability**. All
three. A strong hook on thin content gets clicks, not shares. Every script
should trigger at least one sharing motivation:

| Motivation | Trigger it by |
|---|---|
| **Identity** — "sharing this says something good about me" | make the viewer look smart/informed/principled for sharing |
| **Utility** — "too useful not to pass on" | teach something with an immediate result |
| **Emotion** — "this made me feel something" | surprise, delight, righteous anger, nostalgia |
| **Tribe** — "my people need to see this" | speak to one tight community, specifically |
| **Status** — "I'm ahead of the curve" | contrarian take, insider info |
| **Validation** — "exactly what I couldn't articulate" | be the viewer's spokesperson for something they already believe |

Name the target motivation in the brief. Serious/finance usually plays
Utility + Validation; playful/consumer usually Emotion + Identity.

---

## 9. Length budget (the one hard constraint)

Spoken delivery ≈ **2 words/second** (before TTS speed). Match the tone's
`pacing_wpm` and the project's `target_seconds`:

| target | ~words @ 145 wpm | ~words @ 175 wpm |
|---|---|---|
| 20 s | 48 | 58 |
| 30 s | 72 | 88 |
| 45 s | 109 | 131 |
| 60 s | 145 | 175 |

The `script` checkpoint's `_PROMPT.txt` computes the exact number. Craft-per-line
doesn't matter if the script runs 15 seconds long — **cut beats, keep the lens
and the last dab.**

---

## Audit checklist (run in `--stage script` review, or on any draft)

- [ ] Real beats, nothing invented (claims defensible if `disclaimers_required`)
- [ ] A unique lens, not the obvious "struggled → succeeded" arc
- [ ] First + last line written first; last line is a shareable **last dab** that loops into the hook
- [ ] **BUT / THEREFORE** between beats — count the "and then" / detail-piling beats and rewrite each; ≥ 2 open loops in the first 30 s
- [ ] Jagged left edge — varied sentence lengths; reads right aloud
- [ ] Sounds like one friend talking, not a speech
- [ ] Hook uses a formula from §7, is plot-indicative, and shot s01 carries a visual hook
- [ ] One named shareability motivation (§8)
- [ ] Within the length budget (§9) for `target_seconds` at the tone's wpm
