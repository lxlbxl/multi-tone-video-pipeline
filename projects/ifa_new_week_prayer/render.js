// usage: node render_reel.js <buildDir> preview|full [times...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
(async () => {
  const [dir, mode, ...ts] = process.argv.slice(2);
  const D = path.resolve(dir), FPS = 30, NFR = fs.readdirSync(path.join(D, 'fr')).length;
  const edit = JSON.parse(fs.readFileSync(path.join(D, 'edit.json')));
  const logo = 'data:image/png;base64,' + fs.readFileSync(path.join(D, 'logo.png')).toString('base64');
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(D, 'reel.html'));
  const TOT = await page.evaluate(([e, l]) => window.init(e, l), [edit, logo]);
  const frameURL = t => 'file://' + path.join(D, 'fr', String(Math.min(NFR, Math.floor(t * FPS) + 1)).padStart(5, '0') + '.jpg');
  const grab = async t => {
    await page.evaluate(u => window.setFrame(u), frameURL(t));
    const b64 = await page.evaluate(t => { window.drawFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93).split(',')[1]; }, t);
    return Buffer.from(b64, 'base64');
  };
  if (mode === 'preview') {
    for (const t of ts) fs.writeFileSync(path.join(D, `prev_${t}.jpg`), await grab(parseFloat(t)));
  } else {
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', path.join(D, 'reel_noaudio.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = Math.round(TOT * FPS);
    for (let i = 0; i < N; i++) {
      const buf = await grab(i / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 300 === 0) console.log(`frame ${i}/${N}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
