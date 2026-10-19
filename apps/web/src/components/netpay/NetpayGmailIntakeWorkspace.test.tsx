import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NetpayApiClient, type GmailCandidate, type GmailConnection } from '../../api/netpay';
import { NetpayGmailIntakeWorkspace } from './NetpayGmailIntakeWorkspace';

const connection: GmailConnection = {
  id: 'connection-1', provider_account_id: 'pilot@example.invalid', provider_kind: 'google',
  label_id: 'Label_1', state: 'ready', last_sync_at: '2026-10-08T12:00:00Z',
  last_error_code: null, mailbox_verified_at: '2026-10-08T11:00:00Z', manifest_status: 'approved',
  manifest_entries: [], manifest_approved_at: '2026-10-08T11:30:00Z',
};
const candidate: GmailCandidate = {
  id: 'candidate-1', source_item_id: 'source-1', received_at: '2026-10-07T12:00:00Z',
  state: 'pending_link', request_type: 'consumable_shipment', product: 'not_applicable',
  description: 'Caso sintético 00199130', ticket_references: ['00199130'], commerce_hints: [],
  terminal_serials: [], shipment_facts: { carrier: 'FedEx', tracking_number: '878325984682' },
  facts: [{ field: 'ticket', value: '00199130' }],
  inferences: [{ field: 'shipment_interpretation', value: 'delivery remains unconfirmed' }],
  contradictions: [], missing_data: ['verified_commerce_identifier'], correlation_key: 'ticket:00199130',
  priority: 'normal', suggested_next_action: 'Vincular comercio', follow_up_at: '2026-10-06T12:00:00Z',
  follow_up_basis: 'derived_follow_up_threshold', explicit_deadline_at: null,
  confidence: 0.75, age_days: 1, overdue: true, related_candidate_ids: [], owner_type: null, owner_id: null,
  disposition_reason: null, reviewed_at: null, immutable: false,
};

function configuredClient() {
  const client = new NetpayApiClient({
    baseUrl: 'http://api.test', organizationLabel: 'Organización sintética',
    capabilities: new Set(['netpay.inbox.read', 'netpay.inbox.manage']),
  });
  vi.spyOn(client, 'listGmailConnections').mockResolvedValue([connection]);
  vi.spyOn(client, 'listGmailCandidates').mockResolvedValue({ items: [candidate], offset: 0, limit: 50, total: 1 });
  vi.spyOn(client, 'getGmailCandidate').mockResolvedValue(candidate);
  vi.spyOn(client, 'getGmailSourceItem').mockResolvedValue({ id: 'source-1', gmail_message_id: 'synthetic-message-1', gmail_thread_id: 'synthetic-thread-1', provider_received_at: '2026-10-07T12:00:00Z', sender: 'sender@example.invalid', recipient: 'netpay@example.invalid', subject: 'Caso sintético 00199130', plain_excerpt: 'Contenido sintético', attachment_metadata: [{ name: 'CSF_demo.pdf', mime_type: 'application/pdf', size: 1234 }], provenance: {} });
  vi.spyOn(client, 'syncGmailConnection').mockResolvedValue({ status: 'succeeded' });
  vi.spyOn(client, 'reviewGmailCandidate').mockResolvedValue({ ...candidate, state: 'rejected' });
  vi.spyOn(client, 'listCandidateFollowUps').mockResolvedValue({ items: [], offset: 0, limit: 50, total: 0 });
  vi.spyOn(client, 'recordCandidateFollowUp').mockResolvedValue({
    id: 'follow-up-1', candidate_id: candidate.id, kind: 'meeting', note: 'Synthetic operator follow-up.',
    provenance_kind: 'operator_reported', occurred_at: null, recorded_at: '2026-10-11T12:00:00Z',
    created_by_principal_id: 'principal-1', correlation_id: 'correlation-1',
  });
  vi.spyOn(client, 'listCommercialIntake').mockResolvedValue({ items: [], offset: 0, limit: 25, total: 0 });
  vi.spyOn(client, 'listCandidateQualifications').mockResolvedValue([]);
  vi.spyOn(client, 'createCandidateQualification').mockResolvedValue({ id: 'qualification-1', candidate_id: candidate.id, sequence: 1, payload: {}, provenance_kind: 'operator_reported', recorded_at: '2026-10-13T12:00:00Z', created_by_principal_id: 'principal-1' });
  vi.spyOn(client, 'previewCandidateCommercialIntake').mockResolvedValue({ candidate_id: candidate.id, qualification_id: 'qualification-1', provisional_company_name: 'Marca Sintética', provisional_contact_name: 'Persona Sintética', product_interest: 'mixed', summary: 'Alta sintética', priority: 'normal', next_action: 'Revisar', branches: [{ name: 'Sucursal Uno' }, { name: 'Sucursal Dos' }], provenance: { qualification: 'operator_reported' }, unresolved: [] });
  vi.spyOn(client, 'promoteCandidateCommercialIntake').mockResolvedValue({ trace_id: 'trace-1', commercial_intake_id: 'intake-1' });
  vi.spyOn(client, 'previewCandidateDossier').mockResolvedValue({
    existing: false, candidate_id: candidate.id, commercial_intake_id: 'intake-1',
    qualification_id: 'qualification-1', candidate_terminal: true, candidate_state: 'accepted',
    catalog_version: '1.0.0', catalog_effective_date: '2026-10-14',
    catalog_sha256: '4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b',
    catalog_owner: 'Guillermo De Hoyos', applicant_kind: 'persona_moral',
    products: ['tpv', 'ecommerce'],
    branches: Array.from({ length: 5 }, (_, index) => ({ name: `Sucursal ${index + 1}` })),
    requirements: [{ snapshot_key: 'client:bank_account_statement', key: 'bank_account_statement', label: 'Estado de cuenta bancario', scope: 'client', scope_key: 'client', required: true, maximum_age_days: 60, shareable: true, state: 'pending' }],
    blocker_count: 1, excluded: ['ecommerce_without_physical_location'],
  });
  vi.spyOn(client, 'createCandidateDossier').mockRejectedValue(new Error('not used'));
  return client;
}

