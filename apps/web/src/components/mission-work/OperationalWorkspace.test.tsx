import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../../App';
import { setMissionWorkAccess } from '../../api/missionWork';

const fetchMock = vi.fn();
global.fetch = fetchMock as unknown as typeof fetch;

const summary = {
  subject_type: 'mission_work_item', subject_id: 'work-1', currency: 'MXN', as_of: '2026-07-29T10:00:00Z',
  expected_revenue: '1200.00', contracted_revenue: null, estimated_cost: '500.00', committed_cost: null,
  incurred_cost: '200.00', labor_cost: null, estimated_cost_to_complete: '300.00', projected_total_cost: '500.00',
  cash_received: '100.00', cash_paid: '50.00', net_cash_position: '50.00', expected_final_profit: '700.00',
  expected_final_margin_percent: '58.33', input_fact_ids: ['fact-1'], availability: 'available',
};

const workspace = {
  work_item: {
    id: 'work-1', inbox_item_id: 'inbox-1', source_type: 'intake', source_id: 'intake-1', title: 'Review merchant intake',
    summary: 'Needs review', status: 'in_progress', priority: 'high', assignee_subject_id: 'subject-2',
    created_by_subject_id: 'subject-1', created_at: '2026-07-29T08:00:00Z', updated_at: '2026-07-29T10:00:00Z',
    assigned_at: '2026-07-29T09:00:00Z', started_at: '2026-07-29T09:30:00Z', resolved_at: null, version: 2,
  },
  participants: ['subject-1', 'subject-2'],
  process_instances: [{
    id: 'process-1', lifecycle: 'active', process_definition_id: 'definition-1', process_definition_name: 'Merchant review',
    process_definition_version: 2, current_stage_id: 'stage-2', current_stage_key: 'review', current_stage_name: 'Review',
    current_stage_type: 'work', created_at: '2026-07-29T08:00:00Z', updated_at: '2026-07-29T10:00:00Z',
    completed_at: null, cancelled_at: null, cancellation_reason: null,
    last_transition: { id: 'process-event-1', occurred_at: '2026-07-29T10:00:00Z', event_type: 'process_instance.transitioned', actor_subject_id: 'subject-2', payload: { previous_stage_key: 'start', current_stage_key: 'review' }, sequence_number: 2 },
    links: [{ id: 'link-1', relationship_type: 'primary', linked_at: '2026-07-29T08:00:00Z', unlinked_at: null }],
    economic_summary: { ...summary, subject_type: 'process_instance', subject_id: 'process-1' },
  }],
  timeline: { items: [
    { id: 'event-1', occurred_at: '2026-07-29T08:00:00Z', event_type: 'work_item.created', actor_subject_id: 'subject-1', payload: {}, sequence_number: 1 },
    { id: 'event-2', occurred_at: '2026-07-29T10:00:00Z', event_type: 'process_instance.transitioned', actor_subject_id: 'subject-2', payload: { previous_stage_key: 'start', current_stage_key: 'review' }, sequence_number: 2 },
  ] },
  economic_summary: summary, active_process_instance_count: 1, historical_process_instance_count: 0, last_activity_at: '2026-07-29T10:00:00Z',
};

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

function renderWorkspace() {
  return render(<MemoryRouter initialEntries={['/mission-work/work-1/workspace']}><App /></MemoryRouter>);
}

describe('Operational Workspace', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    setMissionWorkAccess({ actorId: 'subject-1', organizationId: 'organization-1', token: 'token-1', authorities: ['mission.work.read'] });
    fetchMock.mockReset();
  });

  it('renders the governed workspace with direct economic summaries and its unified timeline', async () => {
    fetchMock.mockResolvedValue(response(workspace));
    renderWorkspace();

    expect(await screen.findByRole('heading', { name: 'Review merchant intake' })).toBeTruthy();
    expect(screen.getByText('Procesos activos')).toBeTruthy();
    expect(screen.getByText('Merchant review v2')).toBeTruthy();
    expect(screen.getByText(/Etapa actual: Review/)).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Timeline operativo' })).toBeTruthy();
    expect(screen.getByText('Etapa: start → review.')).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/mission/work-items/work-1/workspace?currency=MXN'), expect.objectContaining({ headers: expect.objectContaining({ 'X-Yarvis-Authority': 'mission.work.read' }) }));
  });

  it('renders the empty process and timeline states', async () => {
    fetchMock.mockResolvedValue(response({ ...workspace, process_instances: [], timeline: { items: [] }, active_process_instance_count: 0 }));
    renderWorkspace();

    expect(await screen.findByText('No hay instancias de proceso relacionadas.')).toBeTruthy();
    expect(screen.getByText('No hay eventos registrados para este Work Item.')).toBeTruthy();
  });

  it('conceals unavailable cross-tenant workspaces as a visible not-found state', async () => {
    fetchMock.mockResolvedValue(response({ code: 'RESOURCE_NOT_FOUND' }, 404));
    renderWorkspace();

    expect(await screen.findByText(/no está disponible o no pertenece a tu organización/i)).toBeTruthy();
  });

  it('renders a network failure without fabricating workspace data', async () => {
    fetchMock.mockRejectedValue(new Error('offline'));
    renderWorkspace();

    expect(await screen.findByText('No se pudo conectar con la API.')).toBeTruthy();
    expect(screen.queryByText('Procesos relacionados')).toBeNull();
  });
});
