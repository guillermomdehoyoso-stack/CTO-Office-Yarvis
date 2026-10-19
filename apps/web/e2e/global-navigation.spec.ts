import { expect, test } from '@playwright/test';

test('global navigation prioritizes Netpay and keeps Gmail one click away', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\/netpay-inbox$/);

  const nav = page.getByRole('navigation', { name: 'Navegaci\u00f3n principal' });
  await expect(nav.getByRole('link', { name: 'Operaci\u00f3n Netpay' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Solicitudes Gmail' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Datos Netpay' })).toBeVisible();
  await expect(nav.getByText('Mission Work')).not.toBeVisible();

  const more = nav.getByText('M\u00e1s');
  await more.focus();
  await page.keyboard.press('Enter');
  await expect(nav.getByRole('link', { name: 'Mission Work' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Mission Control' })).toHaveAttribute('href', '/mission-control');

  const navBox = await nav.boundingBox();
  const menuBox = await nav.locator('.global-nav-more > div').boundingBox();
  expect(navBox).not.toBeNull();
  expect(menuBox).not.toBeNull();
  expect(navBox!.x + navBox!.width).toBeLessThanOrEqual(
    await page.evaluate(() => document.documentElement.clientWidth),
  );
  expect(menuBox!.x).toBeGreaterThanOrEqual(0);
  expect(menuBox!.x + menuBox!.width).toBeLessThanOrEqual(
    await page.evaluate(() => document.documentElement.clientWidth),
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    await page.evaluate(() => document.documentElement.clientWidth),
  );

  await nav.getByRole('link', { name: 'Mission Control' }).click();
  await expect(page).toHaveURL(/\/mission-control$/);

  await page.goto('/');
  await expect(page).toHaveURL(/\/netpay-inbox$/);
  await nav.getByRole('link', { name: 'Solicitudes Gmail' }).click();
  await expect(page).toHaveURL(/\/netpay-inbox\/gmail$/);
  await expect(nav.getByRole('link', { name: 'Solicitudes Gmail' })).toHaveClass(/global-nav-active/);
});
