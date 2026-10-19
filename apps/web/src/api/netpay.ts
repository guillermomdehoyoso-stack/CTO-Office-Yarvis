export type NetpayStoreReference = {
  id: string;
  store_id: string;
  source_type: string;
  source_reference: string | null;
  assigned_at: string;
  confirmed_at: string | null;
  active: boolean;
};

export type NetpayBranch = {
  id: string;
  company_id: string;
  commercial_name: string;
  branch_kind: "physical" | "commercial";
  address: string | null;
  locality: string | null;
  state: string | null;
  postal_code: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  store_reference: NetpayStoreReference | null;
};

export type NetpayCompany = {
  id: string;
  client_id: string;
  legal_name: string;
  tax_identifier: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  branches: NetpayBranch[];
};

export type NetpayClient = {
  id: string;
  display_name: string;
  external_reference: string | null;
  primary_contact_name: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  companies: NetpayCompany[];
};

export type MasterPage = {
  items: NetpayClient[];
  offset: number;
  limit: number;
  total: number;
};
export type ChecklistItem = {
  id: string;
  requirement_key: string;
  status: string;
  required: boolean;
  safe_evidence_reference: string | null;
  template_version: number;
};
export type CaseStep = {
  id: string;
  ordinal: number;
  description: string;
  status: string;
};
export type NextAction = {
  id: string;
  description: string;
  status: string;
  responsible_principal_id: string | null;
  due_date: string | null;
  origin: string;
};
export type CaseActivity = {
  id: string;
  type: string;
  summary: string;
  created_at: string;
};
export type DocumentReference = {
  id: string;
  status: string;
  external_evidence_reference: string | null;
};

export type NetpayCase = {
  id: string;
  folio: string;
  client_id: string;
  company_id: string;
  branch_id: string | null;
  store_reference_id: string | null;
  case_type_key: string;
  original_description: string;
  expected_outcome: string | null;
  product: string;
  state: string;
  priority: string;
  responsible_principal_id: string | null;
  target_date: string | null;
  source_channel: string | null;
  source_reference: string | null;
  checklist_template_version: number | null;
  created_at: string;
  updated_at: string;
  requires_attention: boolean;
  checklist: ChecklistItem[];
  steps: CaseStep[];
  next_actions: NextAction[];
  activities: CaseActivity[];
  document_references: DocumentReference[];
};

