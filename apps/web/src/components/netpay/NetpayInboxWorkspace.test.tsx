import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { NetpayApiClient, NetpayApiError, type NetpayCase, type NetpayClient } from '../../api/netpay';
import { NetpayCaseDetail, NetpayInboxWorkspace } from './NetpayInboxWorkspace';

const runtime = (manage = true) => ({ baseUrl: 'http://api.test', subject: 'operator:test', organizationSelector: 'org-1', organizationLabel: 'Organización de prueba', authToken: 'test-token', capabilities: new Set(manage ? ['netpay.inbox.read', 'netpay.inbox.manage', 'netpay.master.read', 'netpay.master.manage'] : ['netpay.inbox.read']) });
const master: NetpayClient = { id: 'client-1', display_name: 'Cliente Uno', external_reference: null, primary_contact_name: null, primary_email: null, primary_phone: null, status: 'active', created_at: '2026-08-14T00:00:00Z', updated_at: '2026-08-14T00:00:00Z', companies: [{ id: 'company-1', client_id: 'client-1', legal_name: 'Empresa Uno', tax_identifier: null, status: 'active', created_at: '2026-08-14T00:00:00Z', updated_at: '2026-08-14T00:00:00Z', branches: [{ id: 'branch-1', company_id: 'company-1', commercial_name: 'Sucursal Centro', branch_kind: 'physical', address: null, locality: null, state: null, postal_code: null, status: 'active', created_at: '2026-08-14T00:00:00Z', updated_at: '2026-08-14T00:00:00Z', store_reference: { id: 'store-ref-1', store_id: 'STORE-9', source_type: 'manual', source_reference: null, assigned_at: '2026-08-14T00:00:00Z', confirmed_at: null, active: true } }] }] };
const inboxCase: NetpayCase = { id: 'case-1', folio: 'NPS-0001', client_id: 'client-1', company_id: 'company-1', branch_id: 'branch-1', store_reference_id: 'store-ref-1', case_type_key: 'branch_onboarding', original_description: 'Abrir nueva sucursal', expected_outcome: 'Sucursal activa', product: 'tpv', state: 'blocked', priority: 'high', responsible_principal_id: null, target_date: '2026-08-20T00:00:00Z', source_channel: 'manual', source_reference: null, checklist_template_version: 1, created_at: '2026-08-14T00:00:00Z', updated_at: '2026-08-14T00:00:00Z', requires_attention: true, checklist: [{ id: 'check-1', requirement_key: 'legal_data', status: 'missing', required: true, safe_evidence_reference: null, template_version: 1 }], steps: [{ id: 'step-1', ordinal: 1, description: 'Validar solicitud', status: 'pending' }], next_actions: [{ id: 'action-1', description: 'Solicitar documentos', status: 'open', responsible_principal_id: null, due_date: '2020-01-01T00:00:00Z', origin: 'human' }], activities: [{ id: 'activity-1', type: 'created', summary: 'Caso creado', created_at: '2026-08-14T00:00:00Z' }], document_references: [{ id: 'doc-1', status: 'pending', external_evidence_reference: 'SAFE-1' }] };

function configuredClient(manage = true) {
  const client = new NetpayApiClient(runtime(manage));
  vi.spyOn(client, 'listInbox').mockResolvedValue({ items: [], offset: 0, limit: 20, total: 0 });
  return client;
}

