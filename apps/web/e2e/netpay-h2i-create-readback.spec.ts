import { expect, test } from '@playwright/test';

test('operator previews, confirms and reads back one synthetic commercial intake', async ({ page }) => {
  const mutations: string[] = [];
  page.on('request', request => {
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method())) {
      mutations.push(`${request.method()} ${new URL(request.url()).pathname}`);
    }
  });

  await page.goto('/netpay-inbox/gmail');
  await page.getByRole('button', { name: /00199130/ }).click();
  await page.getByLabel('Persona moral observada').fill('Empresa Sintética');
  await page.getByLabel('Sucursales, una por línea').fill('Sucursal Uno\nSucursal Dos');
  await page.getByRole('button', { name: 'Revisar y guardar overlay' }).click();
  await page.getByRole('button', { name: 'Preparar ingreso comercial' }).click();
  await expect(page.getByRole('heading', { name: 'Revisión previa del ingreso comercial' })).toBeVisible();
  await expect(page.getByText('2 sucursales separadas.')).toBeVisible();
  expect(mutations.filter(path => path.includes('/commercial-intake'))).toHaveLength(0);

  await page.getByRole('button', { name: 'Confirmar creación del ingreso comercial' }).click();
  await expect(page.getByRole('heading', { name: 'Ingreso comercial existente' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: /00199130/ }).click();
  await expect(page.getByRole('heading', { name: 'Ingreso comercial existente' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Abrir detalle del ingreso' })).toHaveAttribute(
    'href', /\/netpay-inbox\/contacts\/[^/]+$/,
  );
  expect(mutations.filter(path => path.endsWith('/commercial-intake'))).toHaveLength(1);
  expect(mutations.filter(path => path.includes('/dossier'))).toHaveLength(0);
});
