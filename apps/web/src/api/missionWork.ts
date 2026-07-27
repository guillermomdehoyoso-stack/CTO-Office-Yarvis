import type {
  MissionInboxPage,
  MissionWorkAccess,
  MissionWorkFilters,
  MissionWorkItem,
  MissionWorkPage,
  MissionWorkPriority,
  MissionWorkStatus,
} from '../types/missionWork';

const BASE_URL = 'http://localhost:8000';
const ACCESS_KEY = 'yarvis.mission-work.access';

export class MissionWorkApiError extends Error {
  constructor(public readonly status: number, public readonly code?: string) {
    super(code || `Request failed (${status})`);
  }
}

export function getMissionWorkAccess(): MissionWorkAccess | null {
  const raw = window.sessionStorage.getItem(ACCESS_KEY);
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as MissionWorkAccess;
    if (!value.actorId || !value.organizationId || !value.token) return null;
    return { ...value, authorities: Array.from(new Set(value.authorities || [])) };
  } catch {
    return null;
  }
}

export function setMissionWorkAccess(access: MissionWorkAccess | null): void {
  if (!access) {
    window.sessionStorage.removeItem(ACCESS_KEY);
    return;
  }
  window.sessionStorage.setItem(ACCESS_KEY, JSON.stringify({ ...access, authorities: Array.from(new Set(access.authorities)) }));
}

export function hasMissionWorkAuthority(authority: string): boolean {
  return Boolean(getMissionWorkAccess()?.authorities.includes(authority));
}

function query(values: MissionWorkFilters): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value));
  });
  return params.size ? `?${params}` : '';
}

async function request<T>(path: string, authority: string, init?: RequestInit): Promise<T> {
  const access = getMissionWorkAccess();
  if (!access || !access.authorities.includes(authority)) {
    throw new MissionWorkApiError(403, 'AUTHORIZATION_DENIED');
  }
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'X-Yarvis-Actor': access.actorId,
        'X-Yarvis-Organization': access.organizationId,
        'X-Yarvis-Authority': authority,
        'X-Yarvis-Auth-Token': access.token,
        ...(init?.headers || {}),
      },
    });
  } catch {
    throw new MissionWorkApiError(0, 'NETWORK_ERROR');
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { code?: string };
    throw new MissionWorkApiError(response.status, payload.code);
  }
  return response.json() as Promise<T>;
}

export function listMissionWorkItems(filters: MissionWorkFilters = {}): Promise<MissionWorkPage> {
  return request('/mission/work-items' + query(filters), 'mission.work.read');
}

export function getMissionWorkItem(workItemId: string): Promise<MissionWorkItem> {
  return request(`/mission/work-items/${encodeURIComponent(workItemId)}`, 'mission.work.read');
}

export function createMissionWorkItem(inboxItemId: string): Promise<MissionWorkItem> {
  return request('/mission/work-items', 'mission.work.create', { method: 'POST', body: JSON.stringify({ inbox_item_id: inboxItemId }) });
}

export function assignMissionWorkItem(workItemId: string, assigneeSubjectId: string | null): Promise<MissionWorkItem> {
  return request(`/mission/work-items/${encodeURIComponent(workItemId)}/assignment`, 'mission.work.assign', { method: 'POST', body: JSON.stringify({ assignee_subject_id: assigneeSubjectId }) });
}

export function changeMissionWorkStatus(workItemId: string, status: MissionWorkStatus): Promise<MissionWorkItem> {
  return request(`/mission/work-items/${encodeURIComponent(workItemId)}/status`, 'mission.work.status.change', { method: 'POST', body: JSON.stringify({ status }) });
}

export function changeMissionWorkPriority(workItemId: string, priority: MissionWorkPriority): Promise<MissionWorkItem> {
  return request(`/mission/work-items/${encodeURIComponent(workItemId)}/priority`, 'mission.work.priority.change', { method: 'POST', body: JSON.stringify({ priority }) });
}

export function listMissionInboxItems(): Promise<MissionInboxPage> {
  return request('/mission/inbox', 'mission.inbox.read');
}