export type InboxPage = {
  items: NetpayCase[];
  offset: number;
  limit: number;
  total: number;
};
export type CommercialIntake = {
  id: string;
  kind: string;
  channel: string;
  received_at: string;
  provisional_company_name: string | null;
  provisional_contact_name: string | null;
  product_interest: string;
  summary: string;
  priority: string;
  assignee_principal_id: string | null;
  next_action: string | null;
  due_date: string | null;
  status: string;
  master_client_id: string | null;
  master_company_id: string | null;
  master_branch_id: string | null;
  converted_case_id: string | null;
  created_at: string;
  updated_at: string;
  requires_attention: boolean;
  timeline: { type: string; at: string }[];
};
export type CommercialIntakePage = {
  items: CommercialIntake[];
  offset: number;
  limit: number;
  total: number;
};
export type OperationalDataRow = {
  id: string;
  source_row_number: number;
  validation_status: string;
  match_status: string;
  store_reference_id: string | null;
  error_codes: string[];
  projected_action: string;
  preview: Record<string, unknown>;
};
export type OperationalDataBatch = {
  id: string;
  dataset_type: string;
  reporting_period: string | null;
  sanitized_filename: string;
  selected_sheet: string;
  hash_identifier: string;
  preview_token: string;
  duplicate_upload: boolean;
  status: string;
  row_counts: Record<string, number>;
  source_discarded: boolean;
  created_at: string;
  updated_at: string;
  rows: OperationalDataRow[];
};
export type OperationalDataBatchPage = {
  items: OperationalDataBatch[];
  total: number;
};
export type GmailConnection = {
  id: string;
  provider_account_id: string;
  provider_kind: string;
  label_id: string;
  state: string;
  last_sync_at: string | null;
  last_error_code: string | null;
  mailbox_verified_at: string | null;
  manifest_status: string;
  manifest_entries: { handle: string; received_at: string }[];
  manifest_approved_at: string | null;
};
export type GmailCandidate = {
  id: string;
  source_item_id: string;
  received_at: string;
  state: string;
  request_type: string;
  product: string;
  description: string;
  ticket_references: string[];
  commerce_hints: { kind: string; value: string }[];
  terminal_serials: string[];
  shipment_facts: Record<string, string>;
  facts: Record<string, string>[];
  inferences: Record<string, string>[];
  contradictions: Record<string, string>[];
  missing_data: string[];
  correlation_key: string | null;
  priority: string;
  suggested_next_action: string | null;
  follow_up_at: string | null;
  follow_up_basis: string;
  explicit_deadline_at: string | null;
  confidence: number;
  age_days: number;
  overdue: boolean;
  related_candidate_ids: string[];
  owner_type: string | null;
  owner_id: string | null;
  disposition_reason: string | null;
  reviewed_at: string | null;
  immutable: boolean;
};
export type GmailCandidatePage = {
  items: GmailCandidate[];
  offset: number;
  limit: number;
  total: number;
};
export type GmailSourceItem = {
  id: string;
  gmail_message_id: string;
  gmail_thread_id: string;
  provider_received_at: string;
  sender: string | null;
  recipient: string | null;
  subject: string | null;
  plain_excerpt: string;
  attachment_metadata: Record<string, unknown>[];
  provenance: Record<string, unknown>;
};
export type CandidateHumanFollowUp = {
  id: string;
  candidate_id: string;
  kind: string;
  note: string;
  provenance_kind: "operator_reported";
  occurred_at: string | null;
  recorded_at: string;
  created_by_principal_id: string;
  correlation_id: string;
};
export type CandidateHumanFollowUpPage = {
  items: CandidateHumanFollowUp[];
  offset: number;
  limit: number;
  total: number;
};
export type CandidateQualification = {
  id: string;
  candidate_id: string;
  sequence: number;
  payload: Record<string, unknown>;
  provenance_kind: string;
  recorded_at: string;
  created_by_principal_id: string;
};
export type CommercialIntakePreview = {
  candidate_id: string;
  qualification_id: string;
  provisional_company_name: string | null;
  provisional_contact_name: string | null;
  product_interest: string;
  summary: string;
  priority: string;
  next_action: string | null;
  branches: Record<string, unknown>[];
  provenance: Record<string, string>;
  unresolved: string[];
  promotion_trace?: {
    id: string;
    qualification_id: string;
    commercial_intake_id: string;
    branch_drafts: Record<string, unknown>[];
    created_at: string;
  } | null;
  existing_intake?: Pick<
    CommercialIntake,
    | "id"
    | "provisional_company_name"
    | "provisional_contact_name"
    | "product_interest"
    | "summary"
    | "priority"
    | "next_action"
    | "status"
  > | null;
};
export type DossierRequirementHistory = {
  id: string;
  sequence: number;
  prior_state: string;
  state: string;
  review_data: Record<string, unknown>;
  comment: string | null;
  provenance_kind: string;
  recorded_at: string;
  created_by_principal_id: string;
  evidence: {
    id: string;
    source_item_id: string;
    attachment_index: number;
    metadata: Record<string, unknown>;
    suggestion: string | null;
    verification: string;
  } | null;
};
export type DossierRequirement = {
  snapshot_key: string;
  key: string;
  label: string;
  scope: string;
  scope_key: string;
  branch_name?: string;
  required: boolean;
  maximum_age_days?: number;
  shareable?: boolean;
  expected_count?: number;
  state: string;
  history?: DossierRequirementHistory[];
};
export type CandidateDossier = {
  id: string;
  candidate_id: string;
  commercial_intake_id: string;
  qualification_id: string;
  catalog_version: string;
  catalog_effective_date: string;
  catalog_sha256: string;
  catalog_owner: string;
  applicant_kind: string;
  products: string[];
  branches: Record<string, unknown>[];
  created_at: string;
  requirements: DossierRequirement[];
  state_counts: Record<string, number>;
  blockers: { snapshot_key: string; label: string; state: string }[];
  complete: boolean;
  history_count: number;
};
export type CandidateDossierPreview = {
  existing: boolean;
  dossier?: CandidateDossier;
  candidate_id?: string;
  commercial_intake_id?: string;
  qualification_id?: string;
  candidate_terminal?: boolean;
  candidate_state?: string;
  catalog_version?: string;
  catalog_effective_date?: string;
  catalog_sha256?: string;
  catalog_owner?: string;
  applicant_kind?: string;
  products?: string[];
  branches?: Record<string, unknown>[];
  requirements?: DossierRequirement[];
  blocker_count?: number;
  excluded?: string[];
};
export type ApiProblemKind =
  "forbidden" | "not_found" | "conflict" | "validation" | "unavailable";

