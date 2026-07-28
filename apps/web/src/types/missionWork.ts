export const MISSION_WORK_STATUSES = ['open', 'assigned', 'in_progress', 'waiting', 'resolved', 'cancelled'] as const;
export const MISSION_WORK_PRIORITIES = ['low', 'normal', 'high', 'urgent'] as const;

export type MissionWorkStatus = (typeof MISSION_WORK_STATUSES)[number];
export type MissionWorkPriority = (typeof MISSION_WORK_PRIORITIES)[number];

export interface MissionWorkItem {
  id: string;
  inbox_item_id: string;
  source_type: string;
  source_id: string;
  title: string;
  summary: string | null;
  status: MissionWorkStatus;
  priority: MissionWorkPriority;
  assignee_subject_id: string | null;
  created_by_subject_id: string;
  created_at: string;
  updated_at: string;
  assigned_at: string | null;
  started_at: string | null;
  resolved_at: string | null;
  version: number;
}

export interface MissionWorkPage {
  items: MissionWorkItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MissionWorkEvent {
  id: string;
  occurred_at: string;
  event_type: string;
  actor_subject_id: string | null;
  payload: Record<string, unknown>;
  sequence_number: number;
}

export interface MissionWorkTimeline {
  items: MissionWorkEvent[];
}

export interface MissionInboxItem {
  id: string;
  source_type: string;
  source_id: string;
  title: string;
  summary: string | null;
  status: string;
  priority: string;
}

export interface MissionInboxPage {
  items: MissionInboxItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MissionWorkFilters {
  status?: MissionWorkStatus;
  priority?: MissionWorkPriority;
  assignee_subject_id?: string;
  inbox_item_id?: string;
  source_type?: string;
  source_id?: string;
  limit?: number;
  offset?: number;
}

export interface MissionWorkAccess {
  actorId: string;
  organizationId: string;
  token: string;
  authorities: string[];
}
