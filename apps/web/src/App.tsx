import { Link, Navigate, Route, Routes, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { getRecoveryQueue, getStoreSummary } from './api/storeIntelligence';
import type { RecoveryQueueResult, StoreOperationalProfile } from './types/storeIntelligence';
import {RecoveryQueueWorkspace} from './components/store-intelligence/RecoveryQueueWorkspace';
import {MissionControlStoreIntelligenceCard} from './components/store-intelligence/MissionControlStoreIntelligenceCard';
import { WorkspaceShell } from './workspace-shell/WorkspaceShell';
import { MissionWorkQueue } from './components/mission-work/MissionWorkQueue';
import { OperationalWorkspace } from './components/mission-work/OperationalWorkspace';
import { OperationalRadar } from './components/radar/OperationalRadar';
import { CommercialIntakeDetail, NetpayCaseDetail, NetpayInboxWorkspace } from './components/netpay/NetpayInboxWorkspace';
import { NetpayDataWorkspace } from './components/netpay/NetpayDataWorkspace';
import { beginProductiveLogin, loadProductiveSession, productiveLogout } from './api/netpay';

const api = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function csrfToken() {
  return decodeURIComponent(document.cookie.split('; ').find((item) => item.startsWith('yarvis_csrf='))?.split('=')[1] || '');
}

async function getJson(path: string) {
  const response = await fetch(api + path, { credentials: 'include' });
  if (!response.ok) {
    throw new Error('API unavailable');
  }
  return response.json();
}

async function postJson(path: string, body?: unknown) {
  const response = await fetch(api + path, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken() },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error('API unavailable');
  }
  return response.json();
}

