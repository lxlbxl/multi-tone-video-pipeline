# Ifá o jíire: animated lyric video

A 9:16 lyric video for a Yoruba Ifá song, drawn procedurally on an HTML canvas
(no image-generation model) and rendered frame by frame with Playwright + FFmpeg.

- `lyrics.json`: Yoruba lines, English translations and timings. **Edit this** to correct lyrics.
- `env.json`: per-frame audio envelope (rms / low / flux @ 30 fps) that drives the beat-reactive light.
- `scene.html`: the scenes (Ọpọ́n Ifá, Ọ̀rúnmìlà, Adé, Òpè, Àparò), the òrìṣà medallion ring and the kinetic lyrics.
- `assets/logo.png`: the brand mark with its background removed (shown small in the top-right corner, plus an end sign-off).

## Render

```bash
cd projects/ifa_o_jiire
node render.js . preview 3.2 24.5          # stills -> output/prev_*.jpg
node render.js . full                      # -> output/video_noaudio.mp4 (~3 min)
ffmpeg -i output/video_noaudio.mp4 -i <song.wav> -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 192k -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=62.4:d=3.5" -shortest -movflags +faststart \
  output/ifa_o_jiire_lyric_video.mp4
```

The source song is not committed; extract it from the original clip with
`ffmpeg -i <clip.mp4> -vn -ac 2 -ar 44100 song.wav`.
