# YARVIS
# Implementation Roadmap Amendment 018

## Current-HEAD Reconciliation for MVP-2D1 Manual Review Variant

## Status

**RATIFIED — DESIGN AUTHORITY ONLY — NO IMPLEMENTATION AUTHORITY**

This document is a prospective amendment to
`IMPLEMENTATION_ROADMAP_AMENDMENT_014.md`.

It has no authority unless and until an explicit future act of the Yarvis
Architecture Authority ratifies it. While Proposed, it does not modify,
supersede, replace, or narrow any ratified authority.

It does not assign contracts, roles, permissions, a Principal, Membership, or
Organization. It does not authorize implementation, tests, models, migrations,
OAuth, secrets, Google resources, Gmail access, mailbox access,
synchronization, workers, scheduling, deployment, or a real pilot.

## 1. Purpose, baseline, and evidence boundary

The purpose of this amendment is to reconcile the ratified design of MVP-2D1
Manual Review Variant with the repository state and explicit Architecture
Authority decisions recorded after Implementation Roadmap Amendment 014.

The reviewed current baseline is:

| Field | Value |
| --- | --- |
| Branch | `feat/operational-intake-spine` |
| Current HEAD | `d9c981d18c8fddd1d09fa7aac0574c9f7807124e` |
| Remote branch | `origin/feat/operational-intake-spine` |
| Remote commit | `d9c981d18c8fddd1d09fa7aac0574c9f7807124e` |
| Governing Gmail design | `IMPLEMENTATION_ROADMAP_AMENDMENT_014.md` |
| Governing Inbox authority | `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` |
| Governing Commercial Intake authority | `IMPLEMENTATION_ROADMAP_AMENDMENT_015.md` |
| Identity and Organization authority | ADR-014 and the later productive identity authority chain |
| Secrets governance | ADR-015 |
| Dispatch mechanics | ADR-016 and ADR-017 |

Implementation Roadmap Amendment 014 remains the ratified authority for the
existing MVP-2D1 design unless this amendment is later ratified. The original
Gmail draft and its reviews are evidence and rationale; they are not
independent authority.

Implementation evidence demonstrates what exists at current HEAD, but it
cannot assign a contract, grant a role, authorize Gmail, or replace an
Architecture Authority act.

## 2. Effect if subsequently ratified

If ratified through an explicit future Architecture Authority act, this
amendment would update only the current-HEAD facts and decisions identified
below.

It would preserve every Amendment 014 invariant not expressly reconciled here,
including:

- Gmail remains external evidence and never canonical identity or authority;
- the mailbox-to-Organization binding is explicit and unique;
- provider metadata cannot select a tenant;
- candidates precede definitive business entities;
- human review is mandatory;
- `gmail.readonly` is the maximum initial Gmail scope;
- the exact Gmail label is resolved to and enforced through canonical
  `label_id`;
- invalid or ambiguous identity, authority, binding, label, cursor, retention,
  or credential state fails closed;
- Gmail contracts remain proposed and `gate_closed` until separately assigned
  and authorized;
- OAuth, mailbox access and a real pilot require a separate gate; and
- no authority is granted by implication.

This amendment would not retroactively modify the historical evidence,
reviews, commits, or ratification record of Amendment 014.

## 3. Mailbox, Organization, label, and scope

### 3.1 Dedicated mailbox

The MVP-2D1 design continues to be limited to the single dedicated mailbox
identified by Amendment 014.

The mailbox address is configuration and external-provider identity. It is not
a Person, Principal, Membership, permission, Organization selector, or source
of canonical authority.

One provider mailbox identity may have at most one active Organization binding.

### 3.2 Organization verification gate

The intended current productive Organization is reported as:

- `organization_id`: `6c2bbf37-87d1-4315-8e67-85e9957c9aa7`
- `display_name`: `Yarvis en NetPay`

The historical Amendment 014 reference is:

- `organization_id`: `59650e6f-ad62-40c3-8cb0-7710a122ce8b`
- `display_name`: `Distribución Netpay`

