# perfume_short_fr — talking-head edit for IG Reels / YouTube Shorts

The speaker's own footage, re-edited (no generated imagery): 1080x1920, 24 fps, 88 s, -14 LUFS.

What the edit adds:
- **Hook** (first 2.5 s): "3 PARFUMS QUE VOUS NE CONNAISSEZ PAS".
- **Kinetic captions** in French (Anton): words pop in as they are spoken. The word being spoken turns yellow, and key words sit on a tilted box in the colour of the current product.
- **Text behind the subject**: PÉPITES, SPIRITUEL, DÉBLOCAGE, SECRET, MODERN OUD, DISCRET. The subject is cut out frame by frame (rembg isnet + u2net_human_seg) and pushed down about 250 px so the word fits on the wall behind him.
- **Product context**: a numbered product card (01 Jérusalem, 02 Déblocage, 03 Modern Oud), benefit chips that follow the speech (two on screen at most), and animated brackets with sparkles that follow each bottle when it is held to the camera.
- **Camera**: a slow push-in in each section, a small punch-in on emphasised words, and a zoom with a flash on each product change. Plus a colour grade, a vignette and a progress bar.
- **End card**: "LEQUEL EST POUR TOI ?" with 1/2/3 to comment, and a subscribe button.
- **Audio**: voice cleaned (high-pass, denoise, EQ, compression). A synthesised music bed is ducked under the voice, and synthesised effects (whoosh, boom, pop, shimmer, ding) mark each reveal. Loudness normalised to -14 LUFS, true peak -1 dBTP.

## Rebuild
```
# fonts/: Anton-Regular.ttf and Montserrat.ttf from github.com/google/fonts (ofl/)
python3 asr.py && python3 zf.py           # Whisper text + zipformer-fr word timings (sherpa-onnx)
python3 masks.py SRC.mp4                  # subject masks -> masks/ (every other frame)
python3 render.py SRC.mp4 video.mp4       # compositor (spec in edit_spec.py)
python3 audio.py SRC.mp4 audio.wav
ffmpeg -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out.mp4
```
All timings, words, colours and bottle tracks are in `edit_spec.py`.
