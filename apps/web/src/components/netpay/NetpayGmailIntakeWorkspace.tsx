import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  netpayApi,
  newIdempotencyKey,
  type CandidateDossier,
  type CandidateDossierPreview,
  type CandidateHumanFollowUp,
  type CandidateQualification,
  type CommercialIntakePreview,
  type GmailCandidate,
  type GmailConnection,
  type GmailSourceItem,
  type NetpayApiClient,
} from "../../api/netpay";

const LABELS: Record<string, string> = {
  support_or_incident: "Soporte / revisión operativa",
  ecommerce_activation: "Activación de comercio electrónico",
  consumable_shipment: "Envío de consumibles",
  terminal_shipment: "Envío de terminal",
  shipment_follow_up: "Seguimiento de envío",
  new_branch: "Alta de sucursal",
  unclassified: "Pendiente de clasificar",
  other: "Otro requerimiento",
  normal: "Normal",
  high: "Alta",
  urgent: "Urgente",
  low: "Baja",
  new: "Nuevo",
  needs_review: "Requiere revisión",
  pending_link: "Pendiente de vincular",
  accepted: "Aceptado",
  rejected: "Rechazado",
  duplicate: "Duplicado",
  linked: "Vinculado",
  ready: "Lista",
  running: "En proceso",
  succeeded: "Completada",
  partially_failed: "Completada con incidencias",
  failed: "Fallida",
  approved: "Aprobado",
  discovered: "Descubierto",
  none: "Sin manifiesto",
  commerce_name: "Comercio observado",
  branch_name: "Sucursal observada",
  external_identifier: "Identificador observado",
  explicit_request: "Solicitud explícita",
  requested_action: "Acción solicitada",
  new_branch_onboarding: "Alta de sucursal solicitada",
  next_action: "Siguiente acción propuesta",
  ticket: "Caso o ticket",
  reported_claim: "Afirmación reportada",
  shipment_interpretation: "Interpretación del envío",
  verified: "Verificado",
  unverified: "No verificado",
  observed: "Observado",
  inferred: "Inferido",
  subject: "Asunto",
  body: "Cuerpo del correo",
  message_subject: "Asunto del mensaje",
  message_body: "Cuerpo del mensaje",
  message_text: "Texto del mensaje",
  reported_by_message: "Reportado en el mensaje",
  verified_commerce_identifier: "Identificador verificable del comercio",
  verified_terminal_identifier: "Identificador verificable de la terminal",
  ticket_or_case: "Caso o ticket verificable",
  commerce_link: "Vínculo verificable con el comercio",
  terminal_serial: "Número de serie de terminal",
  tracking_number: "Número de guía",
  carrier: "Paquetería",
  tpv: "TPV",
  ecommerce: "Comercio electrónico",
  mixed: "TPV y comercio electrónico",
  not_applicable: "No aplica",
  deterministic: "Reglas deterministas",
  meeting: "Reunión",
  call: "Llamada",
  agreement: "Acuerdo",
  pending_item: "Pendiente",
  general_follow_up: "Seguimiento general",
  operator_reported: "Reportado por operador",
  pending: "Pendiente",
  attachment_detected: "Adjunto detectado",
  under_review: "Por revisar",
  validated: "Validado",
  persona_moral: "Persona moral",
  persona_fisica: "Persona física",
  client: "Cliente / cuenta receptora",
  representative: "Titular / representante",
  branch: "Sucursal",
};
const label = (value: string | null | undefined, fallback = "No disponible") =>
  value ? LABELS[value] || value.replaceAll("_", " ") : fallback;
const date = (value: string | null) =>
  value ? new Date(value).toLocaleString("es-MX") : "No reportada";
const fact = (candidate: GmailCandidate, field: string) =>
  candidate.facts.find((item) => item.field === field)?.value || null;
const bytes = (value: unknown) => {
  const size = Number(value);
  return Number.isFinite(size)
    ? new Intl.NumberFormat("es-MX").format(size) + " bytes"
    : "Tamaño no reportado";
};
const attachmentSuggestion = (item: Record<string, unknown>) => {
  const name = String(item.filename || item.name || "").toLocaleLowerCase(
    "es-MX",
  );
  if (/(^|[_ -])csf|constancia/.test(name))
    return "Posible constancia de situación fiscal";
  if (/(^|[_ -])ine([_ .-]|$)/.test(name)) return "Posible identificación";
  if (/car[aá]tula|estado.?de.?cuenta/.test(name))
    return "Posible documento bancario";
  if (name.endsWith(".pptx")) return "Posible presentación o evidencia visual";
  return "Tipo documental no determinable por el nombre";
};

function Evidence({
  title,
  values,
}: {
  title: string;
  values: Record<string, string>[];
}) {
  return (
    <section className="gmail-evidence">
      <h3>{title}</h3>
      {values.length ? (
        <dl>
          {values.map((item, index) => (
            <div key={`${item.field}-${index}`}>
              <dt>{label(item.field, "Dato")}</dt>
              <dd>{label(item.value)}</dd>
              <small>
                Procedencia: {label(item.source, "No indicada")} · Verificación:{" "}
                {label(item.verification, "No indicada")}
                {item.attribution ? ` · Atribución: ${item.attribution}` : ""}
              </small>
            </div>
          ))}
        </dl>
      ) : (
        <p className="gmail-muted">Sin elementos registrados.</p>
      )}
    </section>
  );
}
function Manifest({ connection }: { connection: GmailConnection }) {
  return connection.manifest_status === "none" ? null : (
    <section>
      <h3>Manifiesto HMAC para revisión</h3>
      <p>
        {connection.manifest_entries.length} entradas opacas. El descubrimiento
        no ingiere asunto, remitente ni contenido.
      </p>
      <ol>
        {connection.manifest_entries.map((entry) => (
          <li key={entry.handle}>
            <code>{entry.handle}</code> · {date(entry.received_at)}
          </li>
        ))}
      </ol>
    </section>
  );
}
type Destination = { id: string; name: string; summary: string };
const brief = (value: string, max = 140) =>
  value.length > max ? `${value.slice(0, max - 1).trim()}…` : value;