The current Organization identity has not yet been proven from canonical
read-only evidence under this proposal. Therefore this proposal does not
declare that the current value replaces, aliases, renames, or corresponds to
the historical value.

Before any real Gmail contract, real role, productive configuration,
productive persistence, OAuth, mailbox-access or real-pilot gate, a separately
authorized read-only evidence procedure must demonstrate:

1. the exact active Organization row;
2. its canonical UUID and display name;
3. whether the historical Organization exists;
4. whether the values identify the same, different, renamed, superseded, or
   otherwise related records;
5. the active Membership used by the intended human actor; and
6. absence of Organization ambiguity for the intended operation.

Any mismatch, absence or ambiguity fails closed and blocks all productive or
real-provider gates. It does not prevent consideration of an independently
bounded fake/local package that uses only synthetic identities, Organizations,
Memberships, messages, credentials and provider behavior as specified in
§8.4.

No sender, recipient, domain, message, header, token, workspace, Store ID,
display name or configuration value may supply or override Organization
authority.

### 3.3 Gmail label

The exact human-configured label remains:

`Yarvis/Netpay-Intake`

A future authorized real-provider implementation must resolve the canonical
Gmail `label_id`, persist it with the explicit mailbox binding, and verify it
before every synchronization.

An absent, invalid, ambiguous, deleted or inconsistent `label_id` fails closed:

- no fallback by display name;
- no query outside the binding;
- no candidate creation;
- no cursor advance; and
- no external or persistent effect except approved non-sensitive health
  evidence.

A fake/local package may exercise these semantics only with a synthetic label
and synthetic `label_id`. It may not resolve or contact a real Gmail label.

### 3.4 Gmail scope

The maximum initial Gmail scope remains:

`https://www.googleapis.com/auth/gmail.readonly`

This proposal neither requests nor grants that scope. It does not authorize an
OAuth consent flow, token, credential, project, client, connection or mailbox
access.

No Gmail send, modify, label mutation, archive, delete or administrative scope
is within MVP-2D1.

A fake/local adapter requires no Google scope and must not simulate possession
of a real provider credential.

## 4. Candidate data and classification

### 4.1 Closed initial classification catalog

The initial classification catalog is closed to:

- `commercial_contact_or_rfq`;
- `tpv_physical`;
- `ecommerce`;
- `support_or_incident`; and
- `unclassified`.

No implementation may add, infer, alias or silently reinterpret another
classification. A future catalog change requires separate authority.

Classification is a proposal for human review. It does not establish identity,
authority, acceptance or business truth.

### 4.2 Persisted content boundary

A future authorized MVP-2D1 implementation may persist only:

- approved provider and trace metadata;
- approved tenant-safe candidate metadata;
- classification proposal, confidence and controlled reasons;
- disposition and human-review metadata;
- approved hashes, timestamps and idempotency references; and
- one sanitized plain-text excerpt of at most 4 KiB, understood exactly as
  4096 bytes of UTF-8 after sanitization and redaction.

It must not persist:

- the complete body;
- HTML;
- raw or reconstructed MIME;
- raw provider payloads;
- attachment content;
- attachment bytes; or
- any content exceeding the approved excerpt boundary.

Sanitization and redaction occur before truncation. Truncation is deterministic,
produces valid UTF-8, and never supplies or modifies tenant, authority,
provenance, mailbox binding, provider identity or idempotency fields; those
remain separate structured metadata governed by their own validation.

This amendment does not select or authorize a sanitization algorithm. The exact
algorithm, versioning, test corpus and failure semantics remain requirements of
the future privacy and implementation gates.

No prohibited content may enter logs, Events, receipts, errors, metrics,
health responses or frontend telemetry.

### 4.3 Attachment boundary

MVP-2D1 may preserve only approved attachment metadata needed to represent
source evidence, including controlled provider part identity, declared media
type, reported size, inline status and approved hash/reference fields.

Filename retention is prohibited unless a later privacy decision explicitly
authorizes a safe representation. No attachment is downloaded, stored,
rendered, parsed, OCR-processed, classified, uploaded to Document Registry or
sent to an AI provider under this proposal.

