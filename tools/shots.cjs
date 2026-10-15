// node shots.cjs <baseUrl> <outDir> <projectName> — asosiy ekranlar skrinshotlari (hujjat va ko'rsatish uchun)
// Ishga tushirish: NODE_PATH=frontend/node_modules (Playwright), tizim Chrome; ilova ishlab turishi va
// «1 Behzod / 1230 Jamshid+Zafar» papkasida shu nomli loyiha bo'lishi kerak (yoki skriptdagi yo'lni moslang).
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const [base = 'http://127.0.0.1:8000', out = '.', pname = '04 shkaf'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch({ executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', headless: true });
  const ctx = await b.newContext({ viewport: { width: 1800, height: 1000 }, locale: 'ru-RU', deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('response', r => { if (r.status() >= 500) errors.push('HTTP ' + r.status() + ' ' + r.url()); });
  let n = 0;
  const shot = async (name) => { n++; await page.screenshot({ path: path.join(out, String(n).padStart(2, '0') + '_' + name + '.png') }); };
  const step = async (label, fn) => { try { await fn(); } catch (e) { console.log('SKIP ' + label + ': ' + String(e).split('\n')[0].slice(0, 160)); } };
  await page.goto(base); await page.waitForTimeout(1500);
  await shot('proyektlar_royxati_ildiz');
  await step('folder1', async () => { await page.getByText('1 Behzod', { exact: true }).first().dblclick(); await page.waitForTimeout(700); });
  await step('folder2', async () => { await page.getByText('1230 Jamshid+Zafar', { exact: true }).first().dblclick(); await page.waitForTimeout(900); });
  await shot('proyektlar_royxati');
  await step('open', async () => { await page.getByText(pname, { exact: true }).first().dblclick(); await page.waitForTimeout(2200); });
  await shot('loyiha_operatsiyalar');
  await step('params', async () => { await page.getByTestId('cs-tab-params').click(); await page.waitForTimeout(600); await shot('CS_parametrlar'); });
  await step('parts', async () => { await page.getByTestId('cs-tab-parts').click(); await page.waitForTimeout(600); await shot('CS_detallar'); });
  await step('sheets', async () => { await page.getByTestId('cs-tab-sheets').click(); await page.waitForTimeout(600); await shot('CS_listlar_qoldiqlar'); });
  await step('cut', async () => { await page.getByTestId('cs-tab-cut').click(); await page.waitForTimeout(1200); await shot('CS_raskroy_karta'); });
  await step('cmds', async () => { await page.getByText('Таблица команд').first().click(); await page.waitForTimeout(700); await shot('CS_buyruqlar_jadvali'); });
  await step('products', async () => { await page.getByTestId('tab-products').click(); await page.waitForTimeout(600); await shot('izdeliya'); });
  await step('props', async () => { await page.locator('div.ag-row').first().click(); await page.keyboard.press('Control+Space'); await page.waitForTimeout(600); await shot('izdeliya_xossalari'); await page.keyboard.press('Escape'); });
  await step('sort', async () => { await page.getByTitle('Сортировка').first().click(); await page.waitForTimeout(500); await shot('umumiy_saralash'); await page.keyboard.press('Escape'); });
  await step('ops', async () => { await page.getByTestId('tab-ops').click(); await page.waitForTimeout(400); });
  await step('el', async () => { await page.locator('[data-testid=ops-grid] .ag-row', { hasText: 'EL' }).first().click(); await page.waitForTimeout(800); await shot('EL_kromka'); });
  await step('xnc', async () => { await page.locator('[data-testid=ops-grid] .ag-row', { hasText: 'XNC' }).first().click(); await page.waitForTimeout(900); await shot('XNC_operatsiya'); });
  await step('common', async () => { await page.getByText('Общие действия').first().click(); await page.waitForTimeout(500); await shot('umumiy_amallar'); await page.keyboard.press('Escape'); });
  await step('print', async () => { await page.getByTestId('side-print').click(); await page.waitForTimeout(2500); await shot('hisobot_chop'); });
  await step('settings', async () => { await page.getByTestId('side-settings').click(); await page.waitForTimeout(600); await page.getByTestId('settings-pp').click(); await page.waitForTimeout(800); await shot('sozlamalar_postprotsessor'); });
  await step('remnants', async () => { await page.getByTestId('settings-remnants').click(); await page.waitForTimeout(800); await shot('sozlamalar_qoldiqlar_ombori'); });
  console.log('screens:', n, 'errors:', errors.length ? errors.join('\n') : 'none');
  await b.close();
})();
