const { chromium, devices } = require('playwright');
(async () => {
  const out = process.argv[2], url = process.argv[3] || 'https://ifa.ng';
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'], ignoreHTTPSErrors: false });
  const page = await ctx.newPage();
  const fails = new Set();
  page.on('requestfailed', r => fails.add(new URL(r.url()).host));
  const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 }).catch(e => (console.log('goto error', e.message), null));
  console.log('status', resp && resp.status(), 'final url', page.url());
  await page.waitForTimeout(2500);
  console.log('title:', await page.title());
  await page.screenshot({ path: `${out}/00_home.png`, fullPage: false });
  await page.screenshot({ path: `${out}/00_home_full.png`, fullPage: true });
  const links = await page.$$eval('a,button', els => els.map(e => ({ tag: e.tagName, text: (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 60), href: e.getAttribute('href') })).filter(x => x.text || x.href));
  console.log(JSON.stringify(links.slice(0, 80), null, 0));
  console.log('blocked/failed hosts:', [...fails].join(', '));
  await browser.close();
})();