### 4.4 Retention, purge, tombstone and legal hold

The ordinary maximum retention remains 90 days from synchronization for the
approved excerpt and non-essential candidate metadata.

At expiry, a future authorized purge mechanism must retain only the approved
tombstone boundary:

- safe identity/hash;
- timestamps;
- controlled disposition; and
- auditable purge evidence.

Purge must be effective, deterministic, idempotent and testable by readback.

A legal hold may suspend purge only under separate canonical authority and must
record scope, reason, authorized actor, start, review and expiry. This proposal
creates no hold.

A purge failure produces `retention_blocked` and fails closed:

- no new ingestion;
- no synchronization;
- no candidate creation;
- no cursor advance; and
- no silent retention extension.

Recovery requires remediation, auditable evidence and separate human
reauthorization.

## 5. Human authority and business routing

### 5.1 Future Google project ownership

The intended future Google project name is:

`yarvis-netpay-intake`

It must be a dedicated enterprise project owned by GMDHO.

This decision identifies future ownership only. It does not authorize creating
the project, enabling an API, configuring a consent screen, registering a
client, creating a secret, granting a scope or accessing Google.

### 5.2 Future human roles

Guillermo is the intended initial future subject for:

- connector administrator; and
- candidate reviewer.

These are logically separate roles and separate authority evaluations even if
they are initially held by the same human.

This proposal assigns neither role. Before any real or productive assignment,
canonical read-only evidence must prove:

- the exact active Principal;
- the exact active Membership;
- the exact active Organization;
- the allowed role and permission definitions;
- same-Organization authority; and
- absence of ambiguity or revocation.

Visible name, email address, mailbox control, OIDC claims, historical authority
narrative or founder status cannot substitute for that proof.

Synthetic actors and roles used exclusively within an authorized fake/local
test package are test doubles only. They create no productive Principal,
Membership, permission or authority evidence.

### 5.3 Human confirmation and AI boundary

Yarvis AI may classify, summarize or propose corrections only within a later
authorized implementation and privacy boundary.

Yarvis AI must never:

- accept a candidate;
- reject or dismiss a candidate;
- confirm identity;
- select an Organization;
- create or mutate Commercial Intake;
- create or mutate a Case;
- grant a role or permission; or
- cause an external action.

Every candidate receives an explicit human decision by an authorized reviewer.
A fake/local package may use only a synthetic reviewer identity and synthetic
decision evidence.

### 5.4 Commercial contact and RFQ routing

A candidate classified as `commercial_contact_or_rfq` and accepted by a human
must first enter the existing `CommercialIntakeItem` owner boundary.

It must never create a `NetpayServiceCase` directly.

Any later conversion from qualified Commercial Intake to Netpay Master and a
Case remains governed by the existing Commercial Intake contracts, authority,
idempotency and explicit human conversion rules.

MVP-2D1 does not authorize that conversion. It defines only the required
routing boundary.

All other candidate-to-business-entity mutations remain outside MVP-2D1 unless
a later ratified contract and implementation gate explicitly authorizes them.

A fake/local package may prove the routing decision through synthetic doubles
or assertions, but it may not register or invoke a productive business
contract or write productive Commercial Intake or Case state.

## 6. Bounded pilot design and immutable manifest

The future real pilot design is limited to:

- one dedicated mailbox;
- one canonically verified Organization;
- one verified label binding;
- one human-triggered synchronization;
- exactly 10 eligible messages selected before execution;
- a maximum historical window of 30 calendar days;
- the five classifications in §4.1;
- exactly one represented candidate per manifest message; and
- one explicit human decision per candidate.

Before the real pilot executes, the competent authority must approve an
immutable pilot manifest containing exactly 10 eligible messages.

The manifest must identify each message only through approved safe identifiers,
such as an approved cryptographic hash of `provider_message_id`, together with
the applicable mailbox-binding reference and canonical `label_id`. It must not
contain bodies, excerpts, subjects, sender or recipient addresses, header
values, attachment names, credentials, tokens or other PII.

