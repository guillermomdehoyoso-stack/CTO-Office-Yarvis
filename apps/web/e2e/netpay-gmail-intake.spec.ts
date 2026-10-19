import { expect, test } from '@playwright/test';

test('Gmail Intake reloads persisted source evidence and keeps external mutations absent', async ({ page }) => {
  await page.goto('/netpay-inbox/gmail');
  await expect(page.getByRole('heading', { name: 'Gmail Intake Netpay' })).toBeVisible();
  await expect(page.getByText('pilot@example.invalid')).toBeVisible();
  await expect(page.getByText(/Última ejecución/)).toBeVisible();
  await page.getByRole('button', { name: /00199130/ }).click();
  await expect(page.getByRole('heading', { name: 'Hechos observados' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Inferencias' })).toBeVisible();
  await page.getByText('Evidencia de origen y adjuntos').click();
  await expect(page.getByText(/synthetic-browser-message-001/)).toBeVisible();
  await expect(page.getByText(/synthetic-browser-thread-001/)).toBeVisible();
  await expect(page.getByText(/Seguimiento excedido/).first()).toBeVisible();

  await page.reload();
  await page.getByRole('button', { name: /00199130/ }).click();
  await page.getByText('Evidencia de origen y adjuntos').click();
  await expect(page.getByText(/synthetic-browser-message-001/)).toBeVisible();
  await page.getByText('Detalle técnico (JSON)').click();
  await expect(page.getByText(/reported_state_only/)).toBeVisible();
  await expect(page.getByRole('button', { name: /Enviar|Archivar|Borrar correo/i })).toHaveCount(0);
});

test('records one synthetic operator follow-up and reloads its chronology', async ({ page }) => {
  await page.goto('/netpay-inbox/gmail');
  await page.getByRole('button', { name: /00199130/ }).click();
  await expect(page.getByRole('heading', { name: 'Seguimiento humano' })).toBeVisible();
  await expect(page.getByText('Sin seguimiento humano registrado.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Revisar nota' })).toBeDisabled();
  await page.locator('.gmail-follow-ups select').selectOption('meeting');
  await page.getByLabel('Nota del operador').fill('Reunión sintética de seguimiento; resultado no confirmado.');
  await page.getByRole('button', { name: 'Revisar nota' }).click();
  await expect(page.getByRole('heading', { name: 'Revisa la nota exacta' })).toBeVisible();
  await page.getByRole('button', { name: 'Registrar seguimiento' }).click({ clickCount: 2 });
  await expect(page.getByRole('status')).toContainText('Seguimiento registrado y verificado');
  await expect(page.getByText('Reunión sintética de seguimiento; resultado no confirmado.')).toHaveCount(1);
  await page.reload();
  await page.getByRole('button', { name: /00199130/ }).click();
  await expect(page.getByText('Reunión sintética de seguimiento; resultado no confirmado.')).toHaveCount(1);
  await expect(page.getByText(/Reportado por operador/).first()).toBeVisible();
});
