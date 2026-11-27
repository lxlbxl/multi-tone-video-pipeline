const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  const media = await page.$$eval('video, img, picture source', els => els.slice(0, 12).map(e => ({ tag: e.tagName, src: e.currentSrc || e.src || e.srcset, w: e.naturalWidth || e.videoWidth, h: e.naturalHeight || e.videoHeight, top: Math.round(e.getBoundingClientRect().top), dur: e.duration || null })));
  console.log(JSON.stringify(media, null, 1));
  await browser.close();
})();
