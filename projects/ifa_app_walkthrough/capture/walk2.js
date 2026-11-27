const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  await page.goto('https://ifa.ng/search', { waitUntil: 'networkidle' });
  const av = page.getByRole('button', { name: /Available now/ });
  console.log('available pressed:', await av.getAttribute('aria-pressed'));
  await av.click(); await page.waitForTimeout(2000);
  await page.screenshot({ path: 'shots/03_search_all.png', fullPage: true });
  const cards = await page.$$eval('a[href*="/babalawo/"], a[href*="/b/"], a[href*="/practitioner"]', els => els.map(e => [e.getAttribute('href'), e.innerText.trim().replace(/\s+/g, ' ').slice(0, 80)]));
  console.log('cards:', JSON.stringify(cards.slice(0, 20)));
  console.log('body text:', (await page.innerText('main').catch(() => '')).replace(/\s+/g, ' ').slice(0, 600));
  for (const u of ['/auth', '/dashboard', '/babalawo/']) { await page.goto('https://ifa.ng' + u, { waitUntil: 'networkidle' }); await page.waitForTimeout(1200); const n = u.replace(/\W/g, '') || 'x'; await page.screenshot({ path: `shots/04_${n}.png`, fullPage: true }); console.log(u, '->', page.url(), '|', (await page.innerText('body')).replace(/\s+/g, ' ').slice(0, 300)); }
  await browser.close();
})();
