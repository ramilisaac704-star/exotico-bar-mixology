// Renderiza la presentación de marca fotograma a fotograma. Uso: node marca.js <carpeta_salida> [segundos] [fps]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = process.argv[2], dur = parseFloat(process.argv[3] || '9'), fps = parseInt(process.argv[4] || '30');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'marca.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => render(t), i / fps);
    await p.screenshot({ path: path.join(out, `m${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 96 });
  }
  await b.close();
  console.log('fotogramas', n);
})();
