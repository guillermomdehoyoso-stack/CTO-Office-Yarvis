import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  addMissionWorkComment,
  assignMissionWorkItem,
  changeMissionWorkPriority,
  changeMissionWorkStatus,
  createMissionWorkItem,
  getMissionWorkAccess,
  getMissionWorkItem,
  getMissionWorkTimeline,
  hasMissionWorkAuthority,
  listMissionInboxItems,
  listMissionWorkItems,
  MissionWorkApiError,
  setMissionWorkAccess,
} from '../../api/missionWork';
import {
  MISSION_WORK_PRIORITIES,
  MISSION_WORK_STATUSES,
  type MissionWorkPriority,
  type MissionWorkStatus,
  type MissionWorkEvent,
} from '../../types/missionWork';

const WORK_AUTHORITIES = [
  'mission.work.read',
  'mission.work.create',
  'mission.work.assign',
  'mission.work.status.change',
  'mission.work.priority.change',
  'mission.inbox.read',
];

function errorMessage(error: unknown): string {
  if (!(error instanceof MissionWorkApiError)) return 'No se pudo conectar con la API.';
  if (error.status === 404) return 'El recurso ya no está disponible o no pertenece a tu organización.';
  if (error.status === 409) return 'La operación entra en conflicto con el estado gobernado actual.';
  if (error.status === 403) return 'No tienes autorización para esta acción.';
  return 'No se pudo conectar con la API.';
}

function textValue(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key];
  return typeof value === 'string' && value.trim() ? value : null;
}

function transition(payload: Record<string, unknown>, previousKey: string, currentKey: string): string | null {
  const previous = payload[previousKey] === null ? 'sin asignar' : textValue(payload, previousKey) || 'sin dato';
  const current = payload[currentKey] === null ? 'sin asignar' : textValue(payload, currentKey) || 'sin dato';
  return `${previous} → ${current}`;
}

function timelineDescription(event: MissionWorkEvent): string {
  const payload = event.payload;
  switch (event.event_type) {
    case 'work_item.created':
      return `Work Item creado: estado ${textValue(payload, 'status') || 'sin dato'}; prioridad ${textValue(payload, 'priority') || 'sin dato'}.`;
    case 'work_item.assigned':
      return `Responsable: ${transition(payload, 'previous_assignee_subject_id', 'assignee_subject_id')}. Estado: ${transition(payload, 'previous_status', 'status')}.`;
    case 'work_item.unassigned':
      return `Responsable: ${transition(payload, 'previous_assignee_subject_id', 'assignee_subject_id')}. Estado: ${transition(payload, 'previous_status', 'status')}.`;
    case 'work_item.status_changed':
      return `Estado: ${transition(payload, 'previous_status', 'status')}.`;
    case 'work_item.priority_changed':
      return `Prioridad: ${transition(payload, 'previous_priority', 'priority')}.`;
    case 'comment.added':
      return textValue(payload, 'comment') || 'Comentario interno agregado.';
    default:
      return `Evento desconocido: ${event.event_type}.`;
  }
}

function timelineLabel(eventType: string): string {
  return {
    'work_item.created': 'Work Item creado',
    'work_item.assigned': 'Work Item asignado',
    'work_item.unassigned': 'Work Item desasignado',
    'work_item.status_changed': 'Estado actualizado',
    'work_item.priority_changed': 'Prioridad actualizada',
    'comment.added': 'Comentario interno',
  }[eventType] || 'Evento desconocido';
}

function timelineDate(timestamp: string): string {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(date);
}

