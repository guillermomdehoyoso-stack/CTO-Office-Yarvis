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

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

function installApi(options: { empty?: boolean; detailStatus?: number; createStatus?: number; network?: boolean } = {}) {
  let current = { ...workItem };
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (options.network) throw new Error('offline');
    const url = new URL(String(input));
    const path = url.pathname;
    if (path === '/mission/work-items' && !init?.method) return response({ items: options.empty ? [] : [current], total: options.empty ? 0 : 1, limit: 20, offset: 0 });
    if (path === '/mission/inbox') return response({ items: [inboxItem], total: 1, limit: 50, offset: 0 });
    if (path === '/mission/work-items/work-1' && !init?.method) return response(options.detailStatus ? { code: 'RESOURCE_NOT_FOUND' } : current, options.detailStatus);
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
});
