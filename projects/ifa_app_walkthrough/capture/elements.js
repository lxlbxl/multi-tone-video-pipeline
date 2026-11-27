const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ ...devices['iPhone 14 Pro'] });
  const page = await ctx.newPage();
  await page.goto('https://ifa.ng/', { waitUntil: 'networkidle' });
  const ok = page.getByRole('button', { name: 'OK' }); if (await ok.count()) await ok.first().click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'el/hero_viewport.png' });
  // climb from a text node to the nearest "card-like" ancestor (has background or border radius) and screenshot it
  async function card(text, name, up = 6) {
    const loc = page.getByText(text, { exact: false }).first();
    await loc.scrollIntoViewIfNeeded(); await page.waitForTimeout(500);
    await page.evaluate(() => { for (const e of document.querySelectorAll('body *')) { const p = getComputedStyle(e).position; if (p === 'fixed' || p === 'sticky') e.style.visibility = 'hidden'; } });
    const h = await loc.evaluateHandle((el, up) => { let e = el; for (let i = 0; i < up && e.parentElement; i++) { const cs = getComputedStyle(e); if ((cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || parseFloat(cs.borderTopLeftRadius) > 10) && e.getBoundingClientRect().width > 200) return e; e = e.parentElement; } return e; }, up);
    await h.asElement().screenshot({ path: `el/${name}.png` }); console.log('ok', name);
  }
  await card("Tell us what's on your mind", 'step1');
  await card('Pick your Babalawo or Iyanifa', 'step2');
  await card('Meet on Google Meet', 'step3');
  await card('Keep your notes', 'step4');
  await card('Transcribing', 'meet_tile', 8);
  await card('Transcribing', 'sessions_combo', 11);
  await card('Session notes', 'notes_card', 8);
  await card('A new ẹsẹ Ifá each morning', 'daily_verse', 6).catch(e => console.log('verse miss'));
  await page.goto('https://ifa.ng/consult-online', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  for (const [t, n] of [['Verified practitioners', 'trust_verified'], ['Google Meet, nothing to install', 'trust_meet'], ['Written notes', 'trust_notes']]) await card(t, n).catch(e => console.log('miss', n));
  await page.goto('https://ifa.ng/odu', { waitUntil: 'networkidle' }); await page.waitForTimeout(800);
  for (const [t, n] of [['Èjì Ogbè', 'odu1'], ['Ọ̀yẹ̀kú Méjì', 'odu2'], ['Ìwòrì Méjì', 'odu3'], ['Òdí Méjì', 'odu4']]) await card(t, n).catch(e => console.log('miss', n));
  await browser.close();
})();