function AccessConfiguration({ onSaved }: { onSaved: () => void }) {
  const existing = getMissionWorkAccess();
  const [actorId, setActorId] = useState(existing?.actorId || '');
  const [organizationId, setOrganizationId] = useState(existing?.organizationId || '');
  const [token, setToken] = useState(existing?.token || '');
  const [authorities, setAuthorities] = useState<string[]>(existing?.authorities || []);

  function save(event: FormEvent) {
    event.preventDefault();
    setMissionWorkAccess({
      actorId: actorId.trim(),
      organizationId: organizationId.trim(),
      token: token.trim(),
      authorities,
    });
    onSaved();
  }

  return (
    <details>
      <summary>Configurar acceso de Mission Work</summary>
      <form onSubmit={save}>
        <label>Actor<input aria-label="Actor" value={actorId} onChange={(event) => setActorId(event.target.value)} required /></label>
        <label>Organización<input aria-label="Organización" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} required /></label>
        <label>Token<input aria-label="Token" value={token} onChange={(event) => setToken(event.target.value)} required /></label>
        <fieldset>
          <legend>Authorities</legend>
          {WORK_AUTHORITIES.map((authority) => (
            <label key={authority}>
              <input
                type="checkbox"
                checked={authorities.includes(authority)}
                onChange={(event) => setAuthorities((current) => (
                  event.target.checked ? [...current, authority] : current.filter((value) => value !== authority)
                ))}
              />
              {authority}
            </label>
          ))}
        </fieldset>
        <button type="submit">Guardar acceso</button>
      </form>
    </details>
  );
}

