const { chromium, devices } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  // FAQ answers
  const faq = {};
  for (const q of ['How do I book a consultation?', 'Are the Babalawos and Iyanifas verified?', 'Do I need to install anything?', 'Is my session recorded or transcribed?', 'Can I cancel?', 'How do I pay?']) {
    const b = page.getByRole('button', { name: q }); await b.click(); await page.waitForTimeout(400);
    faq[q] = await b.evaluate(el => { const p = el.closest('details,div,li'); return (p ? p.innerText : '').replace(/\s+/g, ' ').slice(0, 600); });
  }
  fs.writeFileSync('seq/faq.json', JSON.stringify(faq, null, 1));
  await page.getByRole('button', { name: 'How do I book a consultation?' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: 'seq/faq_open.png' });
  // search typing
  await page.goto('https://ifa.ng/search', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  const box = page.getByPlaceholder(/Name, specialty or location/);
  await box.click(); await page.screenshot({ path: 'seq/search_00.png' });
  const q = 'Ọ̀ṣun · Yoruba · Lagos'; let i = 1;
  for (const ch of ['Ọ̀','ṣ','u','n',' ','·',' ','Y','o','r','u','b','a']) { await page.keyboard.insertText(ch); await page.waitForTimeout(90); await page.screenshot({ path: `seq/search_${String(i++).padStart(2, '0')}.png` }); }
  await box.fill(''); await page.waitForTimeout(300);
  await page.getByRole('button', { name: /^Filters/ }).click(); await page.waitForTimeout(900);
  await page.screenshot({ path: 'seq/filters_open.png' }); await page.screenshot({ path: 'seq/filters_open_full.png', fullPage: true });
  console.log('filters text:', (await page.innerText('main')).replace(/\s+/g, ' ').slice(0, 900));
  // phone sign-in typing (not submitted)
  await page.goto('https://ifa.ng/auth', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  const ph = page.getByPlaceholder(/Phone number/); await ph.click(); await page.screenshot({ path: 'seq/auth_00.png' }); i = 1;
  for (const d of '2025550147') { await page.keyboard.type(d); await page.waitForTimeout(60); await page.screenshot({ path: `seq/auth_${String(i++).padStart(2, '0')}.png` }); }
  await browser.close();
})();
