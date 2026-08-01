# YARVIS Data Intake and Document Architecture

**Work package:** DI-001
**Status:** Proposed architecture; documentation only; not implementation authorization.
**Principle:** **Preserve first. Interpret second. Act third.**

## Scope and governing rule

DI-001 defines a provider-neutral boundary for receiving operational information from manual uploads, Gmail, WhatsApp Business-compatible providers, API intake, and future scanner/import sources. It creates no runtime schema, API, connector, storage adapter, worker, classifier, or automated business action.

External input is evidence, not canonical truth. A connector may preserve and submit inbound information, but may not directly create a Task, Process Instance, Economic Fact, Document, or other authoritative state. That needs an explicit owner-governed application contract, authority scope, and audit trail.

## Evidence-based discovery

| Finding | Classification | Evidence and limit |
| --- | --- | --- |
| IntakeItem | Implemented | Tenant-scoped idempotency; source and trace metadata; received time; deterministic mode. Raw content is currently duplicated in intake metadata rather than retained as a separately governed source artifact. |
| Message | Implemented | Linked to IntakeItem; preserves external IDs, parties, bodies, headers, timestamps, and trace metadata. No thread/conversation field or provider connector exists. |
| Deterministic intake | Implemented | A local Unit of Work creates IntakeItem, Message, and intake/message events; replay conflict and idempotency-key races are handled. It is fixture-oriented, not a general connector runtime. |
| DomainEvent | Implemented, partial | Sequence, organization, correlation, causation, and payload exist. Append-only is convention only; no durable outbox/worker or DB guard exists. |
| Mission Inbox | Implemented | Rebuildable, tenant-scoped projection of deterministic intake events. Connectors do not currently write it. |
| Mission Work / Operational Context | Implemented | Work is a separate owner. Site/Project/ConnectorMapping and intake-to-context association enforce organization integrity. No Document association exists. |
| SourceRecord / DocumentRecord / Observation | Implemented, legacy/domain-specific | Spreadsheet/manual-upload metadata, checksum, local storage, parsing and observations exist, but not a provider-neutral registry, tenant-safe associations, or connector boundary. |
| Local storage and upload | Implemented, partial | LocalDocumentRepository uses configured root and relative keys; a direct one-file route saves bytes. No streaming, controlled binary download, migration, archive, malware, or production object-storage boundary exists. |
| Gmail, WhatsApp, attachments, external connectors | Documented but absent | No OAuth/webhook/sync, provider connector, Drive/SharePoint, or attachment persistence foundation was found. ConnectorMapping is only operational-context mapping. |
| Workspace corpus / mounted volumes | Architectural foundation only | Workspace safely scans the engineering repository and Markdown references. It is not operational document storage. Absolute paths and mounted-volume locations are not domain truth. |

The legacy spreadsheet/document pipeline is implementation evidence, not DI-001's canonical design. Its direct route-owned writes, parsing, and checksum-only duplicate rule must not be generalized.

## Concepts and ownership

| Concept | Meaning | Boundary |
| --- | --- | --- |
| Message | A communication unit received or sent through a channel. | Communication/Intake preserves channel truth. |
| Intake Item | Governed receipt and processing record for external input. | Intake owns receipt, integrity, idempotency, and routing state. |
| Document | Durable business information object with metadata, versions, associations. | Document Registry owns identity and metadata. |
| Evidence | Information substantiating a claim, decision, completion, or event. | The asserting owner owns the evidence association and claim context. |
| Binary Artifact | Stored bytes or file object. | Storage Provider owns physical storage mechanics. |
| Source Artifact | Original provider-preserved input or attachment. | Intake preserves it immutably. |
| External Reference | Pointer to externally retained object. | Registry governs the reference, not the external bytes. |
| Generated Document | Document produced by Yarvis or an authorized process/user. | Registry records provenance and generating authority. |

These concepts must not collapse into one table or ownership boundary because they may reference the same file. A message can have attachments; an attachment can produce a Source Artifact; a Document can be registered from it; Evidence can later cite it. None implies the next step automatically.

## Canonical inbound envelope

This is semantic guidance, not a final runtime schema.

| Field group | Required semantics | Classification |
| --- | --- | --- |
| Channel/source | channel; external source/account; external message/event ID; optional thread/conversation ID | Canonical identifiers; provider values immutable and potentially sensitive. |
| Parties/time | sender; recipients; received time; optional source timestamp | Canonical meaning; provider values immutable and sensitive. |
| Content | subject/title; text/HTML body; structured payload; attachment descriptors | Canonical slots; source representation immutable; content sensitive. |
| Provenance | source metadata; headers; raw provider-payload reference; source checksums | Provider-specific, immutable, sensitive. Raw payload is referenced, not merged into mutable interpretation. |
| Trace | correlation ID; optional causation ID; idempotency key; delivery/replay ID | Canonical operational metadata; immutable per receipt attempt. |
| Context | organization; optional Site/Project hints | Organization is required before governed persistence; hints are untrusted until authorized association. |
| Derived | normalized channel; content fingerprint; classification; routing state; candidate associations | Derived and historically attributable; never overwrites source truth. |

