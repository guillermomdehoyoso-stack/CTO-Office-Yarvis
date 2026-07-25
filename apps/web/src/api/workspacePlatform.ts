import type {
  DashboardResponse,
  HealthResponse,
  RepositoryResponse,
  SearchResponse,
  TimelineResponse,
  WorkspaceDetailResponse,
  WorkspacesResponse,
} from '../types/workspacePlatform';

const BASE_URL = 'http://localhost:8000/api/v1';
const WORKSPACE_ACCESS_TOKEN_KEY = 'yarvis.workspace.access-token';

export function getWorkspaceAccessToken(): string {
  return window.sessionStorage.getItem(WORKSPACE_ACCESS_TOKEN_KEY) || '';
}

export function setWorkspaceAccessToken(token: string): void {
  const normalized = token.trim();
  if (normalized) {
    window.sessionStorage.setItem(WORKSPACE_ACCESS_TOKEN_KEY, normalized);
  } else {
    window.sessionStorage.removeItem(WORKSPACE_ACCESS_TOKEN_KEY);
  }
}

function buildQuery(params: Record<string, string | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value && value.trim().length > 0) {
      query.set(key, value);
    }
  });
  const rendered = query.toString();
  return rendered.length > 0 ? `?${rendered}` : '';
}

async function request<T>(path: string): Promise<T> {
  const token = getWorkspaceAccessToken();
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: token ? { 'X-Yarvis-Workspace-Token': token } : undefined,
  });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getWorkspaces(): Promise<WorkspacesResponse> {
  return request<WorkspacesResponse>('/workspaces');
}

export function getWorkspace(workspaceId: string): Promise<WorkspaceDetailResponse> {
  return request<WorkspaceDetailResponse>(`/workspaces/${encodeURIComponent(workspaceId)}`);
}

export function getDashboard(workspaceId: string): Promise<DashboardResponse> {
  return request<DashboardResponse>(`/dashboard${buildQuery({ workspace_id: workspaceId })}`);
}

export function getRepository(workspaceId: string): Promise<RepositoryResponse> {
  return request<RepositoryResponse>(`/repository${buildQuery({ workspace_id: workspaceId })}`);
}

export function getTimeline(workspaceId: string): Promise<TimelineResponse> {
  return request<TimelineResponse>(`/timeline${buildQuery({ workspace_id: workspaceId })}`);
}

export function searchRepository(workspaceId: string, query: string): Promise<SearchResponse> {
  return request<SearchResponse>(`/search${buildQuery({ workspace_id: workspaceId, q: query })}`);
}

export function getHealth(workspaceId: string): Promise<HealthResponse> {
  return request<HealthResponse>(`/health${buildQuery({ workspace_id: workspaceId })}`);
}