export function NetpayGmailIntakeWorkspace({
  client = netpayApi,
}: {
  client?: NetpayApiClient;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [connections, setConnections] = useState<GmailConnection[]>([]),
    [candidates, setCandidates] = useState<GmailCandidate[]>([]);
  const [sources, setSources] = useState<Record<string, GmailSourceItem>>({}),
    [selected, setSelected] = useState<GmailCandidate>();
  const [stateFilter, setStateFilter] = useState(""),
    [overdueOnly, setOverdueOnly] = useState(false),
    [ownerType, setOwnerType] = useState("commercial_intake"),
    [ownerId, setOwnerId] = useState(""),
    [query, setQuery] = useState("");
  const [destinations, setDestinations] = useState<Destination[]>([]),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [loading, setLoading] = useState(true);
  const active = useRef(false);
  const [followUps, setFollowUps] = useState<CandidateHumanFollowUp[]>([]),
    [followUpKind, setFollowUpKind] = useState("general_follow_up"),
    [followUpNote, setFollowUpNote] = useState(""),
    [followUpOccurredAt, setFollowUpOccurredAt] = useState(""),
    [reviewingFollowUp, setReviewingFollowUp] = useState(false);
  const [correctedType, setCorrectedType] = useState(""),
    [correctedPriority, setCorrectedPriority] = useState("normal"),
    [correctedNextAction, setCorrectedNextAction] = useState("");
  const [applicantKind, setApplicantKind] = useState("unresolved"),
    [legalPerson, setLegalPerson] = useState(""),
    [representative, setRepresentative] = useState(""),
    [brand, setBrand] = useState(""),
    [products, setProducts] = useState<string[]>(["tpv"]),
    [branchesText, setBranchesText] = useState(""),
    [qualificationId, setQualificationId] = useState(""),
    [intakePreview, setIntakePreview] = useState<CommercialIntakePreview>();
  const [dossierPreview, setDossierPreview] =
      useState<CandidateDossierPreview>(),
    [dossier, setDossier] = useState<CandidateDossier>(),
    [confirmDossier, setConfirmDossier] = useState(false),
    [dossierRequirement, setDossierRequirement] = useState(""),
    [dossierState, setDossierState] = useState("under_review"),
    [dossierComment, setDossierComment] = useState(""),
    [documentDate, setDocumentDate] = useState(""),
    [holder, setHolder] = useState(""),
    [holderCorrespondence, setHolderCorrespondence] = useState("undetermined"),
    [interiorCount, setInteriorCount] = useState(""),
    [facadeCount, setFacadeCount] = useState(""),
    [managerName, setManagerName] = useState(""),
    [managerPhone, setManagerPhone] = useState(""),
    [managerEmail, setManagerEmail] = useState(""),
    [sharedContactReviewId, setSharedContactReviewId] = useState(""),
    [attachmentIndex, setAttachmentIndex] = useState("");
  function applyQualification(item: CandidateQualification) {
    const p = item.payload;
    const value = (key: string) =>
      String((p[key] as { value?: unknown } | null)?.value || "");
    setApplicantKind(String(p.applicant_kind || "unresolved"));
    setLegalPerson(value("legal_person_name"));
    setRepresentative(value("representative_name"));
    setBrand(value("brand_name"));
    setProducts(
      Array.isArray(p.requested_products)
        ? p.requested_products.map(String)
        : [],
    );
    setBranchesText(
      Array.isArray(p.branches)
        ? p.branches
            .map((x) => String((x as { name?: unknown }).name || ""))
            .filter(Boolean)
            .join("\n")
        : "",
    );
    setQualificationId(item.id);
  }
  async function loadCandidateContext(candidateId: string) {
    const [detail, followUpPage, qualifications] = await Promise.all([
      client.getGmailCandidate(candidateId),
      client.listCandidateFollowUps(candidateId),
      client.listCandidateQualifications(candidateId),
    ]);
    setSelected(detail);
    setCorrectedType(detail.request_type);
    setCorrectedPriority(detail.priority);
    setCorrectedNextAction(detail.suggested_next_action || "");
    setFollowUps(followUpPage.items);
    const latest = qualifications.at(-1);
    if (latest) {
      applyQualification(latest);
      setIntakePreview(
        await client.previewCandidateCommercialIntake(candidateId),
      );
      try {
        const preview = await client.previewCandidateDossier(candidateId);
        setDossierPreview(preview);
        setDossier(preview.dossier);
        if (preview.dossier) {
          setDossierRequirement(
            (current) => current || preview.dossier?.requirements[0]?.snapshot_key || "",
          );
        }
      } catch {
        setDossierPreview(undefined);
        setDossier(undefined);
      }
    } else {
      setQualificationId("");
      setIntakePreview(undefined);
      setDossierPreview(undefined);
      setDossier(undefined);
    }
  }
  async function load() {
    setError("");
    try {
      const [cs, page] = await Promise.all([
        client.listGmailConnections(),
        client.listGmailCandidates({
          state: stateFilter,
          overdue: overdueOnly || undefined,
        }),
      ]);
      const pairs = await Promise.all(
        page.items.map(
          async (c) =>
            [
              c.source_item_id,
              await client.getGmailSourceItem(c.source_item_id),
            ] as const,
        ),
      );
      setConnections(cs);
      setCandidates(page.items);
      setSources(Object.fromEntries(pairs));
      const selectedId = selected?.id || searchParams.get("candidate");
      if (selectedId && page.items.some((item) => item.id === selectedId))
        await loadCandidateContext(selectedId);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No fue posible cargar Gmail Intake.",
      );
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  async function operate(action: () => Promise<unknown>, message?: string) {
    if (active.current) return;
    active.current = true;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await action();
      await load();
      if (message) setNotice(message);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "La operación no pudo completarse.",
      );
    } finally {
      active.current = false;
      setLoading(false);
    }
  }
  async function search() {
    if (!query.trim()) {
      setError("Escribe un folio, nombre o descripción.");
      return;
    }
    setLoading(true);
    setOwnerId("");
    try {
      if (ownerType === "case") {
        const page = await client.listInbox({ query: query.trim(), limit: 25 });
        setDestinations(
          page.items.map((x) => ({
            id: x.id,
            name: x.folio,
            summary: x.original_description,
          })),
        );
      } else {
        const page = await client.listCommercialIntake({
          query: query.trim(),
          limit: 25,
        });
        setDestinations(
          page.items.map((x) => ({
            id: x.id,
            name: x.provisional_company_name || "Sin comercio",
            summary: x.summary,
          })),
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Consulta local fallida.");
    } finally {
      setLoading(false);
    }
  }
  async function selectCandidate(candidate: GmailCandidate) {
    setSelected(candidate);
    setSearchParams({ candidate: candidate.id }, { replace: true });
    setOwnerType("commercial_intake");
    setOwnerId("");
    setDestinations([]);
    setNotice("");
    setReviewingFollowUp(false);
    try {
      await loadCandidateContext(candidate.id);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "No fue posible cargar la revisión del candidato.",
      );
    }
  }
  async function saveCorrection() {
    if (!selected) return;
    await operate(
      () =>
        client.reviewGmailCandidate(
          selected.id,
          {
            action: "edit",
            request_type: correctedType,
            priority: correctedPriority,
            suggested_next_action: correctedNextAction || null,
          },
          newIdempotencyKey(),
        ),
      "Corrección humana guardada con lectura posterior. La evidencia del correo no fue modificada.",
    );
  }
  async function submitFollowUp() {
    if (!selected || !followUpNote.trim()) return;
    await operate(async () => {
      await client.recordCandidateFollowUp(
        selected.id,
        {
          kind: followUpKind,
          note: followUpNote.trim(),
          occurred_at: followUpOccurredAt
            ? new Date(followUpOccurredAt).toISOString()
            : null,
        },
        newIdempotencyKey(),
      );
      const page = await client.listCandidateFollowUps(selected.id);
      setFollowUps(page.items);
      setFollowUpNote("");
      setFollowUpOccurredAt("");
      setReviewingFollowUp(false);
    }, "Seguimiento registrado y verificado mediante lectura posterior.");
  }
  async function saveQualification() {
    if (!selected) return;
    const branches = branchesText
      .split("\n")
      .map((x) => x.trim())
      .filter(Boolean)
      .map((name, index) => ({
        draft_key: `branch-${index + 1}`,
        name,
        requested_products: products,
        verification: "operator_reported",
        source_field: "operator_review",
      }));
    const value = (x: string) =>
      x
        ? {
            value: x,
            verification: "operator_reported",
            source_field: "operator_review",
          }
        : null;
    await operate(async () => {
      const item = await client.createCandidateQualification(
        selected.id,
        {
          applicant_kind: applicantKind,
          legal_person_name: value(legalPerson),
          representative_name: value(representative),
          brand_name: value(brand),
          requested_products: products,
          branches,
          rationale: "Revisión explícita del operador.",
        },
        newIdempotencyKey(),
      );
      setQualificationId(item.id);
      setIntakePreview(undefined);
    }, "Overlay guardado como revisión append-only.");
  }
  async function prepareIntake() {
    if (!selected) return;
    await operate(
      async () =>
        setIntakePreview(
          await client.previewCandidateCommercialIntake(selected.id),
        ),
      "Vista previa preparada; todavía no existe ingreso comercial.",
    );
  }
  async function confirmIntake() {
    if (!selected || !intakePreview) return;
    await operate(
      () =>
        client.promoteCandidateCommercialIntake(
          selected.id,
          {
            qualification_id: intakePreview.qualification_id,
            provisional_company_name: intakePreview.provisional_company_name,
            provisional_contact_name: intakePreview.provisional_contact_name,
            product_interest: intakePreview.product_interest,
            summary: intakePreview.summary,
            priority: intakePreview.priority,
            next_action: intakePreview.next_action,
          },
          newIdempotencyKey(),
        ),
      "Ingreso comercial creado y leído nuevamente.",
    );
  }
  async function createDossier() {
    if (
      !selected ||
      !dossierPreview?.qualification_id ||
      !dossierPreview.catalog_sha256 ||
      !confirmDossier
    )
      return;
    await operate(
      () =>
        client.createCandidateDossier(
          selected.id,
          {
            qualification_id: dossierPreview.qualification_id,
            catalog_sha256: dossierPreview.catalog_sha256,
            confirmed: true,
          },
          newIdempotencyKey(),
        ),
      "Expediente creado desde la instantánea aprobada y leído nuevamente.",
    );
  }
  async function reviewDossierRequirement() {
    if (!selected || !dossierRequirement || !dossier) return;
    const requirement = dossier.requirements.find(
      (item) => item.snapshot_key === dossierRequirement,
    );
    if (!requirement) return;
    const review_data: Record<string, unknown> = {};
    if (documentDate) review_data.document_date = documentDate;
    if (holder) review_data.holder = holder;
    if (requirement.key === "tax_status_certificate")
      review_data.holder_correspondence = holderCorrespondence;
    if (requirement.key === "branch_premises_photos") {
      review_data.interior_count = Number(interiorCount);
      review_data.facade_count = Number(facadeCount);
    }
    if (requirement.key === "branch_manager_contact") {
      if (sharedContactReviewId) review_data.shared_contact_review_id = sharedContactReviewId;
      else Object.assign(review_data, { name: managerName, phone: managerPhone, email: managerEmail });
    }
    const evidence =
      attachmentIndex !== "" && source
        ? {
            source_item_id: source.id,
            attachment_index: Number(attachmentIndex),
            suggestion: source.attachment_metadata[Number(attachmentIndex)]
              ? attachmentSuggestion(
                  source.attachment_metadata[Number(attachmentIndex)],
                )
              : null,
          }
        : undefined;
    await operate(
      () =>
        client.reviewCandidateDossierRequirement(
          selected.id,
          {
            requirement_snapshot_key: dossierRequirement,
            state: dossierState,
            comment: dossierComment || null,
            review_data,
            evidence,
          },
          newIdempotencyKey(),
        ),
      "Revisión documental registrada en el historial append-only.",
    );
  }
  const source = selected ? sources[selected.source_item_id] : undefined,
    observed =
      selected?.facts.filter((x) => x.field !== "reported_claim") || [],
    claims = selected?.facts.filter((x) => x.field === "reported_claim") || [];
  const existingIntake = intakePreview?.existing_intake;
  const terminal = Boolean(
    selected?.immutable ||
    ["accepted", "rejected", "duplicate", "linked"].includes(
      selected?.state || "",
    ),
  );
  const selectedDestination = destinations.find((item) => item.id === ownerId);
  const activeDossierRequirement = dossier?.requirements.find(
    (item) => item.snapshot_key === dossierRequirement,
  );
  const reusableManagerContacts = (dossier?.requirements || []).flatMap((requirement) =>
    requirement.key === "branch_manager_contact"
      ? (requirement.history || [])
          .filter((history) => history.state === "validated" && history.review_data.name)
          .map((history) => ({ id: history.id, name: String(history.review_data.name), branch: requirement.branch_name }))
      : [],
  );
  const flowStep = selected?.owner_id
    ? "Destino asociado al candidato."
    : existingIntake
      ? "Ingreso comercial creado; falta decidir si debe asociarse al candidato."
      : qualificationId
        ? "Revisión guardada; prepara y confirma el ingreso comercial."
        : "Revisar los datos observados antes de conformar el ingreso comercial.";
  function chooseExistingIntake() {
    if (!existingIntake || terminal) return;
    setOwnerType("commercial_intake");
    setDestinations([
      {
        id: existingIntake.id,
        name: existingIntake.provisional_company_name || "Sin comercio",
        summary: existingIntake.summary,
      },
    ]);
    setOwnerId(existingIntake.id);
  }
  const connected = connections.some(
    (x) => x.provider_kind === "google" && x.state !== "disconnected",
  );
  return (
    <section className="netpay-workspace gmail-workspace">
      <Link to="/netpay-inbox">← Volver al Inbox</Link>
      <header className="netpay-hero">
        <div>
          <p className="eyebrow">PILOTO RESTRINGIDO · SOLO LECTURA</p>
          <h1>Gmail Intake Netpay</h1>
          <p>Revisión de candidatos con evidencia de origen.</p>
        </div>
        {client.can("netpay.inbox.manage") && (
          <button
            disabled={loading || connected}
            onClick={() =>
              void operate(async () => {
                const x = await client.startGmailOAuth();
                window.location.assign(x.authorization_url);
              })
            }
          >
            Conectar Gmail
          </button>
        )}
      </header>
      {error && (
        <p role="alert" className="error-panel">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="gmail-notice">
          {notice}
        </p>
      )}
      {loading ? (
        <p role="status">Cargando Gmail Intake…</p>
      ) : (
        <>
          {connections.map((c) => (
            <article className="gmail-card" key={c.id}>
              <h2>{c.provider_account_id}</h2>
              <p>
                Estado: {label(c.state)} · Etiqueta:{" "}
                {c.label_id || "No validada"}
              </p>
              <p>
                Última ejecución: {date(c.last_sync_at)} · Error:{" "}
                {c.last_error_code || "Ninguno"} · Manifiesto:{" "}
                {label(c.manifest_status)}
              </p>
              <Manifest connection={c} />
              {client.can("netpay.inbox.manage") && (
                <div className="gmail-buttons">
                  <button
                    onClick={() =>
                      void operate(() =>
                        client.validateGmailConnection(
                          c.id,
                          newIdempotencyKey(),
                        ),
                      )
                    }
                  >
                    Validar
                  </button>
                  <button
                    onClick={() =>
                      void operate(() => client.discoverGmailManifest(c.id))
                    }
                  >
                    Descubrir manifiesto
                  </button>
                  <button
                    disabled={
                      c.manifest_status !== "discovered" ||
                      c.manifest_entries.length !== 10
                    }
                    onClick={() =>
                      void operate(() => client.approveGmailManifest(c.id))
                    }
                  >
                    Aprobar 10 mensajes
                  </button>
                  <button
                    disabled={
                      c.provider_kind === "google" &&
                      c.manifest_status !== "approved"
                    }
                    onClick={() =>
                      void operate(() =>
                        client.syncGmailConnection(c.id, newIdempotencyKey()),
                      )
                    }
                  >
                    Sincronizar 30 días
                  </button>
                </div>
              )}
            </article>
          ))}
          <h2>Pendientes y seguimiento</h2>
          <form
            className="gmail-filters"
            onSubmit={(e) => {
              e.preventDefault();
              setLoading(true);
              void load();
            }}
          >
            <label>
              Estado
              <select
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
              >
                <option value="">Todos</option>
                <option value="pending_link">Pendiente de vincular</option>
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={overdueOnly}
                onChange={(e) => setOverdueOnly(e.target.checked)}
              />{" "}
              Sólo con seguimiento excedido
            </label>
            <button>Aplicar filtros</button>
          </form>
          <div className="gmail-layout">
            <div className="gmail-list" aria-label="Lista de candidatos">
              {candidates.map((c) => (
                <button
                  key={c.id}
                  aria-pressed={selected?.id === c.id}
                  className={selected?.id === c.id ? "selected" : ""}
                  onClick={() => void selectCandidate(c)}
                >
                  <strong>
                    {sources[c.source_item_id]?.subject ||
                      c.description ||
                      "Sin asunto"}
                  </strong>
                  <span>
                    {fact(c, "commerce_name") || "Comercio pendiente"} ·{" "}
                    {label(c.request_type)}
                  </span>
                  <small>
                    {label(c.priority)} · {label(c.state)}
                    {c.overdue ? " · Seguimiento excedido" : ""}
                  </small>
                </button>
              ))}
            </div>
            {selected && (
              <article
                className="gmail-detail"
                aria-label="Detalle del candidato"
              >
                <header>
                  <p className="eyebrow">SOLICITUD</p>
                  <h2>
                    {source?.subject || selected.description || "Sin asunto"}
                  </h2>
                  <p>
                    <strong>Comercio observado:</strong>{" "}
                    {fact(selected, "commerce_name") || "Pendiente"} ·{" "}
                    <strong>ID observado:</strong>{" "}
                    {fact(selected, "external_identifier") || "No reportado"}
                  </p>
                  <small>
                    El ID observado no se usa como identificador interno de
                    Yarvis.
                  </small>
                </header>
                <section className="gmail-summary">
                  <div>
                    <span>Solicitud recibida</span>
                    <strong>
                      {fact(selected, "requested_action") ||
                        fact(selected, "explicit_request") ||
                        selected.description ||
                        source?.subject ||
                        "Pendiente de identificar"}
                    </strong>
                    <small>
                      Extraída de la fuente local; no es la siguiente acción del
                      operador.
                    </small>
                  </div>
                  <div>
                    <span>Estado</span>
                    <strong>{label(selected.state)}</strong>
                  </div>
                  <div>
                    <span>Producto solicitado</span>
                    <strong>{label(selected.product)}</strong>
                    <small>
                      Inferido por reglas desde la fuente local; pendiente de
                      verificación humana.
                    </small>
                  </div>
                  <div>
                    <span>Prioridad</span>
                    <strong>{label(selected.priority)}</strong>
                    <small>
                      Sólo señales explícitas de urgencia o bloqueo.
                    </small>
                  </div>
                  <div className="gmail-next-action">
                    <span>Paso del flujo</span>
                    <strong>{flowStep}</strong>
                    <small>
                      Calculado por la interfaz a partir de la revisión,
                      promoción y asociación existentes.
                    </small>
                  </div>
                  <div className="gmail-next-action">
                    <span>Siguiente acción guardada por el operador</span>
                    <textarea
                      aria-label="Siguiente acción propuesta"
                      readOnly
                      rows={4}
                      value={
                        selected.suggested_next_action || "Pendiente de definir"
                      }
                    />
                    <small>No se sobrescribe al avanzar de paso.</small>
                  </div>
                  <div>
                    <span>Seguimiento</span>
                    <strong>{date(selected.follow_up_at)}</strong>
                    <small>
                      {selected.follow_up_basis ===
                      "derived_follow_up_threshold"
                        ? "Umbral derivado; no es fecha límite."
                        : label(selected.follow_up_basis)}
                    </small>
                  </div>
                  <div>
                    <span>Fecha límite explícita</span>
                    <strong>{date(selected.explicit_deadline_at)}</strong>
                    <small>
                      Antigüedad: {selected.age_days} días
                      {selected.overdue ? " · Seguimiento excedido" : ""}
                    </small>
                  </div>
                </section>
                <div className="gmail-evidence-grid">
                  <Evidence title="Hechos observados" values={observed} />
                  <Evidence title="Afirmaciones reportadas" values={claims} />
                  <Evidence title="Inferencias" values={selected.inferences} />
                  <section className="gmail-evidence">
                    <h3>Datos pendientes</h3>
                    {selected.missing_data.length ? (
                      <ul>
                        {selected.missing_data.map((x) => (
                          <li key={x}>{label(x)}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>Sin datos pendientes.</p>
                    )}
                  </section>
                </div>
                <section className="gmail-review-group">
                  <h3>Revisar y corregir datos</h3>
                  {client.can("netpay.inbox.manage") && (
                    <section className="gmail-correction">
                      <h4>Datos del alta</h4>
                      <p>
                        Overlay atribuido al operador; no modifica el correo ni
                        las notas H1.
                      </p>
                      <div className="gmail-correction-form">
                        <label>
                          Tipo de persona
                          <select
                            value={applicantKind}
                            onChange={(e) => setApplicantKind(e.target.value)}
                          >
                            <option value="unresolved">Pendiente</option>
                            <option value="persona_moral">Persona moral</option>
                            <option value="persona_fisica">
                              Persona física
                            </option>
                          </select>
                        </label>
                        <label>
                          Persona moral observada
                          <input
                            value={legalPerson}
                            onChange={(e) => setLegalPerson(e.target.value)}
                          />
                        </label>
                        <label>
                          Representante observado
                          <input
                            value={representative}
                            onChange={(e) => setRepresentative(e.target.value)}
                          />
                        </label>
                        <label>
                          Marca comercial
                          <input
                            value={brand}
                            onChange={(e) => setBrand(e.target.value)}
                          />
                        </label>
                        <fieldset>
                          <legend>Productos</legend>
                          <label>
                            <input
                              type="checkbox"
                              checked={products.includes("tpv")}
                              onChange={(e) =>
                                setProducts(
                                  e.target.checked
                                    ? [...new Set([...products, "tpv"])]
                                    : products.filter((x) => x !== "tpv"),
                                )
                              }
                            />{" "}
                            TPV
                          </label>
                          <label>
                            <input
                              type="checkbox"
                              checked={products.includes("ecommerce")}
                              onChange={(e) =>
                                setProducts(
                                  e.target.checked
                                    ? [...new Set([...products, "ecommerce"])]
                                    : products.filter((x) => x !== "ecommerce"),
                                )
                              }
                            />{" "}
                            e-commerce
                          </label>
                        </fieldset>
                        <label className="gmail-correction-action">
                          Sucursales, una por línea
                          <textarea
                            value={branchesText}
                            onChange={(e) => setBranchesText(e.target.value)}
                            rows={6}
                          />
                        </label>
                        <button
                          disabled={terminal || loading || !products.length}
                          onClick={() => void saveQualification()}
                        >
                          Revisar y guardar overlay
                        </button>
                        {qualificationId && (
                          <button
                            disabled={terminal || !!existingIntake}
                            onClick={() => void prepareIntake()}
                          >
                            Preparar ingreso comercial
                          </button>
                        )}
                      </div>
                      {intakePreview && (
                        <div className="gmail-follow-up-review">
                          <h4>Revisión previa del ingreso comercial</h4>
                          <p>
                            <strong>Empresa:</strong>{" "}
                            {intakePreview.provisional_company_name ||
                              "Pendiente"}{" "}
                            · <strong>Contacto:</strong>{" "}
                            {intakePreview.provisional_contact_name ||
                              "Pendiente"}{" "}
                            · <strong>Producto:</strong>{" "}
                            {label(intakePreview.product_interest)}
                          </p>
                          <p>
                            {intakePreview.branches.length} sucursales
                            separadas. Esta confirmación no crea Master ni
                            casos.
                          </p>
                          <button
                            disabled={
                              !!existingIntake ||
                              !intakePreview.provisional_company_name
                            }
                            onClick={() => void confirmIntake()}
                          >
                            {existingIntake
                              ? "Ingreso ya creado"
                              : "Confirmar creación del ingreso comercial"}
                          </button>
                        </div>
                      )}
                    </section>
                  )}
                  {client.can("netpay.inbox.manage") && (
                    <section className="gmail-correction">
                      <h4>Tipo, prioridad y acción</h4>
                      <p>
                        Corrige la clasificación o la siguiente acción. Esta
                        operación no altera la fuente Gmail ni convierte una
                        nota del operador en evidencia del correo.
                      </p>
                      <div className="gmail-correction-form">
                        <label>
                          Tipo de solicitud
                          <select
                            value={correctedType}
                            onChange={(e) => setCorrectedType(e.target.value)}
                          >
                            <option value="new_branch">Alta de sucursal</option>
                            <option value="ecommerce_activation">
                              Activación de comercio electrónico
                            </option>
                            <option value="support_or_incident">
                              Soporte / revisión operativa
                            </option>
                            <option value="shipment_follow_up">
                              Seguimiento de envío
                            </option>
                            <option value="consumable_shipment">
                              Envío de consumibles
                            </option>
                            <option value="unclassified">
                              Pendiente de clasificar
                            </option>
                            <option value="other">Otro requerimiento</option>
                          </select>
                        </label>
                        <label>
                          Prioridad
                          <select
                            value={correctedPriority}
                            onChange={(e) =>
                              setCorrectedPriority(e.target.value)
                            }
                          >
                            <option value="urgent">Urgente</option>
                            <option value="high">Alta</option>
                            <option value="normal">Normal</option>
                            <option value="low">Baja</option>
                          </select>
                        </label>
                        <label className="gmail-correction-action">
                          Siguiente acción
                          <textarea
                            rows={5}
                            maxLength={2000}
                            value={correctedNextAction}
                            onChange={(e) =>
                              setCorrectedNextAction(e.target.value)
                            }
                          />
                        </label>
                        <button
                          disabled={terminal || loading || !correctedType}
                          onClick={() => void saveCorrection()}
                        >
                          Guardar corrección
                        </button>
                      </div>
                      <small>
                        La corrección del nombre observado del comercio o de
                        sucursales requiere un contrato adicional de
                        trazabilidad.
                      </small>
                    </section>
                  )}
                </section>
                <section className="gmail-follow-ups">
                  <h3>Seguimiento humano</h3>
                  <p>Notas append-only separadas de la evidencia del correo.</p>
                  {followUps.length ? (
                    <ol>
                      {followUps.map((item) => (
                        <li key={item.id}>
                          <strong>{label(item.kind)}</strong>
                          <span>{item.note}</span>
                          <small>
                            {label(item.provenance_kind)} · Registrado:{" "}
                            {date(item.recorded_at)} · Evento:{" "}
                            {date(item.occurred_at)}
                          </small>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="gmail-muted">
                      Sin seguimiento humano registrado.
                    </p>
                  )}
                  {client.can("netpay.inbox.manage") &&
                    (!reviewingFollowUp ? (
                      <div className="gmail-follow-up-form">
                        <label>
                          Tipo
                          <select
                            value={followUpKind}
                            onChange={(e) => setFollowUpKind(e.target.value)}
                          >
                            <option value="meeting">Reunión</option>
                            <option value="call">Llamada</option>
                            <option value="agreement">Acuerdo</option>
                            <option value="pending_item">Pendiente</option>
                            <option value="general_follow_up">
                              Seguimiento general
                            </option>
                          </select>
                        </label>
                        <label>
                          Fecha del evento (opcional)
                          <input
                            type="datetime-local"
                            value={followUpOccurredAt}
                            onChange={(e) =>
                              setFollowUpOccurredAt(e.target.value)
                            }
                          />
                        </label>
                        <label>
                          Nota del operador
                          <textarea
                            maxLength={4000}
                            value={followUpNote}
                            onChange={(e) => setFollowUpNote(e.target.value)}
                          />
                        </label>
                        <small>
                          Se guardará como Reportado por operador. No modifica
                          el correo, el candidato ni su decisión.
                        </small>
                        <button
                          disabled={!followUpNote.trim() || loading}
                          onClick={() => setReviewingFollowUp(true)}
                        >
                          Revisar nota
                        </button>
                      </div>
                    ) : (
                      <div className="gmail-follow-up-review">
                        <h4>Revisa la nota exacta</h4>
                        <p>{followUpNote}</p>
                        <p>
                          <strong>Tipo:</strong> {label(followUpKind)} ·{" "}
                          <strong>Fecha del evento:</strong>{" "}
                          {followUpOccurredAt
                            ? date(new Date(followUpOccurredAt).toISOString())
                            : "Fecha del evento no proporcionada"}
                        </p>
                        <div className="gmail-buttons">
                          <button
                            disabled={loading}
                            onClick={() => setReviewingFollowUp(false)}
                          >
                            Volver a editar
                          </button>
                          <button
                            disabled={loading}
                            onClick={() => void submitFollowUp()}
                          >
                            Registrar seguimiento
                          </button>
                        </div>
                      </div>
                    ))}
                </section>
                <details>
                  <summary>Correo completo conservado como evidencia</summary>
                  <div className="gmail-body">
                    {source?.plain_excerpt || "Contenido local no disponible."}
                  </div>
                </details>
                <details>
                  <summary>Evidencia de origen y adjuntos</summary>
                  {source && (
                    <dl>
                      <dt>Mensaje Gmail</dt>
                      <dd>{source.gmail_message_id}</dd>
                      <dt>Hilo Gmail</dt>
                      <dd>{source.gmail_thread_id}</dd>
                      <dt>Remitente</dt>
                      <dd>{source.sender || "No disponible"}</dd>
                    </dl>
                  )}
                  <h4>Adjuntos</h4>
                  {source?.attachment_metadata.length ? (
                    <ul className="gmail-attachments">
                      {source.attachment_metadata.map((x, i) => (
                        <li key={i}>
                          <strong>
                            {String(x.filename || x.name || `Adjunto ${i + 1}`)}
                          </strong>
                          <span>
                            {String(x.mime_type || "Tipo no reportado")} ·{" "}
                            {bytes(x.size_bytes ?? x.size)}
                          </span>
                          <span>
                            Correo de origen:{" "}
                            {source.subject || "Asunto no disponible"}
                          </span>
                          <small>
                            Sugerencia no verificada: {attachmentSuggestion(x)}
                          </small>
                          <small>
                            Metadatos locales; archivo no descargado ni
                            revisado.
                          </small>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>Sin metadatos de adjuntos.</p>
                  )}
                </details>
                <details>
                  <summary>Detalle técnico (JSON)</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        facts: selected.facts,
                        inferences: selected.inferences,
                        contradictions: selected.contradictions,
                        missing_data: selected.missing_data,
                        provenance: source?.provenance,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
                {dossierPreview && (
                  <section className="gmail-dossier" aria-label="Expediente de alta">
                    <h3>Expediente de alta</h3>
                    <p>
                      Catálogo v{dossierPreview.catalog_version || dossier?.catalog_version} · Vigente desde {dossierPreview.catalog_effective_date || dossier?.catalog_effective_date} · Propietario operativo: {dossierPreview.catalog_owner || dossier?.catalog_owner}
                    </p>
                    <p>
                      <strong>Productos:</strong>{" "}
                      {(dossierPreview.products || dossier?.products || []).map((item) => label(item)).join(", ")} ·{" "}
                      <strong>Sucursales:</strong> {(dossierPreview.branches || dossier?.branches || []).length}
                    </p>
                    <small>
                      El candidato puede ser terminal: el expediente usa su propio contrato y no modifica la aceptación. E-commerce sin establecimiento físico está excluido.
                    </small>
                    {!dossier ? (
                      <div className="gmail-dossier-preview">
                        <h4>Revisión previa a crear</h4>
                        <p>
                          {(dossierPreview.requirements || []).length} requisitos; {dossierPreview.blocker_count || 0} bloqueadores iniciales. Todos comienzan como Pendiente. Un nombre de archivo nunca valida un documento.
                        </p>
                        <details>
                          <summary>Revisar requisitos y alcance</summary>
                          <ul>
                            {(dossierPreview.requirements || []).map((item) => (
                              <li key={item.snapshot_key}>
                                <strong>{item.label}</strong> · {item.branch_name || label(item.scope)} · {label(item.state)}
                              </li>
                            ))}
                          </ul>
                        </details>
                        <label className="gmail-dossier-confirm">
                          <input type="checkbox" checked={confirmDossier} onChange={(event) => setConfirmDossier(event.target.checked)} />
                          Confirmo crear una instantánea inmutable del catálogo aprobado para este ingreso y sus sucursales.
                        </label>
                        <button disabled={loading || !confirmDossier} onClick={() => void createDossier()}>
                          Crear expediente de alta
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="gmail-dossier-status">
                          <strong>{dossier.complete ? "Expediente completo" : `${dossier.blockers.length} bloqueadores`}</strong>
                          <span>{dossier.history_count} revisiones en historial</span>
                        </div>
                        <ul className="gmail-dossier-requirements">
                          {dossier.requirements.map((item) => (
                            <li key={item.snapshot_key}>
                              <button type="button" aria-pressed={dossierRequirement === item.snapshot_key} onClick={() => setDossierRequirement(item.snapshot_key)}>
                                <strong>{item.label}</strong>
                                <span>{item.branch_name || label(item.scope)} · {label(item.state)}</span>
                              </button>
                            </li>
                          ))}
                        </ul>
                        {client.can("netpay.inbox.manage") && activeDossierRequirement && (
                          <div className="gmail-dossier-review">
                            <h4>Registrar revisión: {activeDossierRequirement.label}</h4>
                            <label>
                              Estado
                              <select value={dossierState} onChange={(event) => setDossierState(event.target.value)}>
                                <option value="pending">Pendiente</option>
                                <option value="attachment_detected">Adjunto detectado</option>
                                <option value="under_review">Por revisar</option>
                                <option value="validated">Validado</option>
                                <option value="observed">Observado</option>
                                <option value="not_applicable">No aplica</option>
                              </select>
                            </label>
                            {activeDossierRequirement.maximum_age_days && <label>Fecha del documento<input type="date" value={documentDate} onChange={(event) => setDocumentDate(event.target.value)} /><small>Se evalúa contra la fecha de revisión humana; máximo 60 días.</small></label>}
                            {["receiving_account_bank_statement", "tax_status_certificate"].includes(activeDossierRequirement.key) && <label>Titular observado<input value={holder} onChange={(event) => setHolder(event.target.value)} /></label>}
                            {activeDossierRequirement.key === "tax_status_certificate" && <label>Correspondencia con estado de cuenta<select value={holderCorrespondence} onChange={(event) => setHolderCorrespondence(event.target.value)}><option value="undetermined">No determinada</option><option value="matches">Coincide</option><option value="does_not_match">No coincide</option></select></label>}
                            {activeDossierRequirement.key === "branch_premises_photos" && <div className="gmail-dossier-pair"><label>Fotos interiores<input type="number" min="0" value={interiorCount} onChange={(event) => setInteriorCount(event.target.value)} /></label><label>Fotos de fachada<input type="number" min="0" value={facadeCount} onChange={(event) => setFacadeCount(event.target.value)} /></label></div>}
                            {activeDossierRequirement.key === "branch_manager_contact" && <><label>Reutilizar encargado ya revisado<select value={sharedContactReviewId} onChange={(event) => setSharedContactReviewId(event.target.value)}><option value="">Registrar contacto para esta sucursal</option>{reusableManagerContacts.map((contact) => <option key={contact.id} value={contact.id}>{contact.name} · {contact.branch}</option>)}</select><small>La relación se guarda por referencia; los datos del contacto no se duplican.</small></label>{!sharedContactReviewId && <div className="gmail-dossier-pair"><label>Nombre del encargado<input value={managerName} onChange={(event) => setManagerName(event.target.value)} /></label><label>Teléfono<input value={managerPhone} onChange={(event) => setManagerPhone(event.target.value)} /></label><label>Correo<input type="email" value={managerEmail} onChange={(event) => setManagerEmail(event.target.value)} /></label></div>}</>}
                            <label>Metadato de adjunto opcional<select value={attachmentIndex} onChange={(event) => setAttachmentIndex(event.target.value)}><option value="">Sin referencia</option>{source?.attachment_metadata.map((item, index) => <option key={index} value={index}>{String(item.filename || item.name || `Adjunto ${index + 1}`)} · no verificado</option>)}</select></label>
                            <label>Comentario de revisión<textarea value={dossierComment} onChange={(event) => setDossierComment(event.target.value)} rows={3} /></label>
                            <button disabled={loading || (["validated", "observed", "not_applicable"].includes(dossierState) && !dossierComment.trim())} onClick={() => void reviewDossierRequirement()}>
                              Registrar en historial
                            </button>
                            <details><summary>Historial del requisito</summary>{activeDossierRequirement.history?.length ? <ol>{activeDossierRequirement.history.map((item) => <li key={item.id}>{label(item.prior_state)} → {label(item.state)} · {date(item.recorded_at)} · {label(item.provenance_kind)}</li>)}</ol> : <p>Sin revisiones; estado inicial Pendiente.</p>}</details>
                          </div>
                        )}
                      </>
                    )}
                  </section>
                )}
                {existingIntake && (
                  <section className="gmail-existing-intake">
                    <h3>Ingreso comercial existente</h3>
                    <p>
                      <strong>
                        {existingIntake.provisional_company_name ||
                          "Sin comercio"}
                      </strong>{" "}
                      · {label(existingIntake.product_interest)} ·{" "}
                      {label(existingIntake.status)}
                    </p>
                    <p>
                      {intakePreview?.promotion_trace?.branch_drafts.length ||
                        0}{" "}
                      sucursales conservadas en la traza de promoción.
                    </p>
                    <Link to={`/netpay-inbox/contacts/${existingIntake.id}`}>
                      Abrir detalle del ingreso
                    </Link>
                  </section>
                )}
                {client.can("netpay.inbox.manage") && (
                  <section className="gmail-actions">
                    <h3>Decidir sobre la solicitud</h3>
                    <p>
                      Aceptar y Vincular requieren seleccionar un registro
                      destino verificado. Crear el ingreso no cambia por sí solo
                      el owner ni la disposición del candidato.
                    </p>
                    {terminal && (
                      <div className="gmail-decision-result">
                        <h4>Resultado registrado</h4>
                        <dl>
                          <dt>Resultado</dt>
                          <dd>{label(selected.state)}</dd>
                          <dt>Destino</dt>
                          <dd>
                            {selected.owner_type === "commercial_intake" &&
                            selected.owner_id === existingIntake?.id
                              ? existingIntake.provisional_company_name ||
                                "Ingreso comercial"
                              : label(selected.owner_type)}
                          </dd>
                          <dt>Fecha de decisión</dt>
                          <dd>{date(selected.reviewed_at)}</dd>
                        </dl>
                        {existingIntake && (
                          <div className="gmail-destination-summary">
                            <strong>
                              {existingIntake.provisional_company_name ||
                                "Ingreso comercial"}
                            </strong>
                            <p>{brief(existingIntake.summary)}</p>
                            <details>
                              <summary>Ver detalle del destino</summary>
                              <p>{existingIntake.summary}</p>
                            </details>
                          </div>
                        )}
                        {selected.owner_type === "commercial_intake" &&
                          selected.owner_id && (
                            <Link
                              to={`/netpay-inbox/contacts/${selected.owner_id}`}
                            >
                              Abrir destino aceptado
                            </Link>
                          )}
                        <p>
                          La disposición es terminal e inmutable; las decisiones
                          incompatibles están deshabilitadas.
                        </p>
                      </div>
                    )}
                    {existingIntake && (
                      <div className="gmail-existing-destination">
                        <strong>Ingreso creado desde esta revisión</strong>
                        <span>
                          {existingIntake.provisional_company_name ||
                            "Sin comercio"}
                        </span>
                        <button
                          type="button"
                          disabled={terminal}
                          onClick={chooseExistingIntake}
                        >
                          Seleccionar este ingreso como destino
                        </button>
                      </div>
                    )}
                    <div className="gmail-search">
                      <label>
                        Tipo de registro destino
                        <select
                          disabled={terminal}
                          value={ownerType}
                          onChange={(e) => {
                            setOwnerType(e.target.value);
                            setOwnerId("");
                            setDestinations([]);
                          }}
                        >
                          <option value="case">Caso Netpay</option>
                          <option value="commercial_intake">
                            Ingreso comercial
                          </option>
                        </select>
                      </label>
                      <label>
                        Buscar registro destino
                        <input
                          disabled={terminal}
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Folio, comercio o descripción"
                        />
                      </label>
                      <button
                        disabled={terminal || !query.trim()}
                        onClick={() => void search()}
                      >
                        Buscar registros locales
                      </button>
                    </div>
                    {destinations.length ? (
                      <>
                        <label>
                          Registro destino verificado
                          <select
                            aria-label="Registro destino verificado"
                            value={ownerId}
                            onChange={(e) => setOwnerId(e.target.value)}
                          >
                            <option value="">Selecciona un resultado</option>
                            {destinations.map((x) => (
                              <option key={x.id} value={x.id}>
                                {x.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        {selectedDestination && (
                          <div className="gmail-destination-summary">
                            <strong>{selectedDestination.name}</strong>
                            <p>{brief(selectedDestination.summary)}</p>
                            <details>
                              <summary>Ver detalle del registro</summary>
                              <p>{selectedDestination.summary}</p>
                            </details>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="gmail-muted">
                        Ningún ID observado se selecciona automáticamente.
                      </p>
                    )}
                    <div className="gmail-buttons">
                      <button
                        disabled={terminal || !ownerId}
                        title={
                          terminal
                            ? "La disposición ya es terminal."
                            : !ownerId
                              ? "Selecciona un registro destino verificado."
                              : undefined
                        }
                        onClick={() =>
                          void operate(
                            () =>
                              client.reviewGmailCandidate(
                                selected.id,
                                {
                                  action: "accept",
                                  owner_type: ownerType,
                                  owner_id: ownerId,
                                },
                                newIdempotencyKey(),
                              ),
                            "Candidato aceptado y persistido.",
                          )
                        }
                      >
                        Aceptar
                      </button>
                      <button
                        disabled={terminal}
                        onClick={() =>
                          void operate(
                            () =>
                              client.reviewGmailCandidate(
                                selected.id,
                                { action: "reject", reason: "Revisión humana" },
                                newIdempotencyKey(),
                              ),
                            "Candidato rechazado y persistido.",
                          )
                        }
                      >
                        Rechazar
                      </button>
                      <button
                        disabled={terminal}
                        onClick={() =>
                          void operate(
                            () =>
                              client.reviewGmailCandidate(
                                selected.id,
                                {
                                  action: "duplicate",
                                  reason: "Duplicado confirmado",
                                },
                                newIdempotencyKey(),
                              ),
                            "Candidato marcado como duplicado.",
                          )
                        }
                      >
                        Marcar duplicado
                      </button>
                      <button
                        disabled={terminal || !ownerId}
                        onClick={() =>
                          void operate(
                            () =>
                              client.reviewGmailCandidate(
                                selected.id,
                                {
                                  action: "link",
                                  owner_type: ownerType,
                                  owner_id: ownerId,
                                },
                                newIdempotencyKey(),
                              ),
                            "Vínculo persistido.",
                          )
                        }
                      >
                        Vincular
                      </button>
                    </div>
                  </section>
                )}
              </article>
            )}
          </div>
        </>
      )}
    </section>
  );
}
