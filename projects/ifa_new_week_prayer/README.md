# New Week Prayer: IG / TikTok reel edit

A rebranded edit of a Yoruba Ifá new-week prayer (ofò) clip for ifa.ng.
Credit the original creator (@only_one_ifablog) in the post caption.

- `edit.json`: Yoruba caption lines + timings, English section headings, òrìṣà callouts and pop stickers. **Edit this** to correct captions.
- `reel.html`: canvas compositor: jump-zoom punch-ins, frosted header + caption plate (these also cover the cleaned-up old text), karaoke captions, hook, stickers, ÀṢẸ outro, subtle logo.
- `render.js`: `node render.js <dir> preview 12.0 78.0` or `node render.js <dir> full`.
  `<dir>` must contain `reel.html`, `edit.json`, `logo.png` and `fr/` (cleaned frames).

## Rebuild

```bash
# 1. clean, grade and upscale source frames (removes old title, caption, TikTok watermark)
ffmpeg -i in.mp4 -vf "delogo=x=60:y=116:w=330:h=56,delogo=x=170:y=744:w=375:h=90,\
delogo=x=416:y=774:w=158:h=94,delogo=x=4:y=468:w=162:h=96:enable='lt(t,5.05)',\
eq=contrast=1.06:saturation=1.12:gamma=0.98,colorbalance=rs=0.03:gs=0.01:bs=-0.03:rm=0.02:bm=-0.02,\
scale=1080:1920:flags=lanczos,unsharp=5:5:0.6" -q:v 4 build/fr/%05d.jpg
# 2. render overlays + video
node render.js build full              # -> build/reel_noaudio.mp4
# 3. mux with the mixed audio (voice cleanup + pad + sfx, -14 LUFS)
```
