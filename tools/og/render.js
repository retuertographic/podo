// Genera assets/img/og-silvia-caceres-romano.jpg a partir de tools/og/og-image.html
// Uso: node tools/og/render.js   (requiere Playwright con Chromium)
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.goto('file://' + path.join(__dirname, 'og-image.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  const out = path.join(__dirname, '..', '..', 'assets', 'img', 'og-silvia-caceres-romano.jpg');
  await p.screenshot({ path: out, type: 'jpeg', quality: 88 });
  await b.close();
  console.log('Generada', out);
})();