describe('Netpay Gmail Intake workspace', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('shows connection health and reviewable facts separated from inferences', async () => {
    const client = configuredClient();
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    expect(await screen.findByText('pilot@example.invalid')).toBeTruthy();
    expect(screen.getByText(/Última ejecución/)).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Conectar Gmail' }) as HTMLButtonElement).disabled).toBe(true);
    await userEvent.click(screen.getByRole('button', { name: /00199130/ }));
    expect(screen.getByRole('heading', { name: 'Hechos observados' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Inferencias' })).toBeTruthy();
    expect(screen.getByText('Producto solicitado')).toBeTruthy();
    expect(screen.getByText('Solicitud recibida')).toBeTruthy();
    expect(screen.getByLabelText('Siguiente acción propuesta').tagName).toBe('TEXTAREA');
    expect(screen.getByText('Interpretación del envío')).toBeTruthy();
    expect(screen.getByText(/synthetic-message-1/)).toBeTruthy();
    expect(screen.getAllByText(/Seguimiento excedido/)).toHaveLength(2);
    expect(screen.getByText(/no es fecha límite/i)).toBeTruthy();
    expect(screen.getByText('Fecha límite explícita')).toBeTruthy();
    expect(screen.getByText('No reportada')).toBeTruthy();
    expect(screen.getByText('CSF_demo.pdf')).toBeTruthy();
    expect(screen.getByText(/application\/pdf · 1,234 bytes/)).toBeTruthy();
    expect(screen.getByText(/Sugerencia no verificada: Posible constancia/)).toBeTruthy();
  });

  it('runs a bounded manual sync and reloads persisted state', async () => {
    const client = configuredClient();
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: 'Sincronizar 30 días' }));
    await waitFor(() => expect(client.syncGmailConnection).toHaveBeenCalledWith('connection-1', expect.any(String)));
    expect(client.listGmailCandidates).toHaveBeenCalledTimes(2);
  });

  it('allows only one sync request while the first request is active', async () => {
    const client = configuredClient();
    let finishSync: (() => void) | undefined;
    vi.mocked(client.syncGmailConnection).mockImplementation(
      () => new Promise((resolve) => { finishSync = () => resolve({ status: 'succeeded' }); }),
    );
    const user = userEvent.setup();
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    const button = await screen.findByRole('button', { name: 'Sincronizar 30 días' });

    await user.click(button);
    expect(screen.queryByRole('button', { name: 'Sincronizar 30 días' })).toBeNull();
    expect(screen.getByRole('status').textContent).toContain('Cargando Gmail Intake');
    expect(client.syncGmailConnection).toHaveBeenCalledTimes(1);

    finishSync?.();
    await waitFor(() => expect(client.listGmailCandidates).toHaveBeenCalledTimes(2));
  });

  it('keeps mutation controls hidden from read-only viewers', async () => {
    const client = configuredClient();
    client.runtime.capabilities = new Set(['netpay.inbox.read']);
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await screen.findByText('pilot@example.invalid');
    expect(screen.queryByRole('button', { name: 'Conectar Gmail' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Sincronizar 30 días' })).toBeNull();
  });

  it('shows ten opaque manifest entries before approval', async () => {
    const client = configuredClient();
    const entries = Array.from({ length: 10 }, (_, index) => ({
      handle: `hmac-${index + 1}`,
      received_at: `2026-10-${String(index + 1).padStart(2, '0')}T12:00:00Z`,
    }));
    vi.mocked(client.listGmailConnections).mockResolvedValue([
      { ...connection, manifest_status: 'discovered', manifest_entries: entries, manifest_approved_at: null },
    ]);

    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);

    expect(await screen.findByRole('heading', { name: 'Manifiesto HMAC para revisión' })).toBeTruthy();
    expect(screen.getByText('10 entradas opacas. El descubrimiento no ingiere asunto, remitente ni contenido.')).toBeTruthy();
    expect(screen.getAllByText(/hmac-/)).toHaveLength(10);
    expect((screen.getByRole('button', { name: 'Aprobar 10 mensajes' }) as HTMLButtonElement).disabled).toBe(false);
  });

  it('reviews, records and reads back an append-only human follow-up', async () => {
    const client = configuredClient();
    const persisted = await client.recordCandidateFollowUp('candidate-1', {}, 'unused');
    vi.mocked(client.listCandidateFollowUps)
      .mockResolvedValueOnce({ items: [], offset: 0, limit: 50, total: 0 })
      .mockResolvedValue({ items: [persisted], offset: 0, limit: 50, total: 1 });
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    await userEvent.selectOptions(screen.getByLabelText('Tipo'), 'meeting');
    await userEvent.type(screen.getByLabelText('Nota del operador'), 'Synthetic operator follow-up.');
    await userEvent.click(screen.getByRole('button', { name: 'Revisar nota' }));
    expect(screen.getByRole('heading', { name: 'Revisa la nota exacta' })).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: 'Registrar seguimiento' }));
    await waitFor(() => expect(client.recordCandidateFollowUp).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Seguimiento registrado y verificado mediante lectura posterior.')).toBeTruthy();
    expect(screen.getAllByText(/Reportado por operador/).length).toBeGreaterThanOrEqual(1);
  });

  it('edits authorized candidate suggestions without changing source evidence', async () => {
    const client = configuredClient();
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    await userEvent.selectOptions(screen.getByLabelText('Tipo de solicitud'), 'new_branch');
    await userEvent.clear(screen.getByLabelText('Siguiente acción'));
    await userEvent.type(screen.getByLabelText('Siguiente acción'), 'Validar sucursales y documentos pendientes.');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar corrección' }));

    await waitFor(() => expect(client.reviewGmailCandidate).toHaveBeenCalledWith(
      'candidate-1',
      expect.objectContaining({
        action: 'edit', request_type: 'new_branch',
        suggested_next_action: 'Validar sucursales y documentos pendientes.',
      }),
      expect.any(String),
    ));
    expect(await screen.findByText(/La evidencia del correo no fue modificada/)).toBeTruthy();
  });

  it('searches same-tenant commercial intake and keeps acceptance blocked without a result', async () => {
    const client = configuredClient();
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    await userEvent.selectOptions(screen.getByLabelText('Tipo de registro destino'), 'commercial_intake');
    await userEvent.type(screen.getByLabelText('Buscar registro destino'), 'Marca Demo');
    await userEvent.click(screen.getByRole('button', { name: 'Buscar registros locales' }));

    await waitFor(() => expect(client.listCommercialIntake).toHaveBeenCalledWith({ query: 'Marca Demo', limit: 25 }));
    expect((screen.getByRole('button', { name: 'Aceptar' }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText('Ningún ID observado se selecciona automáticamente.')).toBeTruthy();
  });

  it('reads back the promoted intake and allows selecting it without another search or mutation', async () => {
    const client = configuredClient();
    vi.mocked(client.listCandidateQualifications).mockResolvedValue([{
      id: 'qualification-1', candidate_id: candidate.id, sequence: 1,
      payload: { applicant_kind: 'persona_moral', brand_name: { value: 'Marca Sintética' }, requested_products: ['tpv', 'ecommerce'], branches: [{ name: 'Sucursal Uno' }, { name: 'Sucursal Dos' }] },
      provenance_kind: 'operator_reported', recorded_at: '2026-10-13T12:00:00Z', created_by_principal_id: 'principal-1',
    }]);
    vi.mocked(client.previewCandidateCommercialIntake).mockResolvedValue({
      candidate_id: candidate.id, qualification_id: 'qualification-1', provisional_company_name: 'Marca Sintética', provisional_contact_name: null,
      product_interest: 'mixed', summary: 'Alta sintética', priority: 'normal', next_action: 'Vincular comercio', branches: [{ name: 'Sucursal Uno' }, { name: 'Sucursal Dos' }],
      provenance: { qualification: 'operator_reported' }, unresolved: [],
      promotion_trace: { id: 'trace-1', qualification_id: 'qualification-1', commercial_intake_id: 'intake-1', branch_drafts: [{ name: 'Sucursal Uno' }, { name: 'Sucursal Dos' }], created_at: '2026-10-13T13:00:00Z' },
      existing_intake: { id: 'intake-1', provisional_company_name: 'Marca Sintética', provisional_contact_name: null, product_interest: 'mixed', summary: 'Alta sintética', priority: 'normal', next_action: 'Vincular comercio', status: 'new' },
    });
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    expect(await screen.findByRole('heading', { name: 'Ingreso comercial existente' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Abrir detalle del ingreso' }).getAttribute('href')).toBe('/netpay-inbox/contacts/intake-1');
    expect(screen.getByText(/Ingreso comercial creado; falta decidir/)).toBeTruthy();
    expect(screen.getByText('Siguiente acción guardada por el operador')).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: 'Seleccionar este ingreso como destino' }));
    expect((screen.getByLabelText('Tipo de registro destino') as HTMLSelectElement).value).toBe('commercial_intake');
    expect((screen.getByLabelText('Registro destino verificado') as HTMLSelectElement).value).toBe('intake-1');
    expect(client.reviewGmailCandidate).not.toHaveBeenCalled();
    expect(client.listCommercialIntake).not.toHaveBeenCalled();
  });

  it('shows an immutable accepted result and disables incompatible decisions', async () => {
    const client = configuredClient();
    const accepted = { ...candidate, state: 'accepted', owner_type: 'commercial_intake', owner_id: 'intake-1', reviewed_at: '2026-10-14T05:42:37Z', immutable: true };
    vi.mocked(client.getGmailCandidate).mockResolvedValue(accepted);
    vi.mocked(client.listCandidateQualifications).mockResolvedValue([{
      id: 'qualification-1', candidate_id: candidate.id, sequence: 4,
      payload: { applicant_kind: 'persona_moral', brand_name: { value: 'Marca Sintética' }, requested_products: ['tpv', 'ecommerce'], branches: Array.from({ length: 5 }, (_, index) => ({ name: `Sucursal ${index + 1}` })) },
      provenance_kind: 'operator_reported', recorded_at: '2026-10-13T12:00:00Z', created_by_principal_id: 'principal-1',
    }]);
    vi.mocked(client.previewCandidateCommercialIntake).mockResolvedValue({
      candidate_id: candidate.id, qualification_id: 'qualification-1', provisional_company_name: 'Marca Sintética', provisional_contact_name: null,
      product_interest: 'mixed', summary: 'Resumen suficientemente largo para comprobar una presentación legible del destino existente.', priority: 'normal', next_action: 'Vincular comercio', branches: [],
      provenance: { qualification: 'operator_reported' }, unresolved: [],
      promotion_trace: { id: 'trace-1', qualification_id: 'qualification-1', commercial_intake_id: 'intake-1', branch_drafts: Array.from({ length: 5 }, (_, index) => ({ name: `Sucursal ${index + 1}` })), created_at: '2026-10-13T13:00:00Z' },
      existing_intake: { id: 'intake-1', provisional_company_name: 'Marca Sintética', provisional_contact_name: null, product_interest: 'mixed', summary: 'Resumen suficientemente largo para comprobar una presentación legible del destino existente.', priority: 'normal', next_action: 'Vincular comercio', status: 'new' },
    });
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    expect(await screen.findByRole('heading', { name: 'Resultado registrado' })).toBeTruthy();
    expect(screen.getAllByText('Aceptado').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('link', { name: 'Abrir destino aceptado' }).getAttribute('href')).toBe('/netpay-inbox/contacts/intake-1');
    expect(screen.getAllByText('Resumen suficientemente largo para comprobar una presentación legible del destino existente.').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Ver detalle del destino')).toBeTruthy();
    for (const action of ['Aceptar', 'Rechazar', 'Marcar duplicado', 'Vincular']) {
      expect((screen.getByRole('button', { name: action }) as HTMLButtonElement).disabled).toBe(true);
    }
    expect((screen.getByRole('button', { name: 'Guardar corrección' }) as HTMLButtonElement).disabled).toBe(true);
    expect(client.reviewGmailCandidate).not.toHaveBeenCalled();
  });

  it('previews the approved H2-D dossier for a terminal candidate without creating it', async () => {
    const client = configuredClient();
    vi.mocked(client.listCandidateQualifications).mockResolvedValue([{
      id: 'qualification-1', candidate_id: candidate.id, sequence: 4,
      payload: { applicant_kind: 'persona_moral', requested_products: ['tpv', 'ecommerce'], branches: Array.from({ length: 5 }, (_, index) => ({ name: `Sucursal ${index + 1}` })) },
      provenance_kind: 'operator_reported', recorded_at: '2026-10-14T12:00:00Z', created_by_principal_id: 'principal-1',
    }]);
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    await waitFor(() => expect(client.previewCandidateDossier).toHaveBeenCalledWith('candidate-1'));
    const dossier = (await screen.findByRole('heading', { name: 'Expediente de alta' })).closest('section');
    expect(dossier?.textContent).toMatch(/Catálogo v1\.0\.0/);
    expect(dossier?.textContent).toMatch(/Sucursales:\s*5/);
    expect(dossier?.textContent).toMatch(/TPV.*e-commerce/i);
    expect(client.createCandidateDossier).not.toHaveBeenCalled();
  });

  it('reviews an overlay and requires preview before commercial intake confirmation', async () => {
    const client = configuredClient();
    const persistedQualification = { id: 'qualification-1', candidate_id: candidate.id, sequence: 1, payload: { applicant_kind: 'unresolved', requested_products: ['tpv'], branches: [{ name: 'Sucursal Uno' }, { name: 'Sucursal Dos' }] }, provenance_kind: 'operator_reported', recorded_at: '2026-10-13T12:00:00Z', created_by_principal_id: 'principal-1' };
    vi.mocked(client.createCandidateQualification).mockResolvedValue(persistedQualification);
    vi.mocked(client.listCandidateQualifications).mockResolvedValueOnce([]).mockResolvedValue([persistedQualification]);
    render(<MemoryRouter><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    await userEvent.type(screen.getByLabelText('Marca comercial'), 'Marca Sintética');
    await userEvent.type(screen.getByLabelText('Sucursales, una por línea'), 'Sucursal Uno\nSucursal Dos');
    await userEvent.click(screen.getByRole('button', { name: 'Revisar y guardar overlay' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Preparar ingreso comercial' }));
    expect(await screen.findByRole('heading', { name: 'Revisión previa del ingreso comercial' })).toBeTruthy();
    expect(client.promoteCandidateCommercialIntake).not.toHaveBeenCalled();
  });

  it('preserves the selected candidate in the URL and restores it after reload', async () => {
    const client = configuredClient();
    const view = render(<MemoryRouter initialEntries={['/netpay-inbox/gmail']}><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: /00199130/ }));
    expect(screen.getByRole('heading', { name: 'Caso sintético 00199130' })).toBeTruthy();
    view.unmount();

    render(<MemoryRouter initialEntries={['/netpay-inbox/gmail?candidate=candidate-1']}><NetpayGmailIntakeWorkspace client={client} /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: 'Caso sintético 00199130' })).toBeTruthy();
    expect(client.getGmailCandidate).toHaveBeenCalledWith('candidate-1');
  });
});
