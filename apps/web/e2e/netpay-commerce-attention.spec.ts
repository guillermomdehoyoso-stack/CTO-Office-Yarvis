import { expect, test } from '@playwright/test';

test('IG-015 corrected amounts, period, settlement lineage and bank status remain read-only', async ({ page }) => {
  const methods:string[]=[];
  page.on('request',r=>{if(r.url().includes('/netpay/commerce-attention'))methods.push(r.method());});
  await page.route('**/netpay/commerce-attention?*', route=>route.fulfill({json:{items:[{...rows[0],p2:{...p2,metric_definition_version:'ap_aq_ar_v2',combined_benefit_mxn:'700.00',distributor_commission_mxn:'100.00',effective_commission_on_sales_percent:'10.00'}}],page:1,page_size:50,total:1,filtered_total:1,pages:1,p2_totals:{monthly_sales_mxn:'1000.00',combined_benefit_mxn:'700.00',distributor_commission_mxn:'100.00',effective_commission_on_sales_percent:'10.00',compatible_stores:1,excluded_stores:0,monetary_stores:1}}}));
  await page.route('**/netpay/commerce-attention/settlements?*',route=>route.fulfill({json:[{batch_id:'synthetic',reporting_period:'2026-09',net_reported:'11.00',positive:'13.00',negative:'-2.00',announced_payment_date:'2026-10-15',bank_status:'not_confirmed',unexplained_difference:null,movements:['Asesor','Distribuidor','Asociado 15'].map((entity,i)=>({entity_original:entity,store_id:i===2?null:'SYN-001',concept_original:'COMISION ORIGINAL',amount_signed:i===2?'-2':'6.5',source_sheet:'sheet1',source_row_number:8+i,source_hash:'a'.repeat(64),reasons:['concept_mapping_pending']}))}]}));
  await page.goto('/netpay-portfolio?period=2026-09');
  await expect(page.getByLabel('Periodo mensual')).toHaveValue('2026-09');
  await expect(page.getByLabel('Totales mensuales P2')).toContainText('Beneficio total combinado: $700.00');
  await expect(page.getByLabel('Totales mensuales P2')).toContainText('Comisión: $100.00');
  await page.getByRole('button',{name:'Ver liquidaciones'}).click();
  await expect(page.getByText('Asesor',{exact:true})).toBeVisible();
  await expect(page.getByText('Distribuidor',{exact:true})).toBeVisible();
  await expect(page.getByText('Asociado 15',{exact:true})).toBeVisible();
  await expect(page.getByText('Sin Store — sin asignar')).toBeVisible();
  await expect(page.getByText('Cobro bancario: No confirmado')).toBeVisible();
  expect(methods.every(m=>m==='GET')).toBeTruthy();
});

