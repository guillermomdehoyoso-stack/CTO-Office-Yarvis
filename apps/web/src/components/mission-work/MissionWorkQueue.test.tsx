import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from '../../App';
import { setMissionWorkAccess } from '../../api/missionWork';

const fetchMock = vi.fn();
global.fetch = fetchMock as unknown as typeof fetch;

const workItem = {
  id: 'work-1', inbox_item_id: 'inbox-before-rebuild', source_type: 'intake', source_id: 'intake-1',
  title: 'Review merchant intake', summary: 'Needs review', status: 'open', priority: 'normal',
  assignee_subject_id: null, created_by_subject_id: 'subject-1', created_at: '2026-07-27T00:00:00Z',
  updated_at: '2026-07-27T00:00:00Z', assigned_at: null, started_at: null, resolved_at: null, version: 1,
};
const inboxItem = { id: 'inbox-after-rebuild', source_type: 'intake', source_id: 'intake-1', title: 'Review merchant intake', summary: 'Needs review', status: 'pending', priority: 'normal' };
const timelineItems = [
  { id: 'event-1', occurred_at: '2026-07-27T10:00:00Z', event_type: 'work_item.created', actor_subject_id: 'subject-1', payload: { status: 'open', priority: 'normal' }, sequence_number: 1 },
  { id: 'event-2', occurred_at: '2026-07-27T11:00:00Z', event_type: 'work_item.assigned', actor_subject_id: 'subject-2', payload: { previous_status: 'open', status: 'assigned', previous_assignee_subject_id: null, assignee_subject_id: 'subject-2' }, sequence_number: 2 },
  { id: 'event-3', occurred_at: '2026-07-27T12:00:00Z', event_type: 'work_item.priority_changed', actor_subject_id: 'subject-2', payload: { previous_priority: 'normal', priority: 'high' }, sequence_number: 3 },
  { id: 'event-4', occurred_at: '2026-07-27T13:00:00Z', event_type: 'work_item.unassigned', actor_subject_id: 'subject-2', payload: { previous_status: 'assigned', status: 'open', previous_assignee_subject_id: 'subject-2', assignee_subject_id: null }, sequence_number: 4 },
  { id: 'event-5', occurred_at: '2026-07-27T14:00:00Z', event_type: 'work_item.status_changed', actor_subject_id: 'subject-1', payload: { previous_status: 'open', status: 'in_progress' }, sequence_number: 5 },
];

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

function installApi(options: { empty?: boolean; detailStatus?: number; createStatus?: number; network?: boolean; timelineEmpty?: boolean; timelineError?: boolean; unknownEvent?: boolean; commentStatus?: number } = {}) {
  let current = { ...workItem };
  let timeline = options.timelineEmpty ? [] : [...timelineItems, ...(options.unknownEvent ? [{ id: 'event-unknown', occurred_at: '2026-07-27T13:00:00Z', event_type: 'future.event', actor_subject_id: null, payload: {}, sequence_number: 4 }] : [])];
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (options.network) throw new Error('offline');
    const url = new URL(String(input));
    const path = url.pathname;
    if (path === '/mission/work-items' && !init?.method) return response({ items: options.empty ? [] : [current], total: options.empty ? 0 : 1, limit: 20, offset: 0 });
    if (path === '/mission/inbox') return response({ items: [inboxItem], total: 1, limit: 50, offset: 0 });
    if (path === '/mission/work-items/work-1' && !init?.method) return response(options.detailStatus ? { code: 'RESOURCE_NOT_FOUND' } : current, options.detailStatus);
    if (path === '/mission/work-items/work-1/timeline' && !init?.method) return response(options.timelineError ? { code: 'RESOURCE_NOT_FOUND' } : { items: timeline }, options.timelineError ? 404 : 200);
    if (path === '/mission/work-items/work-1/comments' && init?.method === 'POST') {
      if (options.commentStatus) return response({ code: 'CONFLICT' }, options.commentStatus);
      const comment = JSON.parse(String(init?.body)).comment;
      const event = { id: `comment-${timeline.length + 1}`, occurred_at: '2026-07-27T14:00:00Z', event_type: 'comment.added', actor_subject_id: 'subject-1', payload: { comment }, sequence_number: timeline.length + 1 };
      timeline = [...timeline, event];
      return response(event, 201);
    }
    if (path === '/mission/work-items' && init?.method === 'POST') return response(options.createStatus ? { code: 'DUPLICATE_RESOURCE' } : current, options.createStatus);
    if (path.endsWith('/assignment')) {
      current = { ...current, assignee_subject_id: (JSON.parse(String(init?.body)).assignee_subject_id), version: current.version + 1 };
      return response(current);
    }
    if (path.endsWith('/status')) {
      current = { ...current, status: JSON.parse(String(init?.body)).status, version: current.version + 1 };
      return response(current);
    }
    if (path.endsWith('/priority')) {
      current = { ...current, priority: JSON.parse(String(init?.body)).priority, version: current.version + 1 };
      return response(current);
    }
    return response({ code: 'RESOURCE_NOT_FOUND' }, 404);
  });
}

