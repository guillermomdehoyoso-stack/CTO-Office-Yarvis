import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import App from '../App';
import { setWorkspaceAccessToken } from '../api/workspacePlatform';

const fetchMock = vi.fn();
global.fetch = fetchMock as unknown as typeof fetch;

const baseWorkspace = {
  workspace: { workspace_id: 'ws000', name: 'Development Workspace', description: 'WS-000', status: 'active', capabilities: ['dashboard'] },
  dashboard: {
    workspace_id: 'ws000', workspace_name: 'Development Workspace', current_sprint: 'WS-000', current_gate: 'Scoped EOS Gate',
    repository_health: { total_files: 10, documentation_files: 5, python_files: 2, typescript_files: 3, by_extension: { '.md': 5 }, generated_at: '2026-07-23T00:00:00+00:00', read_only_authority: 'repository' },
    timeline_preview: [], updated_at: '2026-07-23T00:00:00+00:00',
  },
  state: { current_sprint: 'WS-000', current_gate: 'Scoped EOS Gate', work_package: 'WS-000', governance_mode: 'Maintenance Mode' },
  observer: { observations: ['Repository scanner indexed 10 files.'], recommendations: ['Keep WS-000 implementation outside docs/eos gate scope.'], blockers: [], next_action: 'Build next module', engineering_health: 'healthy', generated_at: '2026-07-23T00:00:00+00:00' },
};

beforeEach(() => {
  fetchMock.mockReset();
  setWorkspaceAccessToken('workspace-test-token');
  fetchMock.mockImplementation((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/api/v1/workspaces')) return Promise.resolve({ ok: true, json: async () => ({ count: 1, items: [{ workspace_id: 'ws000', name: 'Development Workspace', description: 'WS-000', status: 'active' }] }) });
    if (url.includes('/api/v1/workspaces/ws000')) return Promise.resolve({ ok: true, json: async () => baseWorkspace });
    if (url.includes('/api/v1/dashboard')) return Promise.resolve({ ok: true, json: async () => baseWorkspace.dashboard });
    if (url.includes('/api/v1/timeline')) return Promise.resolve({ ok: true, json: async () => ({ workspace_id: 'ws000', current_sprint: 'WS-000', current_gate: 'Scoped EOS Gate', events: [] }) });
    if (url.includes('/api/v1/repository')) return Promise.resolve({ ok: true, json: async () => ({ workspace_id: 'ws000', health: baseWorkspace.dashboard.repository_health, document_reference_graph: { node_count: 2, edge_count: 1 } }) });
    if (url.includes('/api/v1/health')) return Promise.resolve({ ok: true, json: async () => ({ workspace_id: 'ws000', status: 'ok', services: { workspace_api: 'ok', engineering_observer: 'ok' }, engineering_health: 'healthy', generated_at: '2026-07-23T00:00:00+00:00' }) });
    if (url.includes('/api/v1/search')) return Promise.resolve({ ok: true, json: async () => ({ workspace_id: 'ws000', query: 'architecture', count: 1, results: [{ path: 'docs/architecture/ARCHITECTURE_INDEX.md', score: 9, snippet: 'Architecture index' }] }) });
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
});

describe('Workspace shell', () => {
  it('renders dashboard and observer panel', async () => {
    render(<MemoryRouter initialEntries={['/workspace/dashboard']}><App /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /development workspace/i })).toBeTruthy();
    expect(await screen.findByText(/engineering observer/i)).toBeTruthy();
    expect(await screen.findByText(/current sprint/i)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/workspaces'), expect.objectContaining({ headers: { 'X-Yarvis-Workspace-Token': 'workspace-test-token' } }));
  });

  it('renders repository page', async () => {
    render(<MemoryRouter initialEntries={['/workspace/repository']}><App /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /repository/i })).toBeTruthy();
    expect(await screen.findByText(/reference nodes/i)).toBeTruthy();
  });

  it('renders health page', async () => {
    render(<MemoryRouter initialEntries={['/workspace/health']}><App /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /health/i })).toBeTruthy();
    expect(await screen.findByText(/platform status/i)).toBeTruthy();
  });
});
