# IFA.ng app promos: second set (no hero-video visuals)

Two new concepts with the same agenda as `projects/ifa_app_walkthrough` (show the real consultation flow, invite
Ifá lovers to try it). They use only the ifa.ng **hero chant audio**; no frame of the hero video or hero photo appears.
Every screen shown is a real ifa.ng mobile capture (see `projects/ifa_app_walkthrough/capture/`).

| Concept | Feel | Voice (ElevenLabs eleven_v4) | Length |
|---|---|---|---|
| A · The Cast | cinematic, mystical, gold on deep green; the app as the ọpọ́n Ifá, each step one row of Èjì Ogbè (Ìkíní · Ìkejì · Ìkẹta · Ìkẹrin) | "Steven - West African Narrator" | 52.5 s |
| B · Voice Note | playful chat between Ṣadé (London) and Mummy (Nigeria); real screens sent as image messages, live voice-note transcripts | "Chidinma" (Ṣadé), "Ifeoma Odumodu" (Mummy) | 56 s |

Each concept ships as `evergreen`, `prelaunch` and `postlaunch` (only the end card differs).

- `build_edits.py [variant]`: VO phrase timings → captions/cues → `concept_*/edit.json`
- `concept_*/reel.html` + `render.js`: canvas renderers (assets dir `a/` = the real captures + logo)
- `sound_v6.py A|B`: A = reverberant chant bed, àgogò bells and drums on each mark; B = chant as background vibe + chat sounds