describe('Netpay Inbox workspace', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('renders loading, empty and recoverable error states', async () => {
    const client = configuredClient();
    const pending = new Promise<never>(() => undefined);
    vi.mocked(client.listInbox).mockReturnValueOnce(pending);
    const view = render(<MemoryRouter><NetpayInboxWorkspace client={client} /></MemoryRouter>);
    expect(screen.getByRole('status').textContent).toMatch(/Cargando/);
    view.unmount();
    vi.mocked(client.listInbox).mockResolvedValueOnce({ items: [], offset: 0, limit: 20, total: 0 });
    render(<MemoryRouter><NetpayInboxWorkspace client={client} /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /Inbox vacío/i })).toBeTruthy();
    vi.mocked(client.listInbox).mockRejectedValueOnce(new Error('offline'));
    await userEvent.click(screen.getByRole('button', { name: /Aplicar/i }));
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeTruthy();
  });

  it('shows attention-first rows, hierarchy, filters and deterministic pagination', async () => {
    const client = configuredClient();
    vi.mocked(client.listInbox).mockResolvedValue({ items: [inboxCase], offset: 0, limit: 20, total: 21 });
    vi.spyOn(client, 'getMasterDetail').mockResolvedValue(master);
    render(<MemoryRouter><NetpayInboxWorkspace client={client} /></MemoryRouter>);
    expect(await screen.findByText('NPS-0001')).toBeTruthy();
    expect(await screen.findByText(/Empresa Uno → Sucursal Centro → STORE-9/)).toBeTruthy();
    expect(screen.getAllByText(/Requiere atención/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/Filtros/i)).toBeTruthy();
    expect(screen.getByText(/1–20 de 21/)).toBeTruthy();
    await userEvent.selectOptions(screen.getByLabelText('Estado'), 'blocked');
    await waitFor(() => expect(client.listInbox).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'blocked' })));
  });

  it('progressively creates Client, Company and Branch without Store ID and retains case key on retry', async () => {
    const client = configuredClient();
    vi.spyOn(client, 'createClient').mockResolvedValue({ ...master, companies: [] });
    vi.spyOn(client, 'createCompany').mockResolvedValue({ ...master.companies[0], branches: [] });
    vi.spyOn(client, 'createBranch').mockResolvedValue({ ...master.companies[0].branches[0], store_reference: null });
    vi.spyOn(client, 'setStoreReference');
    vi.spyOn(client, 'listMaster').mockResolvedValue({ items: [], offset: 0, limit: 100, total: 0 });
    vi.spyOn(client, 'createCase').mockRejectedValueOnce(new NetpayApiError(409, 'conflict', 'retry')).mockResolvedValueOnce(inboxCase);
    render(<MemoryRouter initialEntries={['/netpay-inbox']}><Routes><Route path="/netpay-inbox" element={<NetpayInboxWorkspace client={client} />} /><Route path="/netpay-inbox/:caseId" element={<p>Detalle creado</p>} /></Routes></MemoryRouter>);
    await screen.findByText(/Inbox vacío/i); const user = userEvent.setup(); await user.click(screen.getByRole('button', { name: /Nueva solicitud/i })); const dialog = within(screen.getByRole('dialog'));
    await user.type(dialog.getByLabelText('Cliente'), 'Cliente Uno'); await user.type(dialog.getByLabelText('Empresa'), 'Empresa Uno'); await user.type(dialog.getByLabelText('Sucursal'), 'Sucursal Centro');
    await user.click(screen.getByRole('button', { name: /Guardar maestro/i })); await screen.findByText(/paso 2/i); await user.type(screen.getByLabelText(/Descripción original/i), 'Abrir nueva sucursal'); await user.click(screen.getByRole('button', { name: /Revisar/i }));
    const submit = screen.getByRole('button', { name: /Crear caso/i }); fireEvent.click(submit); fireEvent.click(submit);
    expect(await screen.findByRole('alert')).toBeTruthy(); expect(client.createCase).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole('button', { name: /Crear caso/i })); await screen.findByText('Detalle creado');
    const firstKey = vi.mocked(client.createCase).mock.calls[0][1]; const secondKey = vi.mocked(client.createCase).mock.calls[1][1]; expect(firstKey).toBe(secondKey); expect(client.setStoreReference).not.toHaveBeenCalled();
  });

  it('renders case detail and invokes all five ratified B2 commands with idempotency', async () => {
    const client = configuredClient(); vi.spyOn(client, 'getCase').mockResolvedValue(inboxCase); vi.spyOn(client, 'getMasterDetail').mockResolvedValue(master);
    const methods = ['updateChecklist', 'assignCase', 'setNextAction', 'transitionCase', 'addActivity'] as const; methods.forEach((method) => vi.spyOn(client, method).mockResolvedValue(inboxCase));
    render(<MemoryRouter initialEntries={['/netpay-inbox/case-1']}><Routes><Route path="/netpay-inbox/:caseId" element={<NetpayCaseDetail client={client} />} /></Routes></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: 'Cliente Uno' })).toBeTruthy(); const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Confirmar' }));
    const assignee = screen.getByPlaceholderText(/UUID o vacío/i); await user.type(assignee, '11111111-1111-1111-1111-111111111111'); await user.click(screen.getByRole('button', { name: /Guardar asignación/i }));
    await user.type(screen.getByLabelText('Siguiente acción'), 'Llamar cliente');
    fireEvent.change(screen.getByLabelText('Fecha objetivo'), { target: { value: '2026-08-20T10:00' } });
    await user.click(screen.getByRole('button', { name: /Definir acción/i }));
    await user.selectOptions(screen.getByLabelText('Nuevo estado'), 'cancelled'); await user.type(screen.getByLabelText('Motivo'), 'Solicitud retirada'); await user.click(screen.getByRole('button', { name: /Cambiar estado/i }));
    await user.type(screen.getByLabelText('Nota interna'), 'Confirmación telefónica'); await user.click(screen.getByRole('button', { name: /Agregar actividad/i }));
    await waitFor(() => methods.forEach((method) => expect(client[method]).toHaveBeenCalled())); methods.forEach((method) => expect(vi.mocked(client[method]).mock.calls[0].at(-1)).toMatch(/.+/));
    expect(client.setNextAction).toHaveBeenCalledWith('case-1', expect.objectContaining({ due_date: '2026-08-20T10:00:00.000Z' }), expect.any(String));
  });

  it('keeps viewers read-only and exposes no mutation controls', async () => {
    const client = configuredClient(false); vi.spyOn(client, 'getCase').mockResolvedValue(inboxCase); vi.spyOn(client, 'getMasterDetail').mockResolvedValue(master);
    render(<MemoryRouter initialEntries={['/netpay-inbox/case-1']}><Routes><Route path="/netpay-inbox/:caseId" element={<NetpayCaseDetail client={client} />} /></Routes></MemoryRouter>);
    expect(await screen.findByText(/Vista de sólo lectura/i)).toBeTruthy(); expect(screen.queryByRole('button', { name: /Guardar asignación/i })).toBeNull();
  });
});

describe('typed Netpay API client', () => {
  it.each([[403, 'forbidden'], [404, 'not_found'], [409, 'conflict']])('maps HTTP %i safely', async (status, kind) => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status, json: async () => ({ detail: 'safe error' }) } as Response);
    const client = new NetpayApiClient(runtime());
    await expect(client.getCase('case-1')).rejects.toMatchObject({ kind });
    expect(fetchMock).toHaveBeenCalledWith('http://api.test/netpay/inbox/cases/case-1', expect.objectContaining({ headers: expect.objectContaining({ 'X-Yarvis-Subject': 'operator:test', 'X-Yarvis-Organization-Selector': 'org-1' }) }));
  });
});