The approved manifest is the sole authoritative denominator for:

- 10 of 10 messages represented exactly once;
- zero omissions;
- zero duplicates;
- 10 of 10 candidates receiving a human decision; and
- the initial-classification acceptance metric.

Messages carrying the configured label but not included in the immutable
manifest are outside the pilot. They must not be ingested, represented as
candidates, included in pilot metrics or cause advancement of the cursor
applicable to the pilot.

The pilot implementation must prove that excluding a non-manifest message
cannot silently skip it through cursor advancement. The cursor strategy,
checkpoint boundary or equivalent provider-safe mechanism must preserve the
ability to process excluded messages later only under separate authority.

This section defines a future pilot boundary. It does not authorize the pilot,
manifest creation from a real mailbox, Gmail access, synchronization or any
external action.

Expanding mailbox count, tenant count, label set, manifest size, time window,
scope, provider or classification catalog requires separate authority.

## 7. GO/NO-GO evidence criteria

The immutable approved manifest defined in §6 is the authoritative denominator
for every count and completeness assertion below.

A future pilot may receive a GO result only if all of the following pass:

1. zero cross-tenant access or disclosure;
2. zero secrets or message bodies in logs, Events, receipts, errors, health,
   metrics or frontend telemetry;
3. zero duplicate candidate representations relative to the manifest;
4. zero omissions relative to the manifest;
5. zero cursor advances after a failed transaction or incomplete batch;
6. zero Cases created without explicit human confirmation;
7. 10 of 10 manifest messages represented exactly once;
8. 10 of 10 manifest candidates receive an explicit human decision;
9. at least 8 of 10 initial classifications for manifest candidates are
   accepted by the reviewer without classification correction;
10. zero manifest candidates remain pending for more than 24 hours;
11. the bounded manual synchronization completes in no more than 2 minutes;
    and
12. credential or authority revocation fails closed.

“Synchronization completes in no more than 2 minutes” means the interval from
the system's acceptance of the manual trigger until either:

- all 10 candidates corresponding to the immutable manifest have been durably
  committed and are available to the authorized review surface; or
- the batch has reached a terminal fail-closed outcome.

Human review and decision time after candidate availability is expressly
excluded from the 2-minute synchronization interval.

Timing evidence must use monotonic clocks or an equivalently reliable duration
source. It may record only safe trigger, batch and terminal timestamps or
durations and controlled identifiers. It must contain no PII, bodies,
credentials, tokens, provider payloads or secrets.

A failure of any criterion is NO-GO.

NO-GO requires disabling the connector and trigger, preserving the last valid
cursor and approved audit evidence, preventing further candidates, and
returning every proposed Gmail Command to `gate_closed`. No automatic retry,
scope expansion, data repair, case creation or continued pilot operation is
authorized.

A result may not be reported as GO without reproducible evidence for every
criterion and reconciliation against the immutable manifest.

## 8. Fake/local and productive OAuth separation

The gates below form two related but independently sequenced branches:

```text
Design ratification
        |
        +--> Synthetic branch:
        |      fake/local implementation gate
        |      --> synthetic Evidence Gate
        |
        +--> Productive branch:
               canonical identity and Organization proof
               --> formal contract and real-role allocation
               --> privacy/retention gate
               --> secrets gate
               --> productive OAuth topology gate
               --> Google project and consent gate
               --> real connector implementation gate
               --> worker/scheduler gate if separately required
               --> real-pilot gate
               --> GO/NO-GO and deployment decision
```

Completion of the synthetic branch does not complete, waive or reduce any
productive-branch gate.

### 8.1 Design ratification gate

A future explicit Architecture Authority act may ratify this design only. It
creates no runtime or external authority.

Design ratification may permit consideration of a separate fake/local package
without first proving productive identity or assigning Gmail contracts, but
only under the isolation requirements in §8.4.

### 8.2 Canonical identity gate

