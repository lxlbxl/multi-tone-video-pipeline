# Ìjúbà, a young voice: IG / TikTok reel edit

The girl's ìjúbà (homage chant), pulled out of a 3-part screen recording of an X post
(@yorubachic quoting @MooAkee, carrying a FAMSTARZZS watermark), then upscaled and edited for ifa.ng.
Credit the original posters in the post caption.

- `edit.json`: 11 homage sections (Olódùmarè, Ilẹ̀, Ayé, Ẹ̀là, Ọ̀rúnmìlà, Agbọnnìrègún, Ìyá mi, Èṣù, Ọbàtálá, Ọ̀ṣun, Ṣàngó), ÀṢẸ onsets, and caption lines
  `[start, end, text, [[word_start, word_end], …]]`. **Edit this** to correct captions.
- `vad.json` + `segtext.json`: the timing source. `vad.json` holds 113 voice-activity phrase segments measured from the audio, and `segtext.json` holds the Yoruba transcribed per segment.
  Captions, section starts and ÀṢẸ stamps all come from these, so they land on real phrase onsets.
- `reel.html`: overlays: header with 10-bead section tracker, deity title cards, karaoke captions,
  ÀṢẸ stamp on every "Àṣẹ", kinetic CTA band under the video (cycles Comment / Share / Follow / Save,
  switches to "Type ÀṢẸ 👇🏾" after each ÀṢẸ), hook, outro CTA, logo.
- `render.js`: `node render.js <dir> preview 13.3 70.5` / `node render.js <dir> full`
  (`START_FRAME` / `END_FRAME` / `OUT_NAME` env vars split the render across parallel workers).
- `mix_sfx.py <edit.json> <out.wav>`: synthesised pad + whooshes + ÀṢẸ chimes.

## Base frames (extract + upscale)

```bash
# parts a,b,c are consecutive; concat, then crop the embedded video (x164 y199 392x456, just above the watermark),
# patch the first 9s of on-video text with a flipped strip of roof, denoise, 2-stage lanczos + CAS sharpen to 1040x1210,
# grade, round corners, and set on a blurred backdrop at 1080x1920.
ffmpeg -f concat -safe 0 -i list.txt -c copy all.mp4
ffmpeg -i all.mp4 -i mask.png -i shadow.png -i ring.png -filter_complex "\
[0:v]crop=392:456:164:199,split[c0][c1];[c1]crop=392:16:0:16,vflip[patch];\
[c0][patch]overlay=0:0:enable='lt(t,9.1)',setsar=1,split=2[fgsrc][bgsrc];\
[fgsrc]hqdn3d=1.5:1.5:4:4,scale=784:912:flags=lanczos,cas=0.55,scale=1040:1210:flags=lanczos,unsharp=5:5:0.45,\
eq=contrast=1.05:saturation=1.10:gamma=0.98,colorbalance=rs=0.02:bs=-0.03:rm=0.015:bm=-0.02[fg];\
[fg][1:v]alphamerge[fga];[bgsrc]scale=1650:1920,crop=1080:1920,gblur=sigma=38,eq=brightness=-0.16:saturation=0.85[bg];\
[bg][2:v]overlay=0:0[bgs];[bgs][fga]overlay=20:276[b1];[b1][3:v]overlay=16:272,format=yuvj420p[out]" \
-map "[out]" -q:v 4 build/fr/%05d.jpg
```
