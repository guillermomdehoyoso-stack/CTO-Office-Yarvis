import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { getOperationalWorkspace, MissionWorkApiError } from '../../api/missionWork';
import type { EconomicSummary, MissionWorkEvent, OperationalWorkspaceProcessInstance } from '../../types/missionWork';

function errorMessage(error: unknown): string {
  if (!(error instanceof MissionWorkApiError)) return 'No se pudo conectar con la API.';
  if (error.status === 404) return 'El espacio operativo no está disponible o no pertenece a tu organización.';
  if (error.status === 403) return 'No tienes autorización para consultar este espacio operativo.';
  return 'No se pudo conectar con la API.';
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function money(value: string | null, currency: string): string {
  if (value === null) return 'No disponible';
  const amount = Number(value);
  return Number.isFinite(amount) ? new Intl.NumberFormat('es-MX', { style: 'currency', currency }).format(amount) : value;
}

function eventDescription(event: MissionWorkEvent): string {
  const payload = event.payload;
  const transition = (from: string, to: string) => `${String(payload[from] ?? 'sin dato')} → ${String(payload[to] ?? 'sin dato')}`;
  switch (event.event_type) {
    case 'work_item.created': return 'Work Item creado.';
    case 'work_item.assigned':
    case 'work_item.unassigned': return `Responsable: ${transition('previous_assignee_subject_id', 'assignee_subject_id')}.`;
    case 'work_item.status_changed': return `Estado: ${transition('previous_status', 'status')}.`;
    case 'work_item.priority_changed': return `Prioridad: ${transition('previous_priority', 'priority')}.`;
    case 'comment.added': return typeof payload.comment === 'string' ? payload.comment : 'Comentario interno agregado.';
    case 'process_instance.started': return 'Instancia de proceso iniciada.';
    case 'process_instance.transitioned': return `Etapa: ${transition('previous_stage_key', 'current_stage_key')}.`;
    case 'process_instance.completed': return 'Instancia de proceso completada.';
    case 'process_instance.cancelled': return typeof payload.reason === 'string' ? `Proceso cancelado: ${payload.reason}` : 'Instancia de proceso cancelada.';
    case 'process_instance.work_linked': return 'Proceso vinculado al Work Item.';
    case 'process_instance.work_unlinked': return 'Proceso desvinculado del Work Item.';
    default: return `Evento registrado: ${event.event_type}.`;
  }
}

function EconomicSummaryPanel({ title, summary }: { title: string; summary: EconomicSummary }) {
  const metrics: Array<[string, string | null]> = [
    ['Ingreso esperado', summary.expected_revenue], ['Ingreso contratado', summary.contracted_revenue],
    ['Costo estimado', summary.estimated_cost], ['Costo comprometido', summary.committed_cost],
    ['Costo incurrido', summary.incurred_cost], ['Costo laboral', summary.labor_cost],
    ['Costo para completar', summary.estimated_cost_to_complete], ['Costo total proyectado', summary.projected_total_cost],
    ['Efectivo recibido', summary.cash_received], ['Efectivo pagado', summary.cash_paid],
    ['Posición neta de efectivo', summary.net_cash_position], ['Utilidad final esperada', summary.expected_final_profit],
  ];
  return <section className="card" aria-label={title}>
    <h2>{title}</h2>
    {summary.availability !== 'available' && <p>Resumen económico no disponible.</p>}
    <p><small>Moneda: {summary.currency} · Corte: <time title={summary.as_of}>{formatDate(summary.as_of)}</time></small></p>
    {metrics.map(([label, value]) => <p key={label}><strong>{label}:</strong> {money(value, summary.currency)}</p>)}
    <p><strong>Margen final esperado:</strong> {summary.expected_final_margin_percent === null ? 'No disponible' : `${summary.expected_final_margin_percent}%`}</p>
  </section>;
}

function ProcessInstanceCard({ process }: { process: OperationalWorkspaceProcessInstance }) {
  const activeLink = process.links.find((link) => link.unlinked_at === null);
  return <article className="item">
    <div>
      <h3>{process.process_definition_name} v{process.process_definition_version}</h3>
      <p>{process.lifecycle} · Etapa actual: {process.current_stage_name} ({process.current_stage_type})</p>
      <p>Última transición: {process.last_transition ? formatDate(process.last_transition.occurred_at) : 'Sin transición registrada'}</p>
      <p>Vínculo: {activeLink ? 'Activo' : 'Histórico'}</p>
      {process.cancellation_reason && <p>Razón de cancelación: {process.cancellation_reason}</p>}
    </div>
    <EconomicSummaryPanel title="Resumen económico directo del proceso" summary={process.economic_summary} />
  </article>;
}

export function OperationalWorkspace() {
  const { workItemId = '' } = useParams();
  const workspace = useQuery({
    queryKey: ['operational-workspace', workItemId, 'MXN'],
    queryFn: () => getOperationalWorkspace(workItemId, 'MXN'),
    enabled: Boolean(workItemId),
    retry: false,
  });

  if (workspace.isLoading) return <p>Cargando espacio operativo…</p>;
  if (workspace.error) return <section><h1>Operational Workspace</h1><p className="error">{errorMessage(workspace.error)}</p><Link to="/mission-work">Volver a Mission Work</Link></section>;
  if (!workspace.data) return <p>No hay datos disponibles para este espacio operativo.</p>;

  const data = workspace.data;
  const completedCount = data.process_instances.filter((process) => process.lifecycle === 'completed').length;
  return <section className="operational-workspace">
    <Link to="/mission-work">Volver a Mission Work</Link>
    <header>
      <h1>{data.work_item.title}</h1>
      <p>{data.work_item.summary || 'Sin resumen'}</p>
      <p>Estado: <strong>{data.work_item.status}</strong> · Prioridad: <strong>{data.work_item.priority}</strong> · Responsable: {data.work_item.assignee_subject_id || 'Sin asignar'}</p>
      <p>Participantes: {data.participants.length ? data.participants.join(', ') : 'Sin participantes registrados'}</p>
      <p>Última actividad: <time title={data.last_activity_at}>{formatDate(data.last_activity_at)}</time></p>
    </header>
    <section className="workspace-grid" aria-label="Indicadores de procesos">
      <article className="card"><small>Procesos activos</small><b>{data.active_process_instance_count}</b></article>
      <article className="card"><small>Procesos completados</small><b>{completedCount}</b></article>
      <article className="card"><small>Vínculos históricos</small><b>{data.historical_process_instance_count}</b></article>
    </section>
    <EconomicSummaryPanel title="Resumen económico directo del Work Item" summary={data.economic_summary} />
    <section aria-label="Instancias de proceso relacionadas"><h2>Procesos relacionados</h2>
      {data.process_instances.length === 0 ? <p>No hay instancias de proceso relacionadas.</p> : data.process_instances.map((process) => <div key={process.id}><ProcessInstanceCard process={process} /></div>)}
    </section>
    <section aria-label="Timeline operativo"><h2>Timeline operativo</h2>
      {data.timeline.items.length === 0 ? <p>No hay eventos registrados para este Work Item.</p> : data.timeline.items.map((event) => <article className="item" key={event.id}>
        <div><strong>{event.event_type}</strong><p>{eventDescription(event)}</p>{event.actor_subject_id && <p>Actor: {event.actor_subject_id}</p>}</div>
        <time title={event.occurred_at} dateTime={event.occurred_at}>{formatDate(event.occurred_at)}</time>
      </article>)}
    </section>
  </section>;
}
