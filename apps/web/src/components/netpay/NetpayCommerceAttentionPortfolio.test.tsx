import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NetpayApiClient, type PortfolioRow } from '../../api/netpay';
import { NetpayCommerceAttentionDetail, NetpayCommerceAttentionPortfolio } from './NetpayCommerceAttentionPortfolio';

const row: PortfolioRow = {
  row_key:'branch:00000000-0000-0000-0000-000000000001', entity_scope:'branch', client_id:'client-1', company_id:'company-1', branch_id:'branch-1', store_reference_id:null, store_id:null, store_reference_count:0,
  commerce_name:'Comercio Sintético', legal_name:null, branch_name:'Sucursal Centro', masked_rfc:'*********4XYZ', contact:{available:false,label:'Contacto registrado',source_scope:null,name:null,email:null,phone:null,verification:'not_available',updated_at:null}, reconciliation_status:'exact_match', availability_reasons:['Sin StoreReference','Contacto no disponible'], source_badges:{master:true,cases_available:0,linked_pre_master:0,unlinked_records:null,d1:'No incorporado en P0/P1',terminals:'Sin fuente canónica autorizada'}, updated_at:'2026-10-19T12:00:00Z',
};

function configured() {
  const client = new NetpayApiClient({baseUrl:'http://api.test',organizationLabel:'Sintética',capabilities:new Set(['netpay.portfolio.read'])});
  vi.spyOn(client,'listCommerceAttention').mockResolvedValue({items:[row],page:1,page_size:50,total:1,filtered_total:1,pages:1});
  vi.spyOn(client,'getCommerceAttentionDetail').mockResolvedValue({...row,full_rfc:null,mid:'MID no disponible',data_quality:row.availability_reasons});
  vi.spyOn(client,'listCommerceAttentionReconciliation').mockResolvedValue({items:[],total:0});
  return client;
}

describe('Cartera operativa reportada', () => {
  beforeEach(()=>{ vi.restoreAllMocks(); });
  it('renders minimized rows, filters, columns and empty-state labels', async () => {
    const client=configured(); render(<MemoryRouter><NetpayCommerceAttentionPortfolio client={client}/></MemoryRouter>);
    expect(await screen.findByText('Comercio Sintético')).toBeTruthy(); expect(screen.getByText('Sin razón social registrada')).toBeTruthy(); expect(screen.getByText('Sin StoreReference')).toBeTruthy(); expect(screen.getByText('Contacto no disponible')).toBeTruthy(); expect(screen.getByText('MID no disponible')).toBeTruthy(); expect(screen.getByText('No incorporado en P0/P1')).toBeTruthy();
    await userEvent.type(screen.getByLabelText('Buscar cartera'),'centro');
    await waitFor(()=>expect(client.listCommerceAttention).toHaveBeenLastCalledWith(expect.objectContaining({search:'centro'})));
    await userEvent.click(screen.getByText('Columnas')); expect(screen.getByLabelText('legal')).toBeTruthy();
  });
  it('opens detail and keeps sensitive data redacted without permission', async () => {
    const client=configured(); render(<MemoryRouter initialEntries={[`/netpay-portfolio/${encodeURIComponent(row.row_key)}`]}><Routes><Route path="/netpay-portfolio/:rowKey" element={<NetpayCommerceAttentionDetail client={client}/>}/></Routes></MemoryRouter>);
    expect(await screen.findByRole('heading',{name:'Comercio Sintético'})).toBeTruthy(); expect(screen.getByText(/RFC: \*+/)).toBeTruthy(); expect(screen.getByText('Correo redactado o no disponible')).toBeTruthy(); expect(client.getCommerceAttentionDetail).toHaveBeenCalledWith(row.row_key,false);
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