export function MissionWorkQueue() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [accessRevision, setAccessRevision] = useState(0);
  const [status, setStatus] = useState<MissionWorkStatus | ''>('');
  const [priority, setPriority] = useState<MissionWorkPriority | ''>('');
  const [assignee, setAssignee] = useState('');
  const [assignment, setAssignment] = useState('');
  const [comment, setComment] = useState('');
  const [offset, setOffset] = useState(0);
  const [notice, setNotice] = useState('');
  const creationAttemptedForInbox = useRef(new Set<string>());
  const workItemId = searchParams.get('work_item_id') || '';
  const canRead = hasMissionWorkAuthority('mission.work.read');
  const canReadInbox = hasMissionWorkAuthority('mission.inbox.read');
  const canCreate = hasMissionWorkAuthority('mission.work.create');
  const canAssign = hasMissionWorkAuthority('mission.work.assign');
  const canChangeStatus = hasMissionWorkAuthority('mission.work.status.change');
  const canChangePriority = hasMissionWorkAuthority('mission.work.priority.change');
  const filters = useMemo(() => ({
    status: status || undefined,
    priority: priority || undefined,
    assignee_subject_id: assignee || undefined,
    limit: 20,
    offset,
  }), [status, priority, assignee, offset]);

  const workItems = useQuery({
    queryKey: ['mission-work-items', filters, accessRevision],
    queryFn: () => listMissionWorkItems(filters),
    enabled: canRead,
    retry: false,
  });
  const detail = useQuery({
    queryKey: ['mission-work-item', workItemId, accessRevision],
    queryFn: () => getMissionWorkItem(workItemId),
    enabled: canRead && Boolean(workItemId),
    retry: false,
  });
  const timeline = useQuery({
    queryKey: ['mission-work-timeline', workItemId, accessRevision],
    queryFn: () => getMissionWorkTimeline(workItemId),
    enabled: canRead && Boolean(workItemId),
    retry: false,
  });
  const inbox = useQuery({
    queryKey: ['mission-inbox-for-work', accessRevision],
    queryFn: listMissionInboxItems,
    enabled: canReadInbox,
    retry: false,
  });

  useEffect(() => setOffset(0), [status, priority, assignee]);
  useEffect(() => setAssignment(detail.data?.assignee_subject_id || ''), [detail.data?.id, detail.data?.assignee_subject_id]);

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['mission-work-items'] });
    await queryClient.invalidateQueries({ queryKey: ['mission-work-item'] });
    await queryClient.invalidateQueries({ queryKey: ['mission-work-timeline'] });
  };
  const open = (id: string) => setSearchParams({ work_item_id: id });
  const close = () => setSearchParams({});

  const create = useMutation({
    mutationFn: ({ inboxItemId }: { inboxItemId: string; sourceType: string; sourceId: string }) => createMissionWorkItem(inboxItemId),
    onSuccess: async (item) => {
      setNotice('Work Item creado.');
      open(item.id);
      await refresh();
    },
    onError: async (error, variables) => {
      if (error instanceof MissionWorkApiError && error.status === 409 && canRead) {
        try {
          const existing = await listMissionWorkItems({
            source_type: variables.sourceType,
            source_id: variables.sourceId,
            limit: 1,
          });
          if (existing.items[0]) {
            setNotice('Ya existe un Work Item para este elemento de Inbox.');
            open(existing.items[0].id);
            return;
          }
        } catch {
          // Preserve the governed conflict message when recovery is not authorized or unavailable.
        }
      }
      if (!(error instanceof MissionWorkApiError && error.status === 409)) {
        creationAttemptedForInbox.current.delete(variables.inboxItemId);
      }
      setNotice(errorMessage(error));
    },
  });
  const assign = useMutation({
    mutationFn: ({ id, subject }: { id: string; subject: string | null }) => assignMissionWorkItem(id, subject),
    onSuccess: async () => {
      setNotice('Asignación actualizada.');
      await refresh();
    },
    onError: (error) => setNotice(errorMessage(error)),
  });
  const changeStatus = useMutation({
    mutationFn: ({ id, value }: { id: string; value: MissionWorkStatus }) => changeMissionWorkStatus(id, value),
    onSuccess: async () => {
      setNotice('Estado actualizado.');
      await refresh();
    },
    onError: (error) => setNotice(errorMessage(error)),
  });
  const changePriority = useMutation({
    mutationFn: ({ id, value }: { id: string; value: MissionWorkPriority }) => changeMissionWorkPriority(id, value),
    onSuccess: async () => {
      setNotice('Prioridad actualizada.');
      await refresh();
    },
    onError: (error) => setNotice(errorMessage(error)),
  });
  const addComment = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) => addMissionWorkComment(id, value),
    onSuccess: async () => {
      setComment('');
      setNotice('Comentario agregado.');
      await queryClient.invalidateQueries({ queryKey: ['mission-work-timeline'] });
    },
    onError: (error) => setNotice(errorMessage(error)),
  });

  const selected = detail.data;
  const mutationPending = create.isPending || assign.isPending || changeStatus.isPending || changePriority.isPending || addComment.isPending;

  function submitAssignment(event: FormEvent) {
    event.preventDefault();
    if (!selected || mutationPending) return;
    assign.mutate({ id: selected.id, subject: assignment.trim() || null });
  }

  function startCreate(inboxItemId: string) {
    if (creationAttemptedForInbox.current.has(inboxItemId) || create.isPending) return;
    creationAttemptedForInbox.current.add(inboxItemId);
    const inboxItem = inbox.data?.items.find((item) => item.id === inboxItemId);
    if (!inboxItem) {
      creationAttemptedForInbox.current.delete(inboxItemId);
      return;
    }
    create.mutate({ inboxItemId, sourceType: inboxItem.source_type, sourceId: inboxItem.source_id });
  }

  function submitComment(event: FormEvent) {
    event.preventDefault();
    if (!selected || !comment.trim() || addComment.isPending) return;
    addComment.mutate({ id: selected.id, value: comment.trim() });
  }

  return (
    <>
      <h1>Mission Work Queue</h1>
      <AccessConfiguration onSaved={() => {
        setAccessRevision((value) => value + 1);
        setNotice('Acceso actualizado.');
      }} />
      {notice && <p role="status">{notice}</p>}

      {!canRead ? <p className="error">No tienes autorización para leer Mission Work.</p> : (
        <>
          <section className="cards" aria-label="Filtros de Mission Work">
            <label>Estado<select aria-label="Filtrar estado" value={status} onChange={(event) => setStatus(event.target.value as MissionWorkStatus | '')}><option value="">Todos</option>{MISSION_WORK_STATUSES.map((value) => <option value={value} key={value}>{value}</option>)}</select></label>
            <label>Prioridad<select aria-label="Filtrar prioridad" value={priority} onChange={(event) => setPriority(event.target.value as MissionWorkPriority | '')}><option value="">Todas</option>{MISSION_WORK_PRIORITIES.map((value) => <option value={value} key={value}>{value}</option>)}</select></label>
            <label>Asignado a<input aria-label="Filtrar asignado a" value={assignee} onChange={(event) => setAssignee(event.target.value)} /></label>
          </section>
          {workItems.isLoading && <p>Cargando Mission Work…</p>}
          {workItems.error && <p className="error">{errorMessage(workItems.error)}</p>}
          {workItems.data?.items.length === 0 && <p>No hay Work Items para estos filtros.</p>}
          {workItems.data?.items.map((item) => (
            <button className="item" type="button" key={item.id} onClick={() => open(item.id)}>
              <b>{item.title}</b><span>{item.status} · {item.priority}</span><em>{item.assignee_subject_id || 'Sin asignar'}</em>
            </button>
          ))}
          {workItems.data && (
            <p>Mostrando {workItems.data.items.length} de {workItems.data.total}. <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - workItems.data!.limit))}>Anterior</button><button type="button" disabled={offset + workItems.data.limit >= workItems.data.total} onClick={() => setOffset(offset + workItems.data!.limit)}>Siguiente</button></p>
          )}
        </>
      )}

      {detail.error && <p className="error">{errorMessage(detail.error)}</p>}
      {selected && (
        <section className="chat">
          <button type="button" onClick={close}>Cerrar detalle</button><h2>{selected.title}</h2><p>{selected.summary || 'Sin resumen'} · v{selected.version}</p><p>{selected.status} · {selected.priority} · {selected.assignee_subject_id || 'Sin asignar'}</p>
          <form onSubmit={submitAssignment}>
            <label>Asignado a<input aria-label="Asignar a" value={assignment} disabled={!canAssign || mutationPending} onChange={(event) => setAssignment(event.target.value)} /></label>
            <button type="submit" disabled={!canAssign || mutationPending}>Asignar</button>
            <button type="button" disabled={!selected.assignee_subject_id || !canAssign || mutationPending} onClick={() => assign.mutate({ id: selected.id, subject: null })}>Desasignar</button>
          </form>
          <label>Estado<select aria-label="Cambiar estado" value={selected.status} disabled={!canChangeStatus || mutationPending} onChange={(event) => changeStatus.mutate({ id: selected.id, value: event.target.value as MissionWorkStatus })}>{MISSION_WORK_STATUSES.map((value) => <option value={value} key={value}>{value}</option>)}</select></label>
          <label>Prioridad<select aria-label="Cambiar prioridad" value={selected.priority} disabled={!canChangePriority || mutationPending} onChange={(event) => changePriority.mutate({ id: selected.id, value: event.target.value as MissionWorkPriority })}>{MISSION_WORK_PRIORITIES.map((value) => <option value={value} key={value}>{value}</option>)}</select></label>
          <section aria-label="Timeline operativo">
            <h3>Timeline operativo</h3>
            {timeline.isLoading && <p>Cargando Timeline…</p>}
            {timeline.error && <p className="error">{errorMessage(timeline.error)}</p>}
            {timeline.data?.items.length === 0 && <p>No hay eventos registrados para este Work Item.</p>}
            {timeline.data?.items.map((event) => (
              <article key={event.id}>
                <h4>{timelineLabel(event.event_type)}</h4>
                <time title={event.occurred_at} dateTime={event.occurred_at}>{timelineDate(event.occurred_at)}</time>
                {event.actor_subject_id && <p>Actor: {event.actor_subject_id}</p>}
                <p>{timelineDescription(event)}</p>
                <small>Secuencia {event.sequence_number}</small>
              </article>
            ))}
          </section>
          <form onSubmit={submitComment}>
            <label>Comentario interno<textarea aria-label="Comentario interno" value={comment} disabled={!canCreate || addComment.isPending} onChange={(event) => setComment(event.target.value)} /></label>
            <button type="submit" disabled={!canCreate || !comment.trim() || addComment.isPending}>{addComment.isPending ? 'Agregando comentario…' : 'Agregar comentario'}</button>
          </form>
        </section>
      )}

      <section>
        <h2>Mission Inbox</h2>
        {!canReadInbox && <p>No tienes autorización para leer Mission Inbox.</p>}
        {inbox.isLoading && <p>Cargando Mission Inbox…</p>}
        {inbox.error && <p className="error">{errorMessage(inbox.error)}</p>}
        {inbox.data?.items.length === 0 && <p>No hay elementos de Inbox disponibles.</p>}
        {inbox.data?.items.map((item) => (
          <div className="item" key={item.id}>
            <span>{item.title}</span>
            <button type="button" disabled={!canCreate || create.isPending} onClick={() => startCreate(item.id)}>Crear o abrir Work Item</button>
          </div>
        ))}
      </section>
    </>
  );
}
