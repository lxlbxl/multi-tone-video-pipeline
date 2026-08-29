"""
Multi-Style, Multi-Tone Script-to-Video Pipeline.

Config-driven. One engine serves every business, every visual style, every
tone, by loading a project config instead of hardcoding a character or a
voice. No video-generation model anywhere in this system: shots are stills
(GPT Image 2, reference-conditioned) animated procedurally with FFmpeg.

Module map (see the spec, section 9):

    config.py       load/resolve/validate project.json
    style_packs.py  build generation prompts, enforce the forbidden list
    characters.py   one-time character reference images, locked
    backgrounds.py  one-time background library, tagged, reusable
    tone.py         load a tone/brand profile
    narrative.py    shot-list schema, scaffold, and validator
    imagegen.py     reference-conditioned shot generation
    animate.py      Ken Burns / parallax / pose-crossfade, motion-scaled
    captions.py     kinetic captions (ASS) from word timings + caption_style
    render.py       composite, mux audio, optional disclaimer end-card
    cli.py          `python -m pipeline --project projects/<name>/project.json`

Supporting: util.py, kie.py (kie-cli + upload wrapper), tts.py, align.py,
music.py.
"""

__version__ = "1.0.0"
