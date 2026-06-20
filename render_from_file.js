const puppeteer = require('puppeteer-core');
const path = require('path');

async function renderFromFile(htmlPath, outputPath) {
  const executablePath = process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/chromium';

  const browser = await puppeteer.launch({
    executablePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 850, height: 1200, deviceScaleFactor: 2 });

  const fileUrl = 'file://' + path.resolve(htmlPath);
  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 15000 });

  // Wait for fonts and images to load
  await new Promise(r => setTimeout(r, 2000));

  // Get actual content height
  const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
  await page.setViewport({ width: 850, height: bodyHeight, deviceScaleFactor: 2 });

  await page.screenshot({
    path: outputPath,
    fullPage: true,
    type: 'png',
  });

  await browser.close();
  console.log('Flyer rendered to:', outputPath);
}

const args = process.argv.slice(2);
if (args.length >= 2) {
  renderFromFile(args[0], args[1])
    .then(() => process.exit(0))
    .catch(err => { console.error(err); process.exit(1); });
} else {
  console.error('Usage: node render_from_file.js <html_path> <output_png>');
  process.exit(1);
}