function renderWork(path = '/mission-work') {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

describe('Mission Work Queue', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    setMissionWorkAccess({
      actorId: 'subject-1', organizationId: 'organization-1', token: 'token-1',
      authorities: ['mission.work.read', 'mission.work.create', 'mission.work.assign', 'mission.work.status.change', 'mission.work.priority.change', 'mission.inbox.read'],
    });
    fetchMock.mockReset();
  });

  it('renders the list, filters it, and preserves the API authority header', async () => {
    installApi();
    renderWork();
    expect((await screen.findAllByText('Review merchant intake')).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText('Filtrar estado'), { target: { value: 'open' } });
    fireEvent.change(screen.getByLabelText('Filtrar prioridad'), { target: { value: 'high' } });
    fireEvent.change(screen.getByLabelText('Filtrar asignado a'), { target: { value: 'subject-2' } });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('assignee_subject_id=subject-2'), expect.any(Object)));
    const call = fetchMock.mock.calls.find(([url]) => String(url).includes('/mission/work-items?') && String(url).includes('status=open') && String(url).includes('priority=high') && String(url).includes('assignee_subject_id=subject-2'));
    expect((call?.[1] as RequestInit).headers).toMatchObject({ 'X-Yarvis-Authority': 'mission.work.read' });
  });

  it('renders the empty state', async () => {
    installApi({ empty: true });
    renderWork();
    expect(await screen.findByText('No hay Work Items para estos filtros.')).toBeTruthy();
  });

  it('opens detail and supports assignment, unassignment, status, and priority changes', async () => {
    installApi();
    const user = userEvent.setup();
    renderWork();
    await user.click(await screen.findByRole('button', { name: /review merchant intake/i }));
    expect(await screen.findByRole('heading', { name: 'Review merchant intake' })).toBeTruthy();
    await user.type(screen.getByLabelText('Asignar a'), 'subject-2');
    await user.click(screen.getByRole('button', { name: 'Asignar' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Desasignar' }).hasAttribute('disabled')).toBe(false));
    await user.click(screen.getByRole('button', { name: 'Desasignar' }));
    await user.selectOptions(screen.getByLabelText('Cambiar estado'), 'in_progress');
    await user.selectOptions(screen.getByLabelText('Cambiar prioridad'), 'high');
    await waitFor(() => expect(fetchMock.mock.calls.filter(([url, init]) => String(url).includes('/assignment') || String(url).includes('/status') || String(url).includes('/priority')).length).toBe(4));
  });

  it('creates a Work Item from Mission Inbox without sending a duplicate mutation', async () => {
    installApi();
    const user = userEvent.setup();
    renderWork();
    const button = await screen.findByRole('button', { name: 'Crear o abrir Work Item' });
    await user.dblClick(button);
    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Work Item creado.'));
    expect(fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith('/mission/work-items') && init?.method === 'POST')).toHaveLength(1);
  });

  it('handles governed 404 and recovers a post-rebuild duplicate by stable source identity', async () => {
    installApi({ detailStatus: 404 });
    const { unmount } = renderWork('/mission-work?work_item_id=work-1');
    expect(await screen.findByText(/ya no está disponible/i)).toBeTruthy();
    unmount();

    installApi({ createStatus: 409 });
    renderWork();
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Crear o abrir Work Item' }));
    expect(await screen.findByText(/ya existe un Work Item/i)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('source_type=intake'), expect.any(Object));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('source_id=intake-1'), expect.any(Object));
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('inbox_item_id='))).toBe(false);
  });

  it('handles a network error and hides mutations without their authorities', async () => {
    setMissionWorkAccess({ actorId: 'subject-1', organizationId: 'organization-1', token: 'token-1', authorities: ['mission.work.read'] });
    installApi({ network: true });
    renderWork();
    expect(await screen.findByText('No se pudo conectar con la API.')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Crear o abrir Work Item' })).toBeNull();
  });

  it('loads the Timeline in sequence order and renders governed transitions', async () => {
    installApi();
    const user = userEvent.setup();
    renderWork();
    await user.click(await screen.findByRole('button', { name: /review merchant intake/i }));

    const timeline = await screen.findByRole('region', { name: 'Timeline operativo' });
    expect(timeline.textContent).toContain('Work Item creado');
    expect(timeline.textContent).toContain('sin asignar → subject-2');
    expect(timeline.textContent).toContain('subject-2 → sin asignar');
    expect(timeline.textContent).toContain('open → in_progress');
    expect(timeline.textContent).toContain('normal → high');
    expect(timeline.textContent?.indexOf('Secuencia 1')).toBeLessThan(timeline.textContent?.indexOf('Secuencia 2') || 0);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/mission/work-items/work-1/timeline'), expect.any(Object));
  });

  it('renders empty, error, and unknown Timeline states safely', async () => {
    installApi({ timelineEmpty: true });
    const { unmount } = renderWork('/mission-work?work_item_id=work-1');
    expect(await screen.findByText('No hay eventos registrados para este Work Item.')).toBeTruthy();
    unmount();

    installApi({ timelineError: true });
    const second = renderWork('/mission-work?work_item_id=work-1');
    expect(await screen.findByText(/ya no est. disponible/i)).toBeTruthy();
    second.unmount();

    installApi({ unknownEvent: true });
    renderWork('/mission-work?work_item_id=work-1');
    expect(await screen.findByText('Evento desconocido: future.event.')).toBeTruthy();
  });

  it('adds a non-empty comment once, clears it, and refreshes the Timeline', async () => {
    installApi();
    const user = userEvent.setup();
    renderWork('/mission-work?work_item_id=work-1');
    const comment = await screen.findByLabelText('Comentario interno');
    expect(screen.getByRole('button', { name: 'Agregar comentario' }).hasAttribute('disabled')).toBe(true);
    await user.type(comment, 'Seguimiento confirmado');
    await user.dblClick(screen.getByRole('button', { name: 'Agregar comentario' }));

    await waitFor(() => expect(screen.getByRole('status').textContent).toContain('Comentario agregado.'));
    expect((screen.getByLabelText('Comentario interno') as HTMLTextAreaElement).value).toBe('');
    expect(await screen.findByText('Seguimiento confirmado')).toBeTruthy();
    expect(fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith('/comments') && init?.method === 'POST')).toHaveLength(1);
  });

  it('preserves the comment text when the governed comment request fails', async () => {
    installApi({ commentStatus: 409 });
    const user = userEvent.setup();
    renderWork('/mission-work?work_item_id=work-1');
    const comment = await screen.findByLabelText('Comentario interno');
    await user.type(comment, 'No perder este texto');
    await user.click(screen.getByRole('button', { name: 'Agregar comentario' }));

    expect(await screen.findByText(/entra en conflicto/i)).toBeTruthy();
    expect((screen.getByLabelText('Comentario interno') as HTMLTextAreaElement).value).toBe('No perder este texto');
  });
});