An attachment descriptor includes provider attachment ID where available, filename, declared/detected media type, size, checksum when obtained, binary/external reference, and preservation outcome. Secrets, OAuth tokens, and raw payload bodies never belong in ordinary event or projection payloads.

## Preservation, idempotency, and correlation

Preserve original bodies, headers and raw-payload references, attachments, external IDs, original timestamps, party metadata, and source checksums where possible. Classification, association, routing, redaction, and title correction are separate attributable history; they never rewrite raw inbound history.

Idempotency is tenant-scoped and binds an accepted fingerprint to a key. Provider identity takes precedence; a checksum/fingerprint supplements dedupe and never establishes business-document identity.

| Input | Primary dedupe identity | Supplement / conflict |
| --- | --- | --- |
| Gmail message / attachment | mailbox account + message ID; attachment part/ID | Thread is correlation only. Checksum/filename/size detect delivery changes. Same external ID with material conflict is quarantined. |
| WhatsApp message / media | business account/phone + message ID; media ID | Conversation/contact is correlation only. Delivery IDs handle webhook duplicates. |
| Manual upload | tenant + caller idempotency key + request fingerprint | Checksum detects byte equality, but same bytes from separate sources remain distinct until explicit duplicate/version policy. |
| API submission | tenant + producer + external event ID, or idempotency key | Signed request fingerprint and causation/correlation distinguish replay from conflicting reuse. |
| Sync/retry | persisted cursor/delivery identity plus source identity | Lock/unique constraint; resume a failed artifact rather than recreate accepted source records. |

## Document Registry and storage

The proposed Document Registry owns canonical document identity, title, media type, checksum, size, classification, lifecycle, version lineage, provenance, provider/key or external reference, visibility, retention, and explicit associations. It does not necessarily own bytes.

Associations are typed and tenant-scoped to Organization, Site, Project, Mission Work Item, Operational Task, Process Instance, and future Case, Accounting, and Trading subjects. Each needs target integrity (foreign key or owner-contract validation), organization ID, purpose, authority, and audit time. A generic polymorphic owner-type/id model alone is insufficient: it loses referential integrity, permits cross-tenant links, and hides target lifecycle semantics.

A conceptual Storage Provider supports put, read/stream, metadata/head, delete-or-archive, checksum verification, signed/controlled access, and version-safe key generation. Keys are provider-relative; provider migration never changes Document identity; raw bytes never go in relational JSON.

| Option | Position |
| --- | --- |
| Local filesystem | Development adapter only, behind the provider boundary. |
| S3-compatible object storage | Recommended production canonical-byte boundary. |
| Google Drive / SharePoint / OneDrive | Connector or external-reference providers, not canonical-storage assumptions. |
| External-reference-only | Valid where reference retention/access is verifiable; bytes are not presumed available. |
| Hybrid | Recommended: development-local and production-object-storage providers with the same relative-key semantics. |

## Connectors

### Gmail first

Gmail should be the first production connector: stable mailbox, message and thread identifiers, incremental synchronization, structured MIME parts, attachments, and labels validate the generic preservation and operator-review design. Authorized connector accounts own OAuth credentials and mailbox scope separately from Document Registry data. The connector maps provider IDs, thread, labels, parties, HTML/plain bodies, attachments, and raw payload reference into the inbound envelope. It must paginate, rate-limit, retry safely, surface revoked credentials, prevent duplicates, and use a separately approved historical-import policy. Outbound email is deferred.

### WhatsApp after Gmail

Use only a WhatsApp Business-compatible API; never unofficial consumer-session automation. Map business phone/account, message ID, contact/conversation, text/media, quoted references, and delivery/read state. Webhooks are out-of-order and duplicate-prone, so receipt and display ordering are distinct. Preserve consent, privacy, personal-versus-business boundaries, fragmented conversations, and expiring media. Gmail comes first because it proves stable attachment/replay/Inbox handling before WhatsApp's webhook ordering, consent, and media constraints. Outbound responses are deferred.

## Manual upload, Inbox, and routing

The DI-003 workflow is: authorized user selects one or more files; validate size/type; stream each binary to Storage Provider; verify checksum and source metadata; create Registry entry; add optional typed Organization/Site/Project/Work/Task/Process associations; create an Evidence association only by explicit request; emit owner events; project suitable items into Inbox/Workspace/Document views. Interrupted upload is staging; cancellation/expiry cleans only unreferenced temporary objects. Unsupported types reject before registration; mismatch/malware quarantine; title correction makes metadata history. Checksum equality is an alert, not automatic version or identity.

