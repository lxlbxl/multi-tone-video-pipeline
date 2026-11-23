// usage: node render.js <buildDir> <mode: preview|full> [times...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
(async () => {
  const [dir, mode, ...ts] = process.argv.slice(2);
  const lyrics = JSON.parse(fs.readFileSync(path.join(dir, 'lyrics.json')));
  const env = JSON.parse(fs.readFileSync(path.join(dir, 'env.json')));
  const logo = 'data:image/png;base64,' + fs.readFileSync(path.join(dir, "assets", "logo.png")).toString('base64');
  const DUR = parseFloat(process.env.DUR || '65.98'), FPS = 30;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(dir, 'scene.html'));
  await page.evaluate(([l, e, g, d]) => window.init(l, e, g, d), [lyrics, env, logo, DUR]);
  const grab = async t => {
    const b64 = await page.evaluate(t => { window.drawFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.94).split(',')[1]; }, t);
    return Buffer.from(b64, 'base64');
  };
  if (mode === 'preview') {
    for (const t of ts) fs.writeFileSync(path.join(dir, "output", `prev_${t}.jpg`), await grab(parseFloat(t)));
  } else {
    const out = path.join(dir, "output", "video_noaudio.mp4");
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = Math.round(DUR * FPS);
    for (let i = 0; i < N; i++) {
      const buf = await grab(i / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`frame ${i}/${N}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
