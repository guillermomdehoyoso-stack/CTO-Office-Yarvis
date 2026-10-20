import { expect, test } from '@playwright/test';

const base = { client_id: '00000000-0000-0000-0000-000000000001', company_id: null, branch_id: null, store_reference_id: null, store_id: null, store_reference_count: 0, legal_name: null, branch_name: null, masked_rfc: '*********4XYZ', contact: { available: false, label: 'Contacto registrado', source_scope: null, name: null, email: null, phone: null, verification: 'not_available', updated_at: null }, reconciliation_status: 'exact_match', availability_reasons: [], source_badges: { master: true, cases_available: 0, linked_pre_master: 0, unlinked_records: null, d1: 'No incorporado en P0/P1', terminals: 'Sin fuente canónica autorizada' }, updated_at: '2026-10-19T12:00:00Z' };
const rows = [
  { ...base, row_key: 'client:00000000-0000-0000-0000-000000000001', entity_scope: 'client', commerce_name: 'Comercio Sintético', availability_reasons: ['Sin Company', 'Sin Branch', 'Sin StoreReference'] },
  { ...base, row_key: 'client:00000000-0000-0000-0000-000000000002', client_id: '00000000-0000-0000-0000-000000000002', entity_scope: 'client', commerce_name: 'Cliente sin empresa' },
  { ...base, row_key: 'company:00000000-0000-0000-0000-000000000003', entity_scope: 'company', commerce_name: 'Comercio empresa', company_id: '00000000-0000-0000-0000-000000000003', legal_name: 'Empresa sin sucursal' },
  { ...base, row_key: 'branch:00000000-0000-0000-0000-000000000004', entity_scope: 'branch', commerce_name: 'Comercio sucursal', company_id: '00000000-0000-0000-0000-000000000003', branch_id: '00000000-0000-0000-0000-000000000004', branch_name: 'Sucursal sin tienda' },
  { ...base, row_key: 'branch:00000000-0000-0000-0000-000000000005', entity_scope: 'branch', commerce_name: 'Comercio multi tienda', company_id: '00000000-0000-0000-0000-000000000003', branch_id: '00000000-0000-0000-0000-000000000005', branch_name: 'Sucursal multi', store_reference_id: '00000000-0000-0000-0000-000000000006', store_id: 'STORE-001', store_reference_count: 2, availability_reasons: ['2 StoreReferences'] },
];

test('portfolio list, filters, detail and back remain read-only', async ({ page }) => {
  const methods: string[] = [];
  page.on('request', (request) => { if (request.url().includes('/netpay/commerce-attention')) methods.push(request.method()); });
  await page.route('**/netpay/commerce-attention/**', async (route) => {
    const key = decodeURIComponent(new URL(route.request().url()).pathname.split('/').pop() || '');
    await route.fulfill({ json: { ...rows[0], row_key: key, full_rfc: null, mid: 'MID no disponible', data_quality: rows[0].availability_reasons } });
  });
  await page.route('**/netpay/commerce-attention?*', async (route) => {
    const url = new URL(route.request().url()); const pageNumber = Number(url.searchParams.get('page') || '1'); const search = url.searchParams.get('search');
    const items = search ? [rows[0]] : pageNumber === 1 ? rows.slice(0, 4) : rows.slice(4);
    await route.fulfill({ json: { items, page: pageNumber, page_size: 50, total: 5, filtered_total: search ? 1 : 5, pages: search ? 1 : 2 } });
  });
  await page.goto('/netpay-portfolio');
  await expect(page.getByRole('heading', { name: 'Cartera operativa reportada' })).toBeVisible();
  await expect(page.getByText('Cliente sin empresa')).toBeVisible(); await expect(page.getByText('Empresa sin sucursal')).toBeVisible(); await expect(page.getByText('Sucursal sin tienda')).toBeVisible();
  await page.getByRole('button', { name: 'Siguiente' }).click(); await expect(page.getByText('Página 2 de 2')).toBeVisible(); await expect(page.getByText('2 StoreReferences')).toBeVisible();
  await page.getByLabel('Buscar cartera').fill('sintético'); await expect(page.getByText('Comercio Sintético')).toBeVisible();
  await page.getByLabel('Cliente').check(); await page.getByLabel('Orden').selectOption('updated_at'); await page.getByRole('button', { name: 'Ascendente' }).click();
  await page.getByRole('button', { name: 'Ver detalle' }).first().click(); await expect(page.getByText('Correo redactado o no disponible')).toBeVisible();
  await page.getByRole('link', { name: /Volver a cartera/ }).click(); await expect(page.getByLabel('Buscar cartera')).toHaveValue('sintético'); await expect(page.getByLabel('Cliente')).toBeChecked(); await expect(page.getByLabel('Orden')).toHaveValue('updated_at');
  await page.reload(); await expect(page.getByLabel('Buscar cartera')).toHaveValue(''); await expect(page.getByLabel('Cliente')).not.toBeChecked(); await expect(page.getByLabel('Orden')).toHaveValue('commerce'); await expect(page.getByText('Página 1 de 2')).toBeVisible();
  expect(methods.every((method) => method === 'GET')).toBeTruthy();
});
