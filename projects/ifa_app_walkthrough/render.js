// usage: node render_app.js <buildDir> preview|full [times...]   env: START_FRAME END_FRAME OUT_NAME
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
(async () => {
  const [dir, mode, ...ts] = process.argv.slice(2);
  const D = path.resolve(dir), FPS = 30;
  const edit = JSON.parse(fs.readFileSync(path.join(D, 'edit.json')));
  const A = path.join(D, 'a');
  const assets = {};
  for (const f of fs.readdirSync(A)) { const k = f.replace(/\.(png|jpg)$/, ''); assets[k] = 'file://' + path.join(A, f); }
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(D, 'reel.html'));
  const TOT = await page.evaluate(([e, l, a]) => window.init(e, l, a), [edit, assets.logo, assets]);
  const HV = path.join(D, 'hv');
  const grab = async t => { const ht = await page.evaluate(t => window.heroTime ? window.heroTime(t) : -1, t);
    await page.evaluate(u => window.setHero && window.setHero(u), ht >= 0 ? 'file://' + path.join(HV, String(Math.min(540, Math.floor(ht * 30) + 1)).padStart(4, '0') + '.jpg') : null);
    return Buffer.from((await page.evaluate(t => { window.drawFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93).split(',')[1]; }, t)), 'base64'); };
  if (mode === 'preview') {
    for (const t of ts) fs.writeFileSync(path.join(D, `prev_${t}.jpg`), await grab(parseFloat(t)));
  } else {
    const out = path.join(D, process.env.OUT_NAME || 'video_noaudio.mp4');
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = Math.round(TOT * FPS), I0 = parseInt(process.env.START_FRAME || '0'), I1 = Math.min(N, parseInt(process.env.END_FRAME || String(N)));
    for (let i = I0; i < I1; i++) { const b = await grab(i / FPS); if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r)); if (i % 300 === 0) console.log(`frame ${i}/${N}`); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
