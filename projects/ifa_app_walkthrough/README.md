# IFA.ng app walkthrough (evergreen)

A ~78 s 9:16 promo that walks through the real ifa.ng consultation flow in mobile view, with kinetic step slams,
synced chips, a Nigerian-English voiceover, a synthesized afro-pop groove and the real ifa.ng hero chant.

## How it was made
- `capture/*.js`: Playwright (iPhone 14 Pro emulation) captures of the live site: homepage, How-it-works step
  cards, the Google Meet session mock, the example Session-notes card, Find-your-Babalawo search (typing + filters),
  phone sign-in (a fictional 555 number typed, never submitted), the Odù library, and the hero chant video
  (`/hero/hero-chant-mobile.webm`).
- Everything inside the phone frame is the real site UI. Chips, stamps and the "Meet link" notification are
  overlays, not fake app screens.
- `build_edit.py [evergreen|prelaunch|postlaunch]`: VO phrase timings → word-timed captions + cue points → `edit.json`.
- `reel.html` + `render.js`: canvas renderer (`START_FRAME/END_FRAME/OUT_NAME` for parallel workers; streams hero
  video frames from `hv/`).
- `sound_app.py`: VO + ducked 108 bpm groove (kick/clap/shaker/bass/plucks/talking-drum) + UI sounds + hero chant.

## Swappable end card
`variant` in `edit.json` picks the last 5.5 s: `evergreen` (Book a consultation), `prelaunch` (Opening soon), or
`postlaunch` (Now live). Only the end card re-renders between variants.