A separate read-only evidence package must prove the exact productive
Principal, Membership and Organization before real roles, productive
configuration, productive persistence, Gmail access or a real pilot are
considered.

This gate is mandatory for the productive branch. It is not a prerequisite for
a synthetic-only package that uses no productive identity or state.

### 8.3 Contract and role allocation gate

A separate canonical action must assign the approved Gmail contracts, roles
and permissions before they are registered or used in any productive runtime.

Formal assignment is mandatory before real Gmail access, productive role
assignment, productive persistence or a real pilot.

A synthetic-only package may precede this assignment if it does not modify the
canonical catalog, register a business contract in the productive runtime or
represent its synthetic identifiers as canonically assigned contracts.

### 8.4 Fake/local implementation gate

A future fake/local package may be considered before productive Organization,
Principal or Membership proof and before formal Gmail contract assignment.

It must use only:

- a synthetic mailbox;
- a synthetic Organization;
- a synthetic Principal;
- a synthetic Membership;
- synthetic role and permission doubles;
- synthetic messages and attachment metadata;
- synthetic credentials that are not valid provider secrets; and
- a fake provider adapter with no Google or Gmail connectivity.

It must not:

- connect to Google, Gmail or another external provider;
- use a real mailbox, provider identity, label, message, credential, token,
  secret or commercial datum;
- use or expose production configuration;
- register Gmail or other business contracts in the productive runtime;
- create productive role assignments;
- create a productive mailbox binding;
- write productive Commercial Intake, Case or candidate state;
- create migrations or productive persistence unless separately authorized;
- modify deployment; or
- claim that synthetic evidence proves productive identity, OAuth,
  credentials, mailbox access or provider behavior.

The package may authorize only expressly bounded artifacts such as:

- provider-neutral adapter protocols;
- fake provider implementations;
- synthetic mailbox, label, manifest, messages and failures;
- candidate models or in-memory/test-only representations specifically
  authorized by that package;
- deterministic classification;
- idempotency, cursor, rollback, retention-state and redaction behavior; and
- focused synthetic tests.

It must have its own:

- Authorized File Boundary;
- Evidence Gate;
- persistence and migration prohibition or explicit boundary;
- rollback strategy; and
- conformance review.

If the package cannot remain synthetic or requires a file, migration,
configuration, database, contract registration or runtime effect outside its
boundary, it must stop and request an amendment.

Synthetic evidence creates no authority for the productive branch.

### 8.5 Privacy and retention gate

A separate privacy review must approve field-level metadata, sanitization,
redaction, excerpt construction, retention, purge, tombstone, access, legal
hold and readback evidence before real Gmail content is accessed.

Synthetic sanitization tests may precede this gate, but no chosen synthetic
algorithm becomes approved for real content merely because those tests pass.

### 8.6 Secrets gate

A separate secrets design must define:

- credential store;
- `credential_secret_ref`;
- client-secret and refresh-token custody;
- encryption;
- least-privilege access;
- rotation;
- revocation;
- recovery;
- audit; and
- non-disclosure controls.

No secret may enter Git, documentation, logs, Events, ordinary persistence,
frontend state or health output.

Synthetic placeholder credentials used in fake/local tests must be clearly
non-functional and must not resemble or validate as real provider credentials.

### 8.7 Productive OAuth topology gate

Desktop/local loopback remains limited to local or separately authorized
operator-assisted proof. It is not a productive DigitalOcean topology.

A separate decision must approve the productive OAuth client type, exact HTTPS
redirect URI, consent configuration, project ownership, secret injection,
replica/session behavior and incident response.

### 8.8 Google project and consent gate

Only a later explicit act may authorize creating `yarvis-netpay-intake`,
enabling Gmail API, configuring consent, registering a client or obtaining a
credential.

### 8.9 Connector implementation gate

A separate implementation authorization must name the exact files, contracts,
models, migrations, routes, adapter, environment, tests, rollback and
prohibitions for the real connector.

Synthetic adapter code does not authorize replacing the fake provider with a
Gmail adapter.

### 8.10 Worker and scheduler gate

