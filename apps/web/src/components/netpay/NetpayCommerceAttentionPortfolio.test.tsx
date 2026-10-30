import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NetpayApiClient, type PortfolioRow } from '../../api/netpay';
import { NetpayCommerceAttentionDetail, NetpayCommerceAttentionPortfolio } from './NetpayCommerceAttentionPortfolio';

const row: PortfolioRow = {
  row_key:'branch:00000000-0000-0000-0000-000000000001', entity_scope:'branch', client_id:'client-1', company_id:'company-1', branch_id:'branch-1', store_reference_id:null, store_id:null, store_reference_count:0,
  commerce_name:'Comercio Sintético', legal_name:null, branch_name:'Sucursal Centro', masked_rfc:'*********4XYZ', contact:{available:false,label:'Contacto registrado',source_scope:null,name:null,email:null,phone:null,verification:'not_available',updated_at:null}, reconciliation_status:'exact_match', availability_reasons:['Sin StoreReference','Contacto no disponible'], source_badges:{master:true,cases_available:0,linked_pre_master:0,unlinked_records:null,d1:'No incorporado en P0/P1',terminals:'Sin fuente canónica autorizada'}, updated_at:'2026-10-19T12:00:00Z', p2:{reporting_period:'2026-09',currency_code:'MXN',monthly_sales_mxn:1000,distributor_commission_mxn:-25,effective_commission_on_sales_percent:-2.5,percentage_status:'calculated',percentage_reason:null,source_fields:{monthly_sales_mxn:'Volumen',distributor_commission_mxn:'Rentabilidad'},source_batch_id:'batch-1',precision_classification:'exact_decimal_source',freshness_at:'2026-10-19T12:00:00Z',quality:'qualified'},
};

function configured() {
  const client = new NetpayApiClient({baseUrl:'http://api.test',organizationLabel:'Sintética',capabilities:new Set(['netpay.portfolio.read'])});
  vi.spyOn(client,'listCommerceAttention').mockResolvedValue({items:[row],page:1,page_size:50,total:1,filtered_total:1,pages:1,p2_totals:{monthly_sales_mxn:1000,distributor_commission_mxn:-25,effective_commission_on_sales_percent:-2.5,percentage_status:'calculated',percentage_reason:null,compatible_stores:1,excluded_stores:0}});
  vi.spyOn(client,'getCommerceAttentionDetail').mockResolvedValue({...row,full_rfc:null,mid:'MID no disponible',data_quality:row.availability_reasons});
  vi.spyOn(client,'listCommerceAttentionReconciliation').mockResolvedValue({items:[],total:0});
  return client;
}

