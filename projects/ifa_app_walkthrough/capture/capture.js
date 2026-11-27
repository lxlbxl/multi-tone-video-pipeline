const { chromium, devices } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  const out = {};
  for (const [name, url] of [['home', '/'], ['search', '/search'], ['auth', '/auth'], ['odu', '/odu'], ['learn', '/learn'], ['consult', '/consult-online'], ['orisha', '/orisha']]) {
    await page.goto('https://ifa.ng' + url, { waitUntil: 'networkidle' }); await page.waitForTimeout(1500);
    // let lazy content/animations settle by scrolling through
    const H = await page.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < H; y += 600) { await page.evaluate(y => window.scrollTo(0, y), y); await page.waitForTimeout(120); }
    await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(800);
    await page.screenshot({ path: `pages/${name}.png`, fullPage: true });
    // heading positions (CSS px) for cropping
    out[name] = await page.$$eval('h1,h2,h3', els => els.map(e => { const r = e.getBoundingClientRect(); return [e.innerText.trim().replace(/\s+/g, ' ').slice(0, 60), Math.round(r.top + scrollY), Math.round(r.height)]; }));
    console.log(name, H);
  }
  fs.writeFileSync('pages/headings.json', JSON.stringify(out, null, 1));
  await browser.close();
})();
