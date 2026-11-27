const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  await page.goto('https://ifa.ng/search', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  await page.getByText('Filters', { exact: true }).first().click(); await page.waitForTimeout(900);
  await page.screenshot({ path: 'seq/filters_open.png' });
  console.log('filters text:', (await page.innerText('main')).replace(/\s+/g, ' ').slice(300, 1100));
  await page.goto('https://ifa.ng/auth', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  const ph = page.getByPlaceholder(/Phone number/); await ph.click(); await page.screenshot({ path: 'seq/auth_00.png' }); let i = 1;
  for (const d of '2025550147') { await page.keyboard.type(d); await page.waitForTimeout(60); await page.screenshot({ path: `seq/auth_${String(i++).padStart(2, '0')}.png` }); }
  await browser.close();
})();
