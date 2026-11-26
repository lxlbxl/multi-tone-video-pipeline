# Yemọja in Brazil: heritage explainer reel

A Carnival 2026 clip of a giant Yemọja water float, cut into a ~73 s 9:16 reel for ifa.ng with a Nigerian-English
explainer voiceover, kinetic effects, synthesized sound design and a closing call for Yorùbá pride.

- `build_edit.py`: VO phrase timings (from silence detection) → word-timed captions + cue points → `edit.json`
- `reel.html`: all visuals (hook slam, YEMỌJA reveal, Atlantic map, B&W quote card, Iemanjá = Yemọja, the call, ÀṢẸ, end card)
- `sound.py`: places VO, ducks the carnival bed, muffles it in the emotional section, synthesizes risers/booms/ripples/heartbeat/pad
- `render.js`: `START_FRAME/END_FRAME/OUT_NAME` for parallel workers
- `vo/script.md`: the voiceover lines + fact-check notes

Base frames: crop the source below its headline band (`crop=720:920:0:359`), upscale to 1499x1920, crop 1080 wide
(x=150), grade; then a 9 s minterpolate slow-motion replay of the goddess (src 3–12 s at 0.5x) for the closing call.
