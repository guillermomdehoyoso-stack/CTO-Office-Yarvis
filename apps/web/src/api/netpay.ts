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
  branch_kind: 'physical' | 'commercial';
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

export type MasterPage = { items: NetpayClient[]; offset: number; limit: number; total: number };
export type ChecklistItem = { id: string; requirement_key: string; status: string; required: boolean; safe_evidence_reference: string | null; template_version: number };
export type CaseStep = { id: string; ordinal: number; description: string; status: string };
export type NextAction = { id: string; description: string; status: string; responsible_principal_id: string | null; due_date: string | null; origin: string };
export type CaseActivity = { id: string; type: string; summary: string; created_at: string };
export type DocumentReference = { id: string; status: string; external_evidence_reference: string | null };

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

export type InboxPage = { items: NetpayCase[]; offset: number; limit: number; total: number };
export type ApiProblemKind = 'forbidden' | 'not_found' | 'conflict' | 'validation' | 'unavailable';

export class NetpayApiError extends Error {
  constructor(public status: number, public kind: ApiProblemKind, message: string) {
    super(message);
  }
}

export type NetpayRuntime = {
  baseUrl: string;
  subject: string;
  organizationSelector: string;
  organizationLabel: string;
  authToken: string;
  capabilities: ReadonlySet<string>;
};

function runtimeFromEnvironment(): NetpayRuntime {
  const env = import.meta.env;
  return {
    baseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000',
    subject: env.VITE_YARVIS_SUBJECT || '',
    organizationSelector: env.VITE_YARVIS_ORGANIZATION_SELECTOR || '',
    organizationLabel: env.VITE_YARVIS_ORGANIZATION_LABEL || '',
    authToken: env.VITE_YARVIS_AUTH_TOKEN || '',
    capabilities: new Set((env.VITE_YARVIS_CAPABILITIES || '').split(',').map((item: string) => item.trim()).filter(Boolean)),
  };
}

export function newIdempotencyKey(): string {
  return globalThis.crypto?.randomUUID?.() || `intent-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export class NetpayApiClient {
  readonly runtime: NetpayRuntime;

  constructor(runtime: NetpayRuntime = runtimeFromEnvironment()) {
    this.runtime = runtime;
  }

  can(capability: string): boolean {
    return this.runtime.capabilities.has(capability);
  }

  private async request<T>(path: string, init: RequestInit = {}, idempotencyKey?: string): Promise<T> {
    if (!this.runtime.subject || !this.runtime.organizationSelector || !this.runtime.authToken) {
      throw new NetpayApiError(0, 'unavailable', 'La identidad local de Netpay no está configurada.');
    }
    const response = await fetch(`${this.runtime.baseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'X-Yarvis-Subject': this.runtime.subject,
        'X-Yarvis-Auth-Token': this.runtime.authToken,
        'X-Yarvis-Organization-Selector': this.runtime.organizationSelector,
        ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
        ...(init.headers || {}),
      },
    });
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json();
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
      } catch {
        detail = await response.text();
      }
      const kind: ApiProblemKind = response.status === 403 ? 'forbidden' : response.status === 404 ? 'not_found' : response.status === 409 ? 'conflict' : response.status === 422 ? 'validation' : 'unavailable';
      throw new NetpayApiError(response.status, kind, detail || 'No fue posible completar la operación.');
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  listMaster(query = '', offset = 0, limit = 100) {
    const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
    if (query) params.set('query', query);
    return this.request<MasterPage>(`/netpay/master?${params}`);
  }
  getMasterDetail(branchId: string) { return this.request<NetpayClient>(`/netpay/master/branches/${branchId}`); }
  createClient(payload: Record<string, unknown>, key: string) { return this.request<NetpayClient>('/netpay/master/clients', { method: 'POST', body: JSON.stringify(payload) }, key); }
  createCompany(clientId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCompany>(`/netpay/master/clients/${clientId}/companies`, { method: 'POST', body: JSON.stringify(payload) }, key); }
  createBranch(companyId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayBranch>(`/netpay/master/companies/${companyId}/branches`, { method: 'POST', body: JSON.stringify(payload) }, key); }
  setStoreReference(branchId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayStoreReference>(`/netpay/master/branches/${branchId}/store-reference`, { method: 'PUT', body: JSON.stringify(payload) }, key); }

  listInbox(filters: Record<string, string | boolean | number | undefined> = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => value !== undefined && value !== '' && params.set(key, String(value)));
    return this.request<InboxPage>(`/netpay/inbox?${params}`);
  }
  getCase(caseId: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}`); }
  createCase(payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>('/netpay/inbox/cases', { method: 'POST', body: JSON.stringify(payload) }, key); }
  updateChecklist(caseId: string, itemId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}/checklist/${itemId}`, { method: 'PUT', body: JSON.stringify(payload) }, key); }
  assignCase(caseId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}/assignment`, { method: 'PUT', body: JSON.stringify(payload) }, key); }
  setNextAction(caseId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}/next-action`, { method: 'PUT', body: JSON.stringify(payload) }, key); }
  transitionCase(caseId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}/state`, { method: 'PUT', body: JSON.stringify(payload) }, key); }
  addActivity(caseId: string, payload: Record<string, unknown>, key: string) { return this.request<NetpayCase>(`/netpay/inbox/cases/${caseId}/activities`, { method: 'POST', body: JSON.stringify(payload) }, key); }
}

export const netpayApi = new NetpayApiClient();

export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof NetpayApiError)) return 'No fue posible conectar con Netpay Inbox.';
  if (error.kind === 'forbidden') return 'No tienes autorización para esta operación.';
  if (error.kind === 'not_found') return 'El caso no existe o no está visible en esta organización.';
  if (error.kind === 'conflict') return `Conflicto: ${error.message}`;
  if (error.kind === 'validation') return `Revisa los datos: ${error.message}`;
  return error.message;
}
