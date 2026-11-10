// Ochiq loyihani yopadi (onlayn tizim avtomatik saqlaydi) va sinov papkasidagi loyihalar ro'yxatini qaytaradi.
export default async ({ page, drv }) => {
  await drv.closeProject();
  await page.waitForTimeout(3000);
  return drv.projects();
};