const p2 = { reporting_period:'2026-09',currency_code:'MXN',monthly_sales_mxn:1000,distributor_commission_mxn:-25,effective_commission_on_sales_percent:-2.5,percentage_status:'calculated',percentage_reason:null,source_fields:{monthly_sales_mxn:'Volumen',distributor_commission_mxn:'Rentabilidad'},source_batch_id:'00000000-0000-0000-0000-000000000099',precision_classification:'exact_decimal_source',freshness_at:'2026-10-19T12:00:00Z',quality:'qualified' };
const base = { client_id: '00000000-0000-0000-0000-000000000001', company_id: null, branch_id: null, store_reference_id: null, store_id: null, store_reference_count: 0, legal_name: null, branch_name: null, masked_rfc: '*********4XYZ', contact: { available: false, label: 'Contacto registrado', source_scope: null, name: null, email: null, phone: null, verification: 'not_available', updated_at: null }, reconciliation_status: 'exact_match', availability_reasons: [], source_badges: { master: true, cases_available: 0, linked_pre_master: 0, unlinked_records: null, d1: 'No incorporado en P0/P1', terminals: 'Sin fuente canónica autorizada' }, updated_at: '2026-10-19T12:00:00Z', p2 };
const rows = [
  { ...base, row_key: 'client:00000000-0000-0000-0000-000000000001', entity_scope: 'client', commerce_name: 'Comercio Sintético', availability_reasons: ['Sin Company', 'Sin Branch', 'Sin StoreReference'] },
  { ...base, row_key: 'client:00000000-0000-0000-0000-000000000002', client_id: '00000000-0000-0000-0000-000000000002', entity_scope: 'client', commerce_name: 'Cliente sin empresa', p2:{...p2,monthly_sales_mxn:0,effective_commission_on_sales_percent:null,percentage_status:'not_calculable',percentage_reason:'volume_zero'} },
  { ...base, row_key: 'company:00000000-0000-0000-0000-000000000003', entity_scope: 'company', commerce_name: 'Comercio empresa', company_id: '00000000-0000-0000-0000-000000000003', legal_name: 'Empresa sin sucursal' },
  { ...base, row_key: 'branch:00000000-0000-0000-0000-000000000004', entity_scope: 'branch', commerce_name: 'Comercio sucursal', company_id: '00000000-0000-0000-0000-000000000003', branch_id: '00000000-0000-0000-0000-000000000004', branch_name: 'Sucursal sin tienda' },
  { ...base, row_key: 'branch:00000000-0000-0000-0000-000000000005', entity_scope: 'branch', commerce_name: 'Comercio multi tienda', company_id: '00000000-0000-0000-0000-000000000003', branch_id: '00000000-0000-0000-0000-000000000005', branch_name: 'Sucursal multi', store_reference_id: '00000000-0000-0000-0000-000000000006', store_id: 'STORE-001', store_reference_count: 2, availability_reasons: ['2 StoreReferences'] },
];

test('portfolio list, filters, detail and back remain read-only', async ({ page }) => {
  const methods: string[] = [];
  page.on('request', (request) => { if (request.url().includes('/netpay/commerce-attention')) methods.push(request.method()); });
  await page.route('**/netpay/commerce-attention/**', async (route) => {
    const key = decodeURIComponent(new URL(route.request().url()).pathname.split('/').pop() || '');
    if (key === 'reconciliation') { await route.fulfill({json:{items:[],total:0}}); return; }
    await route.fulfill({ json: { ...rows[0], row_key: key, full_rfc: null, mid: 'MID no disponible', data_quality: rows[0].availability_reasons } });
  });
  await page.route('**/netpay/commerce-attention?*', async (route) => {
    const url = new URL(route.request().url()); const pageNumber = Number(url.searchParams.get('page') || '1'); const search = url.searchParams.get('search');
    const items = search ? [rows[0]] : pageNumber === 1 ? rows.slice(0, 4) : rows.slice(4);
    await route.fulfill({ json: { items, page: pageNumber, page_size: 50, total: 5, filtered_total: search ? 1 : 5, pages: search ? 1 : 2, p2_totals:{monthly_sales_mxn:1000,distributor_commission_mxn:-25,effective_commission_on_sales_percent:-2.5,percentage_status:'calculated',percentage_reason:null,compatible_stores:1,excluded_stores:4} } });
  });
  await page.goto('/netpay-portfolio');
  await expect(page.getByRole('heading', { name: 'Cartera operativa reportada' })).toBeVisible();
  await expect(page.getByText(/1 Stores incluidos/)).toBeVisible(); await expect(page.getByText(/4 excluidos/)).toBeVisible(); await expect(page.getByText('Comisión del distribuidor (MXN)')).toBeVisible(); await expect(page.getByText('Venta mensual igual a cero')).toBeVisible();
  await expect(page.getByText('Cliente sin empresa')).toBeVisible(); await expect(page.getByText('Empresa sin sucursal')).toBeVisible(); await expect(page.getByText('Sucursal sin tienda')).toBeVisible();
  await page.getByRole('button', { name: 'Siguiente' }).click(); await expect(page.getByText('Página 2 de 2')).toBeVisible(); await expect(page.getByText('2 StoreReferences')).toBeVisible();
  await page.getByLabel('Buscar cartera').fill('sintético'); await expect(page.getByText('Comercio Sintético')).toBeVisible();
  await page.getByLabel('Cliente').check(); await page.getByLabel('Orden').selectOption('updated_at'); await page.getByRole('button', { name: 'Ascendente' }).click();
  await page.getByRole('button', { name: 'Ver detalle' }).first().click(); await expect(page.getByText('Correo redactado o no disponible')).toBeVisible();
  await page.getByRole('link', { name: /Volver a cartera/ }).click(); await expect(page.getByLabel('Buscar cartera')).toHaveValue('sintético'); await expect(page.getByLabel('Cliente')).toBeChecked(); await expect(page.getByLabel('Orden')).toHaveValue('updated_at');
  await page.reload(); await expect(page.getByLabel('Buscar cartera')).toHaveValue(''); await expect(page.getByLabel('Cliente')).not.toBeChecked(); await expect(page.getByLabel('Orden')).toHaveValue('commerce'); await expect(page.getByText('Página 1 de 2')).toBeVisible();
  expect(methods.every((method) => method === 'GET')).toBeTruthy();
});

