const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  const shot = async (n) => { await page.waitForTimeout(1200); await page.screenshot({ path: `shots/${n}.png` }); await page.screenshot({ path: `shots/${n}_full.png`, fullPage: true }); console.log('shot', n, page.url()); };
  const links = async () => console.log(JSON.stringify((await page.$$eval('a,button', els => els.map(e => [(e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 50), e.getAttribute('href')]).filter(x => x[0]))).slice(0, 60)));
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  await shot('01_home');
  await page.goto('https://ifa.ng/search', { waitUntil: 'networkidle' }); await shot('02_search'); await links();
  await browser.close();
})();