MVP-2D1 begins with human-triggered manual synchronization. No worker,
scheduler, queue, broker, Pub/Sub, webhook or Gmail `watch` is authorized.

Any later worker or scheduler requires separate runtime design, ownership,
lease, retry, recovery, observability and deployment authority.

A fake/local package may simulate invocation boundaries but may not introduce
a productive worker or scheduler.

### 8.11 Real-pilot gate

A separate real-pilot authority must name:

- the canonically verified mailbox;
- the canonically verified Organization;
- the canonical `label_id`;
- the authorized human actors and logically separate roles;
- the enterprise Google project;
- the approved OAuth topology;
- the approved credential mechanism;
- the immutable pilot manifest containing exactly 10 safe message
  identifiers;
- the maximum 30-day window;
- the metrics and timing rules in §7;
- monitoring;
- rollback; and
- revocation procedure.

The immutable manifest must be approved before the first real trigger. It must
use only safe identifiers, such as approved hashes of provider message IDs
bound to the mailbox-binding reference and `label_id`, and must contain no
body, excerpt, subject, sender/recipient address, header, attachment name,
credential, token or PII.

Only the 10 manifest entries belong to the pilot. Other labelled messages must
not be ingested or advance the cursor applicable to the manifest.

No fake/local artifact, manifest or synthetic test result may substitute for
the approved real-pilot manifest or its productive evidence.

### 8.12 GO/NO-GO and deployment gate

Pilot evidence must be reviewed against §7 and reconciled against the approved
immutable manifest. A GO result does not by itself authorize broader
deployment, additional mailboxes, scheduling, automation or production
continuation.

Any continuation or deployment requires another explicit authority act.

## 9. Contract and Dispatch boundary

The following remain proposed only:

- `IC-NETPAY-CMD-016 ConfigureNetpayGmailConnector`;
- `IC-NETPAY-CMD-017 SynchronizeNetpayGmailConnector`;
- `IC-NETPAY-CMD-018 ReviewNetpayIntakeCandidate`;
- `IC-NETPAY-QRY-007 ListNetpayIntakeCandidates`;
- `IC-NETPAY-QRY-008 RetrieveNetpayIntakeCandidate`;
- `IC-NETPAY-EVT-007 NetpayIntakeCandidateReceived`;
- `IC-NETPAY-EVT-008 NetpayIntakeCandidateReviewed`; and
- `IC-NETPAY-EVT-010 NetpayGmailConnectorSyncFailed`.

They are not canonically assigned, registered, dispatchable, implemented or
authorized. `CMD-017` remains `gate_closed`.

`IC-NETPAY-CMD-019` and `IC-NETPAY-EVT-009` remain outside MVP-2D1.

ADR-016 and ADR-017 prove platform Dispatch mechanics and Handler-factory
composition only. They do not authorize registering any Gmail or other
business Handler.

No existing static or factory Handler registration grants Gmail authority by
implication.

A fake/local package may use test-local semantic identifiers or doubles only
as expressly bounded by its own gate. It may not alter the canonical catalog or
register Gmail business contracts in the default productive composition root.

## 10. Explicit prohibitions and non-effects

This proposal does not authorize:

- modifying the canonical contract catalog;
- creating or assigning a productive role or permission;
- provisioning or changing a productive Person, Principal, Identity Binding,
  Membership or Organization;
- implementation, code, tests, models, schemas, migrations or routes;
- invoking the legacy `/netpay/import-email` path;
- creating a Google project or OAuth client;
- OAuth consent or credentials;
- Gmail or mailbox access;
- reading, synchronizing, sending, modifying, archiving, labelling or deleting
  email;
- persisting complete bodies, HTML, MIME or attachment content;
- downloading or storing attachment bytes;
- AI acceptance or business mutation;
- automatic Commercial Intake or Case creation;
- workers, schedulers, queues, brokers, Pub/Sub, webhooks or `watch`;
- configuration, DigitalOcean changes or deployment;
- a local or real pilot; or
- broader authority for another mailbox, Organization, provider or Command.

