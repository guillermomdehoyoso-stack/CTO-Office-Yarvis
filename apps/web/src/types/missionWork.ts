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

export interface EconomicSummary {
  subject_type: string;
  subject_id: string;
  currency: string;
  as_of: string;
  expected_revenue: string | null;
  contracted_revenue: string | null;
  estimated_cost: string | null;
  committed_cost: string | null;
  incurred_cost: string | null;
  labor_cost: string | null;
  estimated_cost_to_complete: string | null;
  projected_total_cost: string | null;
  cash_received: string | null;
  cash_paid: string | null;
  net_cash_position: string | null;
  expected_final_profit: string | null;
  expected_final_margin_percent: string | null;
  input_fact_ids: string[];
  availability: string;
}

export interface OperationalWorkspaceProcessLink {
  id: string;
  relationship_type: string;
  linked_at: string;
  unlinked_at: string | null;
}

export interface OperationalWorkspaceProcessInstance {
  id: string;
  lifecycle: string;
  process_definition_id: string;
  process_definition_name: string;
  process_definition_version: number;
  current_stage_id: string;
  current_stage_key: string;
  current_stage_name: string;
  current_stage_type: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  last_transition: MissionWorkEvent | null;
  links: OperationalWorkspaceProcessLink[];
  economic_summary: EconomicSummary;
}

export interface OperationalWorkspace {
  work_item: MissionWorkItem;
  participants: string[];
  process_instances: OperationalWorkspaceProcessInstance[];
  timeline: MissionWorkTimeline;
  economic_summary: EconomicSummary;
  active_process_instance_count: number;
  historical_process_instance_count: number;
  last_activity_at: string;
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