describe('Cartera operativa reportada', () => {
  it('renders Decimal strings and legacy commission absence without displaying AS as commission', async () => {
    const client=configured();
    vi.mocked(client.listCommerceAttention).mockResolvedValue({items:[{...row,p2:{...row.p2!,monthly_sales_mxn:'1000',combined_benefit_mxn:'700',distributor_commission_mxn:null,effective_commission_on_sales_percent:null,quality:'pending_reprocessing',metric_definition_version:'legacy_as_v1',percentage_reason:'commission_components_unavailable'}}],page:1,page_size:50,total:1,filtered_total:1,pages:1});
    render(<MemoryRouter initialEntries={['/netpay-portfolio?period=2026-09']}><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    expect(await screen.findByText(/Histórico v1: comisión corregida pendiente/)).toBeTruthy();
    expect(screen.getByText('No calculable')).toBeTruthy();
    expect(client.listCommerceAttention).toHaveBeenCalledWith(expect.objectContaining({reporting_period:'2026-09'}));
  });
  it('keeps settlement entities and unassigned charges visible without claiming bank payment', async () => {
    const client=configured(); vi.spyOn(client,'can').mockImplementation(scope=>scope==='netpay.portfolio.reconciliation.read');
    vi.spyOn(client,'listCommissionSettlements').mockResolvedValue([{batch_id:'settlement',reporting_period:'2026-09',currency_code:'MXN',net_reported:'11.00',positive:'13.00',negative:'-2.00',announced_payment_date:'2026-10-15',bank_status:'not_confirmed',unexplained_difference:null,difference_reason:'concept_and_entity_mapping_pending',movements:['Asesor','Distribuidor','Asociado 15'].map((entity,i)=>({source_row_number:i+8,source_sheet:'sheet1',source_hash:'a'.repeat(64),entity_original:entity,store_id:i===2?null:'SYN-001',concept_original:'Concepto original',amount_signed:i===2?'-2':'6.5',reasons:['concept_mapping_pending']}))}]);
    render(<MemoryRouter><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    await userEvent.click(screen.getByRole('button',{name:'Ver liquidaciones'}));
    expect(await screen.findByText('Asociado 15')).toBeTruthy();
    expect(screen.getByText('Asesor')).toBeTruthy(); expect(screen.getByText('Distribuidor')).toBeTruthy();
    expect(screen.getByText('Sin Store — sin asignar')).toBeTruthy();
    expect(screen.getByText('Cobro bancario: No confirmado')).toBeTruthy();
    expect(screen.getByText(/correspondencia de conceptos y entidades pendiente/)).toBeTruthy();
    expect(client.listCommissionSettlements).toHaveBeenCalledWith('',true);
  });
  beforeEach(()=>{ vi.restoreAllMocks(); });
  it('renders minimized rows, filters, columns and empty-state labels', async () => {
    const client=configured(); render(<MemoryRouter><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    expect(await screen.findByText('Comercio Sintético')).toBeTruthy(); expect(screen.getByText('Sin razón social registrada')).toBeTruthy(); expect(screen.getByText('Sin StoreReference')).toBeTruthy(); expect(screen.getByText('Contacto no disponible')).toBeTruthy(); expect(screen.getByText('MID no disponible')).toBeTruthy(); expect(screen.getByText('No incorporado en P0/P1')).toBeTruthy();
    expect(screen.getAllByText('-$25.00').length).toBeGreaterThan(0); expect(screen.getAllByText('-2.50%').length).toBeGreaterThan(0); expect(screen.getByText(/1 Stores incluidos/)).toBeTruthy();
    await userEvent.type(screen.getByLabelText('Buscar cartera'),'centro');
    await waitFor(()=>expect(client.listCommerceAttention).toHaveBeenLastCalledWith(expect.objectContaining({search:'centro'})));
    await userEvent.click(screen.getByText('Columnas')); expect(screen.getByLabelText('legal')).toBeTruthy();
  });
  it('opens detail and keeps sensitive data redacted without permission', async () => {
    const client=configured(); render(<MemoryRouter initialEntries={[`/netpay-portfolio/${encodeURIComponent(row.row_key)}`]}><Routes><Route path="/netpay-portfolio/:rowKey" element={<NetpayCommerceAttentionDetail client={client}/>}/></Routes></MemoryRouter>);
    expect(await screen.findByRole('heading',{name:'Comercio Sintético'})).toBeTruthy(); expect(screen.getByText(/RFC: \*+/)).toBeTruthy(); expect(screen.getByText('Correo redactado o no disponible')).toBeTruthy(); expect(client.getCommerceAttentionDetail).toHaveBeenCalledWith(row.row_key,false,'');
  });
  it('shows the separate queue only with reconciliation permission', async () => {
    const client=new NetpayApiClient({baseUrl:'http://api.test',organizationLabel:'Sintética',capabilities:new Set(['netpay.portfolio.read','netpay.portfolio.reconciliation.read'])});
    vi.spyOn(client,'listCommerceAttention').mockResolvedValue({items:[row],page:1,page_size:50,total:1,filtered_total:1,pages:1});
    vi.spyOn(client,'listCommerceAttentionReconciliation').mockResolvedValue({items:[{record_type:'candidate',record_id:'candidate-1',label_hint:'Candidato sintético',provenance:'synthetic-fixture',reconciliation_status:'unreconciled',reasons:['Sin vínculo canónico'],updated_at:'2026-10-19T12:00:00Z'}],total:1});
    render(<MemoryRouter><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    expect(await screen.findByRole('heading',{name:'Registros por conciliar'})).toBeTruthy();
    expect(await screen.findByText('Candidato sintético')).toBeTruthy();
    expect(screen.queryByText(/gmail/i)).toBeNull();
  });
  it('starts from defaults without persistent browser storage', async () => {
    const storage=vi.spyOn(Storage.prototype,'setItem'); const client=configured();
    render(<MemoryRouter><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    await screen.findByText('Comercio Sintético');
    expect((screen.getByLabelText('Buscar cartera') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('Orden') as HTMLSelectElement).value).toBe('commerce');
    expect(storage).not.toHaveBeenCalled();
  });
});