This proposal also does not itself authorize the fake/local package described
in §8.4. It only defines the conditions under which a separately ratified
package could be considered.

If a future package cannot operate within its explicit gate and File Boundary,
it must stop and request an amendment. It may not infer authority from this
proposal.

## 11. Rollback and revocation

Before implementation, withdrawal or rejection of this proposal requires no
runtime rollback because it creates no runtime state.

Any future implementation and pilot gates must preserve this minimum rollback:

1. disable the connector;
2. disable every manual or automatic trigger;
3. return proposed Gmail Commands to `gate_closed`;
4. stop Gmail access, candidate creation and cursor advancement;
5. preserve the last valid cursor and approved audit/tombstone evidence;
6. revoke and delete credentials only through the separately authorized
   provider and secret-store procedure;
7. preserve existing Commercial Intake and Case records without attempting
   destructive rollback; and
8. prove that unrelated Inbox, Commercial Intake, Dispatch and authentication
   capabilities continue operating independently.

Revocation, invalid label, binding ambiguity, Organization mismatch,
Membership loss, secret compromise, retention failure or cross-tenant anomaly
fails closed immediately.

A fake/local package must define its own rollback. At minimum, rollback removes
or disables only the synthetic package and leaves the canonical catalog,
productive composition root, productive persistence, authentication, Inbox,
Commercial Intake and deployment unchanged.

## 12. Conditions before implementation consideration

### 12.1 Conditions for a synthetic fake/local package

A fake/local implementation gate may be considered after:

1. this amendment has been independently reviewed;
2. an explicit Architecture Authority act has ratified it;
3. the proposed synthetic package defines its own Authorized File Boundary;
4. the package defines its own Evidence Gate and rollback;
5. it proves that every mailbox, Organization, Principal, Membership, role,
   message, credential and provider behavior is synthetic;
6. it has no Google/Gmail or other external connectivity;
7. it uses no secret or commercial datum;
8. it does not modify the canonical catalog or register a business contract in
   the productive runtime; and
9. it creates no migration or productive persistence unless a later amendment
   explicitly authorizes those effects.

Productive Organization, Principal and Membership proof and formal Gmail
contract assignment are not prerequisites for this synthetic-only package.

Passing the synthetic Evidence Gate proves only the bounded synthetic
mechanics.

### 12.2 Conditions for productive persistence, real roles or Gmail access

No gate involving real roles, productive configuration, productive
persistence, Gmail connectivity, OAuth, credentials, a real mailbox or a real
pilot may be considered until:

1. this amendment has been independently reviewed and ratified;
2. canonical read-only Organization, Principal and Membership evidence has
   passed;
3. Gmail contracts and productive role definitions have been separately
   assigned;
4. any required productive implementation File Boundary has been ratified;
5. privacy and retention review has passed;
6. the secret-store design has been accepted;
7. the productive OAuth topology has been accepted;
8. Google project creation and consent have received separate authority; and
9. all earlier productive gates are documented without implied external
   authority.

No synthetic package, fake adapter or local test waives or satisfies these
productive prerequisites.

## Architecture Authority Ratification

- Decision: **RATIFIED — DESIGN AUTHORITY ONLY**
- Architecture Authority: **Guillermo de Hoyos**
- Decision date: **2026-09-05**
- Accepted proposal SHA-256: **`8D74BF9BDCD53CBE472A28B9B26D50E86515F4080A3D312DB78256EA1D95A180`**
- Hash basis: **Canonical UTF-8 without BOM, with CRLF and lone CR normalized to LF before hashing**
- Accepted exceptions: **None**

This ratification grants design authority only. It does not authorize
implementation, tests, models, migrations, contracts, productive roles,
secrets, Google resources, OAuth, Gmail, mailbox access, synchronization,
workers, scheduling, deployment or a real pilot.

The synthetic fake/local package remains separately unauthorized and requires
its own explicit Architecture Authority act, Authorized File Boundary,
Evidence Gate and rollback strategy. Synthetic conformance cannot complete,
waive or reduce any productive gate.