async function uploadXlsx(file: File) {
  const form = new FormData();
  form.append('file', file);
  form.append('source_type', 'manual_upload');
  form.append('source_name', 'Manual XLSX Upload');
  form.append('classification', 'confidential');
  const response = await fetch(api + '/data-intake/documents', { method: 'POST', credentials: 'include', headers: { 'X-CSRF-Token': csrfToken() }, body: form });
  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

function Layout({ productive = false }: { productive?: boolean }) {
  return (
    <main>
      <nav>
        <Link to="/">Mission Control</Link>
        <Link to="/cases">Cases</Link>
        <Link to="/conversation">Conversación</Link>
        <Link to="/organizations">Organización</Link>
        <Link to="/people">Personas</Link>
        <Link to="/netpay-inbox">Netpay Inbox</Link>
        <Link to="/netpay-data">Datos Netpay</Link>
        <Link to="/recovery-queue">Cola de recuperación</Link>
        <Link to="/workspace">Development Workspace</Link>
        <Link to="/mission-work">Mission Work</Link>
        {productive ? <button onClick={async () => { await productiveLogout(); window.location.reload(); }}>Cerrar sesión</button> : null}
      </nav>
      <Routes>
        <Route path="/" element={<MissionControlPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/:id" element={<CaseDetailPage />} />
        <Route path="/conversation" element={<ConversationPage />} />
        <Route path="/organizations" element={<OrganizationsPage />} />
        <Route path="/people" element={<PeoplePage />} />
        <Route path="/netpay-intake" element={<Navigate to="/netpay-data" replace />} />
        <Route path="/radar-netpay" element={<OperationalRadar />} />
        <Route path="/netpay-inbox" element={<NetpayInboxWorkspace />} />
        <Route path="/netpay-inbox/contacts/:contactId" element={<CommercialIntakeDetail />} />
        <Route path="/netpay-inbox/:caseId" element={<NetpayCaseDetail />} />
        <Route path="/netpay-data" element={<NetpayDataWorkspace />} />
        <Route path="/recovery-queue" element={<RecoveryQueuePage />} />
        <Route path="/workspace/*" element={<WorkspaceShell />} />
        <Route path="/mission-work" element={<MissionWorkQueue />} />
        <Route path="/mission-work/:workItemId/workspace" element={<OperationalWorkspace />} />
      </Routes>
    </main>
  );
}

function ProductiveAuthBoundary() {
  const session = useQuery({ queryKey: ['productive-session'], queryFn: loadProductiveSession, retry: false });
  if (session.isLoading) return <main><p>Cargando sesión…</p></main>;
  if (session.isError) return <main><h1>Acceso a Yarvis</h1><p>Inicia sesión para continuar.</p><button onClick={() => beginProductiveLogin()}>Iniciar sesión</button></main>;
  return <Layout productive />;
}

function MissionControlPage() {
  const missionQuery = useQuery({ queryKey: ['mission'], queryFn: () => getJson('/mission-control/summary'), retry: false });
  const storeQuery = useQuery({ queryKey: ['store-intelligence-summary'], queryFn: getStoreSummary, retry: false });
  if (missionQuery.error) return <p className="error">No se pudo conectar con la API.</p>;
  const operationalMetrics = ['pending_reports', 'critical_stores', 'churn_candidates', 'assets_without_store', 'identity_conflicts'];
  const items: any[] = [];

  return (
    <>
      <h1>Mission Control</h1>
      <div className="cards">
        {missionQuery.data && Object.entries(missionQuery.data).filter(([key]) => operationalMetrics.includes(key)).map(([key, value]) => (
          <div className="card" key={key}>
            <small>{key.replaceAll('_', ' ')}</small>
            <b>{String(value)}</b>
          </div>
        ))}
      </div>
      {items.map((item: any) => (
        <Link className="item" to={'/cases/' + item.case_id} key={item.case_id}>
          <b>{item.case_number}</b>
          <span>{item.title}</span>
          <em>{item.highest_severity} · {item.alert_count} alertas</em>
        </Link>
      ))}
    </>
  );
}

function CasesPage() {
  const { data } = useQuery({ queryKey: ['cases'], queryFn: () => getJson('/cases') });
  const [query, setQuery] = useState('');
  const items = Array.isArray(data) ? data : [];

  return (
    <>
      <h1>Cases</h1>
      <input placeholder="Buscar" value={query} onChange={(event) => setQuery(event.target.value)} />
      {items.filter((item: any) => item.title.toLowerCase().includes(query.toLowerCase())).map((item: any) => (
        <Link className="item" to={'/cases/' + item.id} key={item.id}>
          {item.case_number} · {item.title}
        </Link>
      ))}
    </>
  );
}

function CaseDetailPage() {
  const { id = '' } = useParams();
  const { data: caseData } = useQuery({ queryKey: ['case', id], queryFn: () => getJson('/cases/' + id) });
  const { data: events = [] } = useQuery({ queryKey: ['events', id], queryFn: () => getJson('/cases/' + id + '/events') });
  const { data: alerts = [] } = useQuery({ queryKey: ['alerts', id], queryFn: () => getJson('/cases/' + id + '/alerts') });

  return (
    <>
      <h1>{caseData?.title || 'Case'}</h1>
      <p>{caseData?.case_number} · {caseData?.status}</p>
      <h2>Alerts</h2>
      {alerts.map((alert: any) => (
        <p key={alert.id}>{alert.alert_type}: {alert.status}</p>
      ))}
      <h2>Events</h2>
      {events.map((event: any) => (
        <p key={event.id}>{event.event_type}</p>
      ))}
    </>
  );
}

function ConversationPage() {
  const [text, setText] = useState('');
  const [conversation, setConversation] = useState<any>();
  const [messages, setMessages] = useState<any[]>([]);
  const [notice, setNotice] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [personId, setPersonId] = useState('');
  const [caseId, setCaseId] = useState('');
  const [attachmentName, setAttachmentName] = useState('');
  const [contextStatus, setContextStatus] = useState('Pendiente de confirmación');
  const [intakeItemId, setIntakeItemId] = useState<string | null>(null);

  const { data: organizationsData } = useQuery({ queryKey: ['organizations'], queryFn: () => getJson('/organizations') });
  const { data: peopleData } = useQuery({ queryKey: ['people'], queryFn: () => getJson('/people') });
  const { data: casesData } = useQuery({ queryKey: ['all-cases'], queryFn: () => getJson('/cases') });
  const organizations = Array.isArray(organizationsData) ? organizationsData : [];
  const people = Array.isArray(peopleData) ? peopleData : [];
  const cases = Array.isArray(casesData) ? casesData : [];

  useEffect(() => {
    if (!conversation?.id) return;
    getJson(`/conversations/${conversation.id}`).then((payload) => setMessages(payload.messages || [])).catch(() => undefined);
  }, [conversation?.id]);

  async function sendMessage() {
    let currentConversation = conversation;
    if (!currentConversation) {
      currentConversation = await postJson('/conversations', {
        title: 'Conversación de intake',
        organization_id: organizationId || undefined,
        person_id: personId || undefined,
        case_id: caseId || undefined,
      });
      setConversation(currentConversation);
    }

    const response = await postJson(`/conversations/${currentConversation.id}/messages`, { text_content: text });
    setMessages((existing) => [...existing, response.message]);
    setNotice(response.system_message);
    setText('');
    if (response.intake_item_id) {
      setIntakeItemId(response.intake_item_id);
      setContextStatus('IntakeItem creado. Confirma el contexto para completar la traza.');
    }
  }

  async function confirmContext() {
    if (!intakeItemId) return;
    const response = await postJson(`/intake/${intakeItemId}/confirm-context`, {
      organization_id: organizationId || undefined,
      person_id: personId || undefined,
      case_id: caseId || undefined,
      evidence_type: 'document',
    });
    if (response.status === 'confirmed') {
      setContextStatus('Contexto confirmado');
    }
  }

  async function registerAttachment() {
    if (!conversation?.id || !attachmentName) return;
    const response = await postJson(`/conversations/${conversation.id}/attachments`, {
      original_filename: attachmentName,
      description: 'Adjunto desde la UI',
      mime_type: 'application/octet-stream',
    });
    setNotice(`Adjunto registrado como metadato. Intake ${response.intake_item_id}`);
    setAttachmentName('');
  }

  return (
    <>
      <h1>Conversación</h1>
      <section className="chat">
        <p>{notice || 'Selecciona contexto si lo tienes; puedes confirmarlo después.'}</p>
        {messages.map((message: any) => (
          <p key={message.id}>{message.role}: {message.text_content}</p>
        ))}
      </section>
      <aside>
        <label>
          Organización
          <select value={organizationId} onChange={(event) => setOrganizationId(event.target.value)}>
            <option value="">Seleccione</option>
            {organizations.map((org: any) => (
              <option key={org.id} value={org.id}>{org.display_name}</option>
            ))}
          </select>
        </label>
        <label>
          Persona
          <select value={personId} onChange={(event) => setPersonId(event.target.value)}>
            <option value="">Seleccione</option>
            {people.map((person: any) => (
              <option key={person.id} value={person.id}>{person.display_name}</option>
            ))}
          </select>
        </label>
        <label>
          Caso
          <select value={caseId} onChange={(event) => setCaseId(event.target.value)}>
            <option value="">Seleccione</option>
            {cases.map((item: any) => (
              <option key={item.id} value={item.id}>{item.case_number}</option>
            ))}
          </select>
        </label>
        <button onClick={confirmContext}>Confirmar contexto</button>
        <p>{contextStatus}</p>
      </aside>
      <input value={attachmentName} onChange={(event) => setAttachmentName(event.target.value)} placeholder="Nombre del adjunto" />
      <button onClick={registerAttachment}>Registrar adjunto</button>
      <textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Escribe un mensaje" />
      <button onClick={sendMessage}>Enviar</button>
    </>
  );
}

function NetPayIntakePage() {
  const [file, setFile] = useState<File | null>(null);
  const [documentId, setDocumentId] = useState('');
  const [preview, setPreview] = useState<any>();
  const [reviewer, setReviewer] = useState('');
  const [message, setMessage] = useState('Select a confidential NetPay XLSX file.');

  async function uploadAndPreview() {
    if (!file || !file.name.toLowerCase().endsWith('.xlsx')) {
      setMessage('Select an XLSX file.');
      return;
    }
    try {
      const uploaded = await uploadXlsx(file);
      setDocumentId(uploaded.document_id);
      await postJson(`/data-intake/documents/${uploaded.document_id}/process`);
      setPreview(await getJson(`/data-intake/documents/${uploaded.document_id}/preview`));
      setMessage(uploaded.duplicate ? 'Duplicate detected. No second binary was stored.' : 'Preview ready. Confirm to enrich Operational Memory.');
    } catch {
      setMessage('The XLSX could not be processed.');
    }
  }

  async function confirm() {
    if (!documentId || !reviewer.trim()) {
      setMessage('Enter the confirming reviewer.');
      return;
    }
    try {
      await postJson(`/data-intake/documents/${documentId}/confirm`, { reviewer });
      setMessage('Confirmed. Mission Control and Operational Memory are updated.');
    } catch {
      setMessage('The report could not be confirmed.');
    }
  }

  return <>
    <h1>NetPay XLSX Intake</h1>
    <p>{message}</p>
    <input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => setFile(event.target.files?.[0] || null)} />
    <button onClick={uploadAndPreview}>Upload and preview</button>
    {preview && <section className="intake-preview">
      <h2>{preview.detected_report_type === 'netpay_weekly_sales_report' ? 'Weekly Sales Report' : 'Unknown Report'}</h2>
      <p>Worksheet: {preview.worksheets[0]} | Rows: {preview.total_rows} | Candidate observations: {preview.candidate_observation_count}</p>
      <h3>Operational summary</h3>
      <div className="cards">
        {Object.entries(preview.operational_summary || {}).filter(([, value]) => typeof value === 'number').map(([key, value]) => <div className="card" key={key}><small>{key.replaceAll('_', ' ')}</small><b>{String(value)}</b></div>)}
      </div>
      <MissionControlStoreIntelligenceCard data={storeQuery.data} error={Boolean(storeQuery.error)} />
      <h3>Column mappings</h3>
      {preview.proposed_canonical_mappings.map((mapping: any) => <p className="mapping" key={mapping.source_header}><code>{mapping.source_header}</code> to {mapping.canonical_field || 'unresolved'}</p>)}
      <p>Unavailable: {(preview.operational_summary?.unavailable_fields || []).join(', ') || 'none'}.</p>
      <label>Confirmed by<input value={reviewer} onChange={(event) => setReviewer(event.target.value)} /></label>
      <button onClick={confirm}>Confirm operational summary</button>
    </section>}
  </>;
}

function RecoveryQueuePage() { return <RecoveryQueueWorkspace />; }

function OrganizationsPage() {
  const { data } = useQuery({ queryKey: ['organizations-list'], queryFn: () => getJson('/organizations') });
  const items = Array.isArray(data) ? data : [];
  return <><h1>Organizations</h1>{items.map((item: any) => <p key={item.id}>{item.display_name}</p>)}</>;
}

function PeoplePage() {
  const { data } = useQuery({ queryKey: ['people-list'], queryFn: () => getJson('/people') });
  const items = Array.isArray(data) ? data : [];
  return <><h1>People</h1>{items.map((item: any) => <p key={item.id}>{item.display_name}</p>)}</>;
}

function App() {
  const queryClient = useMemo(() => new QueryClient(), []);

  return (
    <QueryClientProvider client={queryClient}>
      {import.meta.env.PROD ? <ProductiveAuthBoundary /> : <Layout />}
    </QueryClientProvider>
  );
}

export default App;
