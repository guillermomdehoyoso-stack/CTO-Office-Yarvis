import { expect, test, type Page } from '@playwright/test';
import path from 'node:path';

const fixtures = path.resolve('e2e/fixtures');

async function openImport(page: Page) {
  await page.goto('/netpay-data');
  await expect(page.getByRole('heading', { name: 'Datos Netpay' })).toBeVisible();
}

test.describe('D1 operational data browser evidence', () => {
  test('monthly profitability accepts, reloads, and replays idempotently', async ({ page }) => {
    await openImport(page);
    const file = path.join(fixtures, 'monthly-profitability.csv');
    await page.getByLabel('Archivo XLSX o CSV').setInputFiles(file);
    await page.getByRole('button', { name: 'Subir y validar' }).click();
    await expect(page.getByRole('heading', { name: 'Preview sanitizado' })).toBeVisible();
    await expect(page.getByText('***-001')).toBeVisible();
    await page.getByRole('button', { name: 'Confirmar e importar' }).click();
    await expect(page.getByText('Importado').first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Resultados normalizados' })).toBeVisible();
    await expect(page.getByText('2026-08', { exact: true }).first()).toBeVisible();

    await page.reload();
    await page.getByRole('button', { name: 'Historial de importaciones' }).click();
    await expect(page.getByText('Importado')).toHaveCount(1);
    await page.getByRole('button', { name: 'Importar XLSX' }).click();
    await page.getByLabel('Archivo XLSX o CSV').setInputFiles(file);
    await page.getByRole('button', { name: 'Subir y validar' }).click();
    await expect(page.getByText('Este archivo ya existe. Se recuperó el batch idempotente sin duplicarlo.')).toBeVisible();
    await page.getByRole('button', { name: 'Historial de importaciones' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(1);
  });

  test('No Uso filters RFC before preview, accepts, reloads, and replays idempotently', async ({ page }) => {
    await openImport(page);
    await page.getByLabel('Tipo de dataset').selectOption('no_usage_campaign');
    await page.getByLabel('RFC de distribuidor (filtro efímero)').fill('RFC-SYN-ALLOW');
    await page.getByLabel('Archivo XLSX o CSV').setInputFiles(path.join(fixtures, 'no-usage.csv'));
    await page.getByRole('button', { name: 'Subir y validar' }).click();
    await expect(page.getByRole('heading', { name: 'Preview sanitizado' })).toBeVisible();
    await expect(page.locator('article').filter({ hasText: 'Leídas' })).toContainText('2');
    await expect(page.locator('article').filter({ hasText: 'Autorizadas' })).toContainText('1');
    await expect(page.getByText('***-001')).toBeVisible();
    await expect(page.getByText('SYN-STORE-EXCLUDED')).toHaveCount(0);
    await page.getByRole('button', { name: 'Confirmar e importar' }).click();
    await expect(page.getByText('Importado').first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Resultados normalizados' })).toBeVisible();

    await page.reload();
    await page.getByRole('button', { name: 'Historial de importaciones' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(2);
    await page.getByRole('button', { name: 'Importar XLSX' }).click();
    await page.getByLabel('Tipo de dataset').selectOption('no_usage_campaign');
    await page.getByLabel('RFC de distribuidor (filtro efímero)').fill('RFC-SYN-ALLOW');
    await page.getByLabel('Archivo XLSX o CSV').setInputFiles(path.join(fixtures, 'no-usage.csv'));
    await page.getByRole('button', { name: 'Subir y validar' }).click();
    await expect(page.getByText('Este archivo ya existe. Se recuperó el batch idempotente sin duplicarlo.')).toBeVisible();
    await page.getByRole('button', { name: 'Historial de importaciones' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(2);
    await expect(page.getByText('RFC-SYN-EXCLUDED')).toHaveCount(0);
  });
});