export class NetpayApiError extends Error {
  constructor(
    public status: number,
    public kind: ApiProblemKind,
    message: string,
  ) {
    super(message);
  }
}

export type NetpayRuntime = {
  baseUrl: string;
  organizationLabel: string;
  capabilities: ReadonlySet<string>;
};

function runtimeFromEnvironment(): NetpayRuntime {
  const env = import.meta.env;
  const capabilities = String(env.VITE_YARVIS_CAPABILITIES || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  return {
    baseUrl: env.VITE_API_BASE_URL || (env.PROD ? "" : "http://localhost:8000"),
    organizationLabel: env.VITE_YARVIS_ORGANIZATION_LABEL || "",
    capabilities: new Set(capabilities),
  };
}

export function newIdempotencyKey(): string {
  return (
    globalThis.crypto?.randomUUID?.() ||
    `intent-${Date.now()}-${Math.random().toString(16).slice(2)}`
  );
}

export class NetpayApiClient {
  readonly runtime: NetpayRuntime;

  constructor(runtime: NetpayRuntime = runtimeFromEnvironment()) {
    this.runtime = runtime;
  }

  can(capability: string): boolean {
    return this.runtime.capabilities.has(capability);
  }

  private async request<T>(
    path: string,
    init: RequestInit = {},
    idempotencyKey?: string,
  ): Promise<T> {
    const response = await fetch(`${this.runtime.baseUrl}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...(init.method && init.method !== "GET"
          ? { "X-CSRF-Token": csrfCookie() }
          : {}),
        ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
        ...(import.meta.env.VITE_YARVIS_SUBJECT
          ? { "X-Yarvis-Subject": import.meta.env.VITE_YARVIS_SUBJECT }
          : {}),
        ...(import.meta.env.VITE_YARVIS_AUTH_TOKEN
          ? { "X-Yarvis-Auth-Token": import.meta.env.VITE_YARVIS_AUTH_TOKEN }
          : {}),
        ...(init.headers || {}),
      },
    });
    if (!response.ok) {
      let detail = "";
      try {
        const body = await response.json();
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail || body);
      } catch {
        detail = await response.text();
      }
      const kind: ApiProblemKind =
        response.status === 403
          ? "forbidden"
          : response.status === 404
            ? "not_found"
            : response.status === 409
              ? "conflict"
              : response.status === 422
                ? "validation"
                : "unavailable";
      throw new NetpayApiError(
        response.status,
        kind,
        detail || "No fue posible completar la operación.",
      );
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  listMaster(query = "", offset = 0, limit = 100) {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    if (query) params.set("query", query);
    return this.request<MasterPage>(`/netpay/master?${params}`);
  }
  getMasterDetail(branchId: string) {
    return this.request<NetpayClient>(`/netpay/master/branches/${branchId}`);
  }
  createClient(payload: Record<string, unknown>, key: string) {
    return this.request<NetpayClient>(
      "/netpay/master/clients",
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  createCompany(
    clientId: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<NetpayCompany>(
      `/netpay/master/clients/${clientId}/companies`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  createBranch(
    companyId: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<NetpayBranch>(
      `/netpay/master/companies/${companyId}/branches`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  setStoreReference(
    branchId: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<NetpayStoreReference>(
      `/netpay/master/branches/${branchId}/store-reference`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }

  listInbox(
    filters: Record<string, string | boolean | number | undefined> = {},
  ) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(
      ([key, value]) =>
        value !== undefined && value !== "" && params.set(key, String(value)),
    );
    return this.request<InboxPage>(`/netpay/inbox?${params}`);
  }
  listGmailConnections() {
    return this.request<GmailConnection[]>("/netpay/gmail/connections");
  }
  validateGmailConnection(id: string, key: string) {
    return this.request<GmailConnection>(
      `/netpay/gmail/connections/${id}/validate`,
      { method: "POST" },
      key,
    );
  }
  disconnectGmailConnection(id: string, key: string) {
    return this.request<GmailConnection>(
      `/netpay/gmail/connections/${id}/disconnect`,
      { method: "POST" },
      key,
    );
  }
  syncGmailConnection(id: string, key: string) {
    return this.request<Record<string, unknown>>(
      `/netpay/gmail/connections/${id}/sync`,
      { method: "POST", body: JSON.stringify({ backfill_days: 30 }) },
      key,
    );
  }
  startGmailOAuth() {
    return this.request<{ authorization_url: string; expires_at: string }>(
      "/netpay/gmail/oauth/start",
      { method: "POST" },
    );
  }
  discoverGmailManifest(id: string) {
    return this.request<{ status: string }>(
      `/netpay/gmail/connections/${id}/manifest/discover`,
      { method: "POST" },
    );
  }
  approveGmailManifest(id: string) {
    return this.request<{ status: string }>(
      `/netpay/gmail/connections/${id}/manifest/approve`,
      { method: "POST" },
    );
  }
  listGmailCandidates(
    filters: Record<string, string | boolean | undefined> = {},
  ) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(
      ([key, value]) =>
        value !== undefined && value !== "" && params.set(key, String(value)),
    );
    return this.request<GmailCandidatePage>(
      `/netpay/gmail/candidates?${params}`,
    );
  }
  getGmailCandidate(id: string) {
    return this.request<GmailCandidate>(`/netpay/gmail/candidates/${id}`);
  }
  getGmailSourceItem(id: string) {
    return this.request<GmailSourceItem>(`/netpay/gmail/source-items/${id}`);
  }
  reviewGmailCandidate(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<GmailCandidate>(
      `/netpay/gmail/candidates/${id}/review`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  listCandidateFollowUps(id: string) {
    return this.request<CandidateHumanFollowUpPage>(
      `/netpay/gmail/candidates/${id}/follow-ups`,
    );
  }
  recordCandidateFollowUp(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CandidateHumanFollowUp>(
      `/netpay/gmail/candidates/${id}/follow-ups`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  listCandidateQualifications(id: string) {
    return this.request<CandidateQualification[]>(
      `/netpay/gmail/candidates/${id}/qualifications`,
    );
  }
  createCandidateQualification(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CandidateQualification>(
      `/netpay/gmail/candidates/${id}/qualifications`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  previewCandidateCommercialIntake(id: string) {
    return this.request<CommercialIntakePreview>(
      `/netpay/gmail/candidates/${id}/commercial-intake-preview`,
    );
  }
  promoteCandidateCommercialIntake(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<Record<string, unknown>>(
      `/netpay/gmail/candidates/${id}/commercial-intake`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  previewCandidateDossier(id: string) {
    return this.request<CandidateDossierPreview>(
      `/netpay/gmail/candidates/${id}/dossier-preview`,
    );
  }
  getCandidateDossier(id: string) {
    return this.request<CandidateDossier>(
      `/netpay/gmail/candidates/${id}/dossier`,
    );
  }
  createCandidateDossier(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CandidateDossier>(
      `/netpay/gmail/candidates/${id}/dossier`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  reviewCandidateDossierRequirement(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CandidateDossier>(
      `/netpay/gmail/candidates/${id}/dossier/reviews`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  getCase(caseId: string) {
    return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}`);
  }
  createCase(payload: Record<string, unknown>, key: string) {
    return this.request<NetpayCase>(
      "/netpay/inbox/cases",
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  updateChecklist(
    caseId: string,
    itemId: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<NetpayCase>(
      `/netpay/inbox/cases/${caseId}/checklist/${itemId}`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }
  assignCase(caseId: string, payload: Record<string, unknown>, key: string) {
    return this.request<NetpayCase>(
      `/netpay/inbox/cases/${caseId}/assignment`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }
  setNextAction(caseId: string, payload: Record<string, unknown>, key: string) {
    return this.request<NetpayCase>(
      `/netpay/inbox/cases/${caseId}/next-action`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }
  transitionCase(
    caseId: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<NetpayCase>(
      `/netpay/inbox/cases/${caseId}/state`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }
  addActivity(caseId: string, payload: Record<string, unknown>, key: string) {
    return this.request<NetpayCase>(
      `/netpay/inbox/cases/${caseId}/activities`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  listCommercialIntake(
    filters: Record<string, string | number | undefined> = {},
  ) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(
      ([key, value]) =>
        value !== undefined && value !== "" && params.set(key, String(value)),
    );
    return this.request<CommercialIntakePage>(
      `/netpay/inbox/contacts?${params}`,
    );
  }
  getCommercialIntake(id: string) {
    return this.request<CommercialIntake>(`/netpay/inbox/contacts/${id}`);
  }
  createCommercialIntake(payload: Record<string, unknown>, key: string) {
    return this.request<CommercialIntake>(
      "/netpay/inbox/contacts",
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  updateCommercialIntake(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CommercialIntake>(
      `/netpay/inbox/contacts/${id}`,
      { method: "PUT", body: JSON.stringify(payload) },
      key,
    );
  }
  discardCommercialIntake(id: string, key: string) {
    return this.request<CommercialIntake>(
      `/netpay/inbox/contacts/${id}/discard`,
      { method: "PUT", body: "{}" },
      key,
    );
  }
  convertCommercialIntake(
    id: string,
    payload: Record<string, unknown>,
    key: string,
  ) {
    return this.request<CommercialIntake>(
      `/netpay/inbox/contacts/${id}/convert`,
      { method: "POST", body: JSON.stringify(payload) },
      key,
    );
  }
  async uploadOperationalDataset(
    file: File,
    datasetType: string,
    rfcFilter: string,
    key: string,
  ) {
    const form = new FormData();
    form.append("file", file);
    form.append("dataset_type", datasetType);
    if (rfcFilter) form.append("rfc_filter", rfcFilter);
    return this.request<OperationalDataBatch>(
      "/netpay/data/datasets",
      { method: "POST", body: form },
      key,
    );
  }
  listOperationalDatasets(datasetType = "") {
    const query = datasetType
      ? `?dataset_type=${encodeURIComponent(datasetType)}`
      : "";
    return this.request<OperationalDataBatchPage>(
      `/netpay/data/datasets${query}`,
    );
  }
  getOperationalDataset(id: string) {
    return this.request<OperationalDataBatch>(`/netpay/data/datasets/${id}`);
  }
  acceptOperationalDataset(id: string, previewToken: string, key: string) {
    return this.request<OperationalDataBatch>(
      `/netpay/data/datasets/${id}/accept`,
      { method: "POST", body: JSON.stringify({ preview_token: previewToken }) },
      key,
    );
  }
  rejectOperationalDataset(id: string, key: string) {
    return this.request<OperationalDataBatch>(
      `/netpay/data/datasets/${id}/reject`,
      { method: "POST", body: "{}" },
      key,
    );
  }
  resolveOperationalRow(
    id: string,
    rowId: string,
    storeReferenceId: string,
    key: string,
  ) {
    return this.request<OperationalDataBatch>(
      `/netpay/data/datasets/${id}/rows/${rowId}/match`,
      {
        method: "PUT",
        body: JSON.stringify({ store_reference_id: storeReferenceId }),
      },
      key,
    );
  }
  getOperationalDatasetResults(id: string) {
    return this.request<Record<string, unknown>[]>(
      `/netpay/data/datasets/${id}/results`,
    );
  }
}

export const netpayApi = new NetpayApiClient();

function csrfCookie() {
  return decodeURIComponent(
    document.cookie
      .split("; ")
      .find((item) => item.startsWith("yarvis_csrf="))
      ?.split("=")[1] || "",
  );
}
export type ProductiveSession = {
  authenticated: boolean;
  organization_id: string;
  organization_label: string;
  capabilities: string[];
  expires_at: string;
};
export async function loadProductiveSession(): Promise<ProductiveSession> {
  const response = await fetch(
    `${runtimeFromEnvironment().baseUrl}/auth/session`,
    { credentials: "include" },
  );
  if (!response.ok)
    throw new NetpayApiError(
      response.status,
      response.status === 403 ? "forbidden" : "unavailable",
      "Authentication required",
    );
  const session = (await response.json()) as ProductiveSession;
  netpayApi.runtime.organizationLabel = session.organization_label;
  netpayApi.runtime.capabilities = new Set(session.capabilities);
  return session;
}
export function beginProductiveLogin(path = "/netpay-inbox") {
  window.location.assign(
    `${runtimeFromEnvironment().baseUrl}/auth/login?redirect=${encodeURIComponent(path)}`,
  );
}
export async function productiveLogout() {
  await fetch(`${runtimeFromEnvironment().baseUrl}/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrfCookie() },
  });
}

export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof NetpayApiError))
    return "No fue posible conectar con Netpay Inbox.";
  if (error.kind === "forbidden")
    return "No tienes autorización para esta operación.";
  if (error.kind === "not_found")
    return "El caso no existe o no está visible en esta organización.";
  if (error.kind === "conflict") return `Conflicto: ${error.message}`;
  if (error.kind === "validation") return `Revisa los datos: ${error.message}`;
  return error.message;
}
