import { expect, test } from '@playwright/test';

test('shows an existing promoted intake without mutating business state', async ({ page }) => {
  const candidateId = process.env.NETPAY_CANDIDATE_ID;
  const intakeId = process.env.NETPAY_INTAKE_ID;
  if (!candidateId || !intakeId) throw new Error('NETPAY_CANDIDATE_ID and NETPAY_INTAKE_ID are required');

  const mutations: string[] = [];
  page.on('request', request => {
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method())) mutations.push(`${request.method()} ${request.url()}`);
  });

  await page.goto(`/netpay-inbox/gmail?candidate=${candidateId}`);
  await expect(page.getByRole('heading', { name: 'Ingreso comercial existente' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Abrir detalle del ingreso' })).toHaveAttribute(
    'href',
    `/netpay-inbox/contacts/${intakeId}`,
  );
  await expect(page.getByText('Destino asociado al candidato.')).toBeVisible();
  await expect(page.getByText('Siguiente acción guardada por el operador')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Revisar y corregir datos' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Seguimiento humano' })).toBeVisible();
  const dossier = page.getByRole('region', { name: 'Expediente de alta' });
  await expect(dossier.getByRole('heading', { name: 'Expediente de alta' })).toBeVisible();
  await expect(dossier.getByText(/Catálogo v1\.0\.0/)).toBeVisible();
  await expect(dossier).toContainText(/Productos:/i);
  await expect(dossier).toContainText(/TPV/i);
  await expect(dossier).toContainText(/Comercio electrónico/i);
  await expect(dossier).toContainText(/Sucursales:\s*5/);
  await expect(dossier.getByText(/no modifica la aceptación/i)).toBeVisible();
  await expect(dossier.getByRole('button', { name: 'Crear expediente de alta' })).toHaveCount(0);
  await expect(dossier.locator('.gmail-dossier-requirements button').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Decidir sobre la solicitud' })).toBeVisible();
  const result = page.locator('.gmail-decision-result');
  await expect(result.getByRole('heading', { name: 'Resultado registrado' })).toBeVisible();
  await expect(result.getByText('Aceptado', { exact: true })).toBeVisible();
  await expect(page.getByText('Fecha de decisión').locator('..')).not.toContainText('No reportada');
  await expect(page.getByRole('link', { name: 'Abrir destino aceptado' })).toHaveAttribute('href', `/netpay-inbox/contacts/${intakeId}`);
  await expect(page.getByText('Ver detalle del destino')).toBeVisible();
  for (const action of ['Aceptar', 'Rechazar', 'Marcar duplicado', 'Vincular']) {
    await expect(page.getByRole('button', { name: action, exact: true })).toBeDisabled();
  }
  const destination = page.locator('.gmail-decision-result .gmail-destination-summary');
  const destinationBox = await destination.boundingBox();
  expect(destinationBox).not.toBeNull();
  expect(destinationBox!.x + destinationBox!.width).toBeLessThanOrEqual(
    await page.evaluate(() => document.documentElement.clientWidth),
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    await page.evaluate(() => document.documentElement.clientWidth),
  );

  await page.reload();
  await expect(page.getByRole('heading', { name: 'Resultado registrado' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Expediente de alta' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Abrir destino aceptado' })).toHaveAttribute('href', `/netpay-inbox/contacts/${intakeId}`);
  await expect(page.getByRole('button', { name: 'Aceptar', exact: true })).toBeDisabled();
  expect(mutations).toEqual([]);
});
