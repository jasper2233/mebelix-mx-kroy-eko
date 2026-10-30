export default async ({ page, drv }) => { await drv.closeProject(); await page.waitForTimeout(2000); return "closed"; };
