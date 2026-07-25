export interface WorkspaceSummary {
  workspace_id: string;
  name: string;
  description: string;
  status: string;
}

export interface WorkspacesResponse {
  count: number;
  items: WorkspaceSummary[];
}

export interface DashboardResponse {
  workspace_id: string;
  workspace_name: string;
  current_sprint: string;
  current_gate: string;
  repository_health: {
    total_files: number;
    documentation_files: number;
    python_files: number;
    typescript_files: number;
    by_extension: Record<string, number>;
    generated_at: string;
    read_only_authority: string;
  };
  timeline_preview: Array<{
    path: string;
    modified_at: string;
    size_bytes: number;
    kind: string;
  }>;
  updated_at: string;
}

export interface WorkspaceDetailResponse {
  workspace: {
    workspace_id: string;
    name: string;
    description: string;
    status: string;
    capabilities: string[];
  };
  dashboard: DashboardResponse;
  state: {
    current_sprint: string;
    current_gate: string;
    work_package: string;
    governance_mode: string;
  };
  observer: {
    observations: string[];
    recommendations: string[];
    blockers: string[];
    next_action: string;
    engineering_health: string;
    generated_at: string;
  };
}

export interface RepositoryResponse {
  workspace_id: string;
  health: DashboardResponse['repository_health'];
  document_reference_graph: {
    node_count: number;
    edge_count: number;
  };
}

export interface TimelineResponse {
  workspace_id: string;
  current_sprint: string;
  current_gate: string;
  events: Array<{
    path: string;
    modified_at: string;
    size_bytes: number;
    kind: string;
  }>;
}

export interface SearchResponse {
  workspace_id: string;
  query: string;
  count: number;
  results: Array<{
    path: string;
    score: number;
    snippet: string;
  }>;
}

export interface HealthResponse {
  workspace_id: string;
  status: string;
  services: Record<string, string>;
  engineering_health: string;
  generated_at: string;
}