test('aggregate zero sales is explicitly not calculable', async ({ page }) => {
  await page.route('**/netpay/commerce-attention?*', (route) => route.fulfill({json:{items:[rows[0]],page:1,page_size:50,total:1,filtered_total:1,pages:1,p2_totals:{monthly_sales_mxn:0,distributor_commission_mxn:5,effective_commission_on_sales_percent:null,percentage_status:'not_calculable',percentage_reason:'aggregate_volume_zero',compatible_stores:2,excluded_stores:0}}}));
  await page.goto('/netpay-portfolio');
  await expect(page.getByLabel('Totales mensuales P2')).toContainText('Comisión efectiva: No calculable');
  await expect(page.getByText('Venta agregada igual a cero')).toBeVisible();
});

test('empty catalog, filtered result and access failures have distinct guidance', async ({ page }) => {
  await page.route('**/netpay/commerce-attention/reconciliation', route=>route.fulfill({json:{items:[],total:0}}));
  await page.route('**/netpay/commerce-attention?*', (route) => route.fulfill({json:{items:[],page:1,page_size:50,total:0,filtered_total:0,pages:1}}));
  await page.goto('/netpay-portfolio');
  await expect(page.getByRole('heading',{name:'Aún no hay comercios registrados'})).toBeVisible();
  await expect(page.getByText(/todavía no tiene registros Master/)).toBeVisible();

  await page.unroute('**/netpay/commerce-attention?*');
  await page.route('**/netpay/commerce-attention?*', (route) => route.fulfill({json:{items:[],page:1,page_size:50,total:5,filtered_total:0,pages:1}}));
  await page.getByLabel('Buscar cartera').fill('sin coincidencia');
  await expect(page.getByRole('heading',{name:'Sin resultados'})).toBeVisible();
  await expect(page.getByText('Ajusta o limpia los filtros activos.')).toBeVisible();

  await page.unroute('**/netpay/commerce-attention?*');
  await page.route('**/netpay/commerce-attention?*', (route) => route.fulfill({status:403,json:{detail:'permission denied'}}));
  await page.reload();
  await expect(page.getByRole('alert')).toHaveText('Tu identidad no tiene permiso para consultar la Cartera de esta organización.');
  await expect(page.getByText('permission denied')).toHaveCount(0);

  await page.unroute('**/netpay/commerce-attention?*');
  await page.route('**/netpay/commerce-attention?*', (route) => route.fulfill({status:401,json:{detail:'session expired'}}));
  await page.reload();
  await expect(page.getByRole('alert')).toHaveText('Tu sesión no está activa. Inicia sesión nuevamente para consultar la Cartera.');

  await page.unroute('**/netpay/commerce-attention?*');
  await page.route('**/netpay/commerce-attention?*', (route) => route.abort('connectionrefused'));
  await page.reload();
  await expect(page.getByRole('alert')).toHaveText('No fue posible cargar la cartera desde la API local.');
});