Mission Inbox receives governed inbound-event projections; connectors never write its rows directly. It shows new external messages, unclassified documents, failed routing, human-association requests, ambiguous/cross-project inputs, and operator-relevant connector errors. It excludes low-value completed sync noise, duplicates, health pings, and technical retries without operator relevance.

1. Preservation accepts raw source truth.
2. Classification labels it without changing source truth.
3. Association links it to validated subjects.
4. Recommendation proposes links, Evidence, Task, Process, Observation, or decision with rationale/confidence.
5. Authorized action is an explicit owner Command under authority scope.

Deterministic routing may make auditable associations; ambiguity requires human review. Automatic creation of Tasks, Process Instances, Economic Facts, or other authoritative state remains deferred. AI may recommend but never silently mutate truth.

## Security and failures

| Control | MVP required | Production hardening | Future compliance |
| --- | --- | --- | --- |
| Tenant/authority | tenant checks for source, registry, association, Inbox, download; credential ownership | association visibility inheritance and audited override | formal policy administration/delegation |
| Content protection | TLS, size/type validation, sensitive classification, controlled access, audit events | at-rest encryption/key-management boundary, malware scan/quarantine, signed access | DLP and rotation evidence |
| Retention/sharing | no external sharing by default; least-privilege display | retention/archive states and redaction history | legal hold and jurisdictional/personal-data automation |

Connector fetch failure or credential expiry pauses/flags the connector; persisted raw payload plus attachment failure is a pending attachment outcome; binary success plus registry failure retries idempotently or cleans safe orphan staging; registry success plus projection failure replays source events. Timeouts, checksum mismatch, unsupported type, malware, duplicate delivery, and partial historical import retain recovery evidence. Never delete accepted raw evidence because interpretation fails. A transactional outbox/worker is needed before reliable async connector, retry, projection, and archival processing; DI-001 implements none.

## Event ownership

Candidate families, without final schemas:

- Intake/communication owner: inbound_item.received, inbound_message.preserved, inbound_attachment.preserved, connector.sync_failed.
- Document Registry owner: document.registered, document.version_added, document.associated, document.archived.
- Intake routing owner: intake.classification_requested, intake.association_requested, intake.routing_completed.

Document Registry does not own Message or connector lifecycle events. Event consumption grants no mutation authority; Inbox remains rebuildable.

## Phased roadmap

| Workstream | Objective/prerequisite | Non-goals | Acceptance, migration, value |
| --- | --- | --- | --- |
| DI-002 Document Registry Foundation | Owner contracts, metadata, version/provenance/association design after DI-001 review. | bytes, uploads, connectors, UI. | Reviewed migration/association integrity plan; durable document identity. |
| DI-003 Manual Upload + Local Storage | First daily Energía Fotónica slice via provider abstraction. | Gmail, WhatsApp, AI, automatic business action. | stream/checksum/quarantine/idempotent retry; registry/storage migrations. |
| DI-004 Associations + Workspace Read Model | Typed links and read-only document projections. | generic polymorphic ownership; UI mutation. | tenant-safe links/rebuildable views; association/projection migrations. |
| CN-001 Gmail Connector | Authorized incremental preservation. | outbound mail, automated state. | OAuth/cursor/replay/attachment/operator-failure controls; connector-state migrations. |
| CN-002 WhatsApp Connector | Business inbound after Gmail evidence. | consumer automation/outbound messaging. | webhook order/replay/privacy controls; connector-state migrations. |
| WS-008C Intake / Inbox UI | Governed read-only operator workflow. | direct persistence/routing authority. | owner-query-only tenant-safe UI. |
| DI-005 Object Storage | S3-compatible adapter/migration plan. | provider-coupled IDs. | controlled access/checksum/rehearsed migration. |
| DI-006 Hardening | Malware, retention, sharing. | legal-hold automation unless approved. | policy/audit/recovery controls. |
| Future classification/AI | Attributable recommendations. | silent mutation. | explainable human-reviewed proposals. |

## Decisions requiring human approval

- First production storage provider, maximum file size, and allowed media types.
- Initial retention policy and quarantine behavior.
- Gmail historical import and mailbox/account scope; whether WhatsApp is MVP.
- Visibility inheritance, external-sharing policy, and first-release download versus metadata-only references.
- First deterministic routing rules.
- Whether duplicate bytes create a new Document, a version, or separately associated source records.

## Conclusion

DI-001 preserves existing deterministic Intake and Inbox projection as useful foundation while treating legacy spreadsheet/document code as non-canonical. The smallest usable slice is DI-003: authorized manual upload into a governed Registry with local development storage, explicit association, and no automatic business-state creation.
