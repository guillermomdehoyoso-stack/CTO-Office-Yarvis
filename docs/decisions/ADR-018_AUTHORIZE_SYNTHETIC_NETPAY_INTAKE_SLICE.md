# ADR-018: Authorize a Synthetic Local Netpay Intake Slice

## Status

**ACCEPTED — RATIFIED ARCHITECTURAL DECISION — IMPLEMENTATION AUTHORIZATION AS BOUNDED BELOW**

## Identity

- Proposed ADR: `ADR-018`
- Proposed filename:
  `docs/decisions/ADR-018_AUTHORIZE_SYNTHETIC_NETPAY_INTAKE_SLICE.md`
- Governing design:
  `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_018.md`
- Governing authority framework:
  `docs/architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md`
- Related Gmail design:
  `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_014.md`
- Related Commercial Intake design:
  `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_015.md`
- Related Dispatch decisions: ADR-016 and ADR-017
- Accepted exceptions: none recorded

The physical ADR inventory contains ADR identifiers through ADR-017. Although
ADR-001 has two historical filenames, ADR-018 is unused and is the next
available identifier.

This document is a proposal. It grants no implementation authority unless an
explicit later act of the Yarvis Architecture Authority changes it to Accepted
and authorizes exactly the bounded package described below.

## Context

Implementation Roadmap Amendment 018 ratifies design boundaries for the
current-HEAD MVP-2D1 Manual Review Variant. Its authority is design-only. It
does not authorize implementation, tests, contracts, persistence, migrations,
Google resources, OAuth, Gmail, mailbox access, synchronization, deployment or
a real pilot.

Amendment 018 permits a separately authorized synthetic branch to precede
productive identity proof and Gmail contract allocation if that branch:

- uses exclusively synthetic identities, messages, credentials and provider
  behavior;
- has no Google, Gmail or external-provider connectivity;
- has its own Authorized File Boundary, Evidence Gate and rollback;
- creates no productive persistence or migration;
- changes no canonical contract;
- registers no business Handler in the productive composition root; and
- cannot be represented as productive evidence.

The current product already has a persistent, tenant-owned
`CommercialIntakeItem` boundary and a separately owned `NetpayServiceCase`
boundary. Those productive implementations must not be invoked or changed by
this synthetic package.

A small visible local slice can nevertheless prove the intended candidate
workflow and its safety properties before any productive gate is opened.

## Decision if Subsequently Accepted

If this ADR is subsequently Accepted through an explicit Architecture
Authority act, it will authorize only a dedicated local/test synthetic
application that demonstrates:

```text
manual local trigger
→ fake provider
→ immutable manifest of exactly 10 synthetic messages
→ sanitization and redaction
→ deterministic UTF-8 truncation
→ proposed classification
→ candidate visible for review
→ explicit synthetic human decision
→ synthetic CommercialIntakeItem routing intent
```

The selected approach is a standalone, opt-in FastAPI development application
with an in-memory transactional store and a minimal local review UI.

The synthetic application will not be imported, mounted or registered by the
default Yarvis runtime composition root.

## Alternatives

### A. Test-only in-memory harness

Deferred. This has the smallest surface and lowest risk but does not provide a
visible local operator experience.

### B. Visible local API/UI with in-memory storage

Selected. It demonstrates the complete synthetic workflow while remaining
separate from productive persistence, authority, contracts and routes.

### C. Local persistence using models and migrations

Rejected for this package. Persistence introduces schema, migration, repository,
cleanup and composition concerns that require a different implementation gate.
It is not justified merely to demonstrate the synthetic workflow.

## Authorized Implementation Package

The proposed package name is:

`ADR-018 authorized synthetic Netpay intake package`

If and only if this ADR becomes Accepted, that package may implement:

1. one provider-neutral protocol used only inside the synthetic package;
2. one fake provider containing exactly 10 synthetic fixtures;
3. one immutable synthetic manifest;
4. one in-memory candidate store with atomic batch publication;
5. deterministic synthetic sanitization, redaction and UTF-8 truncation;
6. deterministic proposed classification using the closed five-value catalog;
7. one dedicated local/test FastAPI application;
8. one minimal local review UI contained inside that application;
9. explicit decisions made only by a synthetic human reviewer;
10. a synthetic routing projection for accepted
    `commercial_contact_or_rfq` candidates; and
11. focused automated tests for this package.

The provider-neutral protocol is an internal boundary of this package. It may
describe only the operations required by the fake provider. It must not import
an external provider SDK or contain a real endpoint, hostname, OAuth scope,
credential, mailbox identity or provider-specific secret.

The package grants no authority to implement or register a canonical Gmail or
Commercial Intake contract.

## Authorized File Boundary

Only these files may be created or modified:

- `apps/api/src/yarvis_api/synthetic_netpay_intake.py`
- `apps/api/src/yarvis_api/synthetic_netpay_intake_app.py`
- `apps/api/tests/test_synthetic_netpay_intake.py`

No existing file is authorized for modification.

The complete local UI, including its HTML response construction and any
necessary local presentation behavior, must remain contained in
`synthetic_netpay_intake_app.py`. No frontend file, template, static asset,
configuration file or dependency declaration is authorized.

If the implementation requires any other file, including configuration,
bootstrap, package metadata, frontend, templates, assets, models, persistence,
migrations or canonical catalogs, implementation must stop and request an
amendment.

## Synthetic Manifest

The package will define an immutable manifest containing exactly these ten
synthetic fixture identities:

1. `SYN-MSG-001`
2. `SYN-MSG-002`
3. `SYN-MSG-003`
4. `SYN-MSG-004`
5. `SYN-MSG-005`
6. `SYN-MSG-006`
7. `SYN-MSG-007`
8. `SYN-MSG-008`
9. `SYN-MSG-009`
10. `SYN-MSG-010`

Each manifest entry must contain:

- its synthetic fixture identity;
- a deterministic synthetic provider-message hash;
- a synthetic source fingerprint;
- a synthetic mailbox-binding identifier;
- a synthetic label identifier;
- its expected category from the closed classification catalog; and
- its expected sanitized and truncated result when that expectation is
  applicable to the fixture.

The ten fixtures together must cover every category in the closed catalog at
least once. The remaining fixtures may repeat categories only where required
to exercise sanitization, truncation, idempotency, failure or review behavior.

Each expected classification and expected sanitized result is a test oracle,
not a human decision.

The fixtures may contain artificial message text and artificial attachment
metadata needed by the tests. They must be visibly artificial and must contain
no copied, generated-from, or transformed real mailbox or commercial data.

The manifest is the authoritative denominator for exact-once representation,
zero omissions, zero duplicates and ten explicit synthetic human decisions.

The ten decisions must be recorded only after candidate publication through
explicit reviewer actions. Together they must cover accept, reject and request
correction.

The sync, fake provider, sanitizer and classifier must not predetermine or
automatically record those decisions.

A 10-of-10 match against deliberately constructed fixture oracles proves only
determinism and conformance of the synthetic harness. It does not measure
classification accuracy on real email, does not satisfy Amendment 018's
productive threshold of at least 8 accepted initial classifications out of 10,
and is not evidence from or for a real pilot.

## Closed Classification Catalog

Every candidate must receive exactly one proposed classification from:

- `commercial_contact_or_rfq`;
- `tpv_physical`;
- `ecommerce`;
- `support_or_incident`; or
- `unclassified`.

Classification is advisory. It cannot accept, reject, route or mutate a
candidate.

No sixth category, alias or inferred business state is authorized. Any
classification result outside the closed catalog must fail closed before
candidate publication and before checkpoint advancement.

## Content Boundary

Sanitization and redaction must occur before truncation.

The retained candidate excerpt must:

- be plain text;
- be deterministically produced;
- be valid UTF-8;
- contain no more than 4096 UTF-8 bytes; and
- remain separate from tenant, authority, provenance, mailbox binding,
  provider identity and idempotency metadata.

The package must not retain:

- complete message bodies;
- HTML;
- raw or reconstructed MIME;
- raw provider payloads;
- attachment content or bytes;
- real addresses, subjects, identifiers or PII; or
- content exceeding the approved excerpt boundary.

The chosen implementation is synthetic test logic only. Passing its tests does
not approve an algorithm for processing real Gmail content.

## Local Execution and Isolation

The synthetic application must:

1. be disabled by default;
2. require an explicit operator acknowledgement at startup;
3. reject startup unless the effective environment is exactly `local` or
   exactly `test`;
4. reject `production` and every unknown environment value even if enablement
   or operator acknowledgement is supplied;
5. use a supported entrypoint that starts the ASGI server with the bind address
   hard-coded to `127.0.0.1`;
6. provide no argument, environment variable, request value or other input that
   can change the bind address;
7. before executing any application behavior, validate the actual client
   peer/socket address using strict IP-address parsing and require that address
   to be recognized as loopback;
8. fail closed when the actual peer address is absent, malformed or not
   loopback;
9. never allow `X-Forwarded-For`, `Forwarded`, `X-Real-IP` or any other
   client-supplied header to substitute for or authorize the actual peer/socket
   address;
10. configure and trust no external proxy;
11. apply actual-peer validation to GET and POST requests before reading or
    mutating synthetic state;
12. use a closed Host allowlist containing only `127.0.0.1` and `localhost`,
    each with the effective local port;
13. reject every other Host value before executing application behavior;
14. validate Origin and Referer fail-closed for every mutating operation against
    the exact permitted loopback origin and effective local port;
15. generate a cryptographically random CSRF token once per process at startup;
16. accept that token for mutations only through an approved form field or
    request header, never through a query string;
17. never persist or log the CSRF token;
18. destroy the only server-held token reference when the process terminates;
19. make every GET operation read-only and free of state mutation;
20. expose every sync, decision and disable operation exclusively through POST;
21. expose no productive authentication cookie, identity or session;
22. use no cookie or session as the basis for synthetic authorization;
23. use a fixed synthetic Organization, Principal, Membership and role set;
24. store all candidate and review state exclusively in process memory;
25. discard all state when the process exits;
26. display `SYNTHETIC / NOT PRODUCTION` persistently in every UI state;
27. contain no external-provider implementation, Google/Gmail client, network
    adapter or outbound provider connectivity;
28. load no secret or productive configuration; and
29. remain absent from the default runtime application and DigitalOcean
    deployment.

Actual-peer loopback validation, Host validation, Origin/Referer validation and
CSRF validation are cumulative controls, not alternatives. Passing one control
does not waive or weaken another applicable control.

The explicit operator acknowledgement must be a server-side startup condition.
A client-side query parameter, header, cookie, form field, browser storage value
or request cannot enable the application or satisfy that acknowledgement.

An equivalent server-side protection mechanism may be used only if it produces
the same fail-closed evidence for bind address, actual peer/socket address,
environment, operator acknowledgement, Host, Origin/Referer, CSRF, HTTP method
safety and absence of productive cookies or sessions, without modifying a file
outside the Authorized File Boundary.

## Safe Local UI Rendering

Candidate excerpts, categories, controlled errors, fixture identities,
fingerprints and all other candidate-derived values must be rendered
exclusively as escaped text.

No fixture or candidate value may be treated as trusted markup or inserted
through `innerHTML`, raw HTML interpolation or an equivalent active-content
mechanism.

The UI response must include a restrictive Content-Security-Policy. At minimum,
the policy must:

- deny all resource types by default;
- prohibit framing;
- prohibit object and plugin content;
- prohibit base-URI changes;
- limit form submission to the same local origin; and
- permit no external network source.

The local UI must not load external JavaScript, CSS, fonts, images, frames,
media or other assets. It must not require a CDN or remote resource.

The smallest compliant implementation should prefer server-rendered escaped
HTML and ordinary same-origin POST forms so that no client JavaScript is
required. If an equivalent implementation is proposed, it must remain within
the same file boundary and demonstrate the same security properties.

A focused test must supply synthetic markup and script-like content through
fixture or candidate values and prove that:

- the value is displayed as text;
- it is escaped in the HTML response;
- it does not appear as an active element or executable script;
- it does not enter an event-handler attribute or unsafe URL; and
- no use of `innerHTML` or an equivalent unsafe insertion mechanism exists.

These controls provide evidence only for the synthetic harness. They do not
approve a productive Netpay or Gmail UI.

## In-Memory Transaction and Cursor Semantics

A manual trigger processes exactly the immutable ten-entry manifest.

The service must stage all candidate and checkpoint changes separately from the
published state. It may publish the complete staged batch only after all ten
entries pass validation, sanitization, classification and deduplication.

If any step fails:

- no staged candidate becomes visible;
- the checkpoint does not advance;
- no partial batch remains;
- no automatic retry occurs; and
- the failure is reported using a controlled synthetic error category.

Re-executing a completed manifest is idempotent and returns the existing ten
candidate identities without duplication.

This is an in-memory behavioral proof. It does not claim database transaction,
Gmail cursor or provider-history conformance.

## Human Review and Commercial Routing

Only the fixed synthetic reviewer may record a decision.

The permitted decisions are:

- accept;
- reject; or
- request correction.

The classifier, fake provider and application must never record a human
decision automatically.

All ten candidates must receive an explicit decision through the synthetic
review surface after synchronization. The evidence set must include at least
one accept, one reject and one request-correction decision.

When a candidate classified as `commercial_contact_or_rfq` is explicitly
accepted, the package may construct only a synthetic
`CommercialIntakeBoundaryProjection` containing the proposed safe values that
a future authorized adapter could supply to the Commercial Intake owner.

It must not:

- instantiate or persist the SQLAlchemy `CommercialIntakeItem`;
- invoke `IC-NETPAY-CMD-020`;
- call `/netpay/inbox/contacts`;
- invoke a productive service or Repository;
- create Master data; or
- create a `NetpayServiceCase`.

The projection proves only correct routing intent toward the existing owner
boundary.

## Explicit Prohibitions

This ADR does not authorize:

- an external-provider implementation;
- a Google or Gmail client;
- a network provider adapter;
- outbound provider connectivity;
- importing a Google, Gmail or other external-provider SDK;
- real endpoints, provider hostnames or OAuth scopes in the internal protocol;
- Google or Gmail connectivity;
- OAuth, consent, tokens or credentials;
- real or provider-valid secrets;
- a Google project;
- mailbox access;
- real messages or commercial data;
- productive identity, Organization, Principal, Membership or roles;
- canonical-contract changes;
- registering any Gmail or business Command;
- changing `main.py` or `bootstrap.py`;
- changing the default Handler registry;
- using productive cookies or sessions;
- importing or calling productive Netpay routes;
- modifying `CommercialIntakeItem` or `NetpayServiceCase`;
- creating a Case;
- a Repository, database, migration or persistent model;
- workers, schedulers, queues, Pub/Sub or webhooks;
- configuration or `.env` changes;
- DigitalOcean or deployment changes;
- frontend production routes or assets;
- a real pilot; or
- authority for another Command, provider, mailbox or package by implication.

The provider-neutral protocol expressly authorized within the package is not an
external-provider implementation. It must remain an internal typed boundary
implemented only by the in-process fake provider and subject to the restrictions
above.

## Evidence Gate

The package may be declared complete only when evidence proves:

1. the immutable manifest contains exactly ten unique synthetic entries;
2. each entry has a synthetic identity, fingerprint, expected category and,
   where applicable, expected sanitized/truncated result;
3. the ten fixtures collectively cover all five approved categories;
4. all ten candidates appear exactly once after a successful trigger;
5. there are zero omissions and zero duplicates;
6. repeating the trigger preserves the same ten candidate identities;
7. a controlled failure before atomic publication leaves zero new candidates
   and does not advance the checkpoint;
8. sanitization and redaction execute before truncation;
9. every retained excerpt is valid UTF-8 and no more than 4096 bytes;
10. complete bodies, HTML, MIME, raw payloads and attachment bytes are absent
    from candidate state;
11. classification is deterministic;
12. all ten fixtures match their expected categories;
13. a result outside the five-category catalog fails closed before publication
    and checkpoint advancement;
14. classification success records no human decision;
15. all ten candidates receive a subsequent explicit synthetic human decision;
16. the decision evidence includes accept, reject and request correction;
17. no AI, classifier, fake-provider or sync operation can decide a candidate;
18. an accepted `commercial_contact_or_rfq` candidate produces the correct
    synthetic Commercial Intake boundary projection;
19. no `CommercialIntakeItem`, Master record or `NetpayServiceCase` is created;
20. disabling or revoking the local harness fails closed;
21. the application cannot be constructed outside exact `local` or `test`
    environments;
22. the supported entrypoint starts the ASGI server only on hard-coded
    `127.0.0.1`;
23. no argument, environment variable or request can change the bind address;
24. startup requires explicit operator acknowledgement;
25. an allowed IPv4 loopback peer can operate after all other applicable
    controls pass;
26. an IPv6 loopback peer, if the harness elects to support it, is recognized
    only by explicit strict IP loopback validation; otherwise IPv6 fails closed
    and that unsupported behavior is documented;
27. a remote, absent or malformed actual peer address is rejected;
28. `Host: localhost` from a non-loopback peer does not grant access;
29. `Forwarded`, `X-Forwarded-For`, `X-Real-IP` and other client-supplied
    forwarding headers do not grant access or replace the actual peer address;
30. peer rejection occurs before sync, candidate reads, decisions, disable or
    any other access to synthetic state;
31. the Host allowlist accepts only `127.0.0.1` and `localhost` with the
    effective local port;
32. Origin and Referer validation fails closed for mutations;
33. the CSRF token is random per process, is not accepted from query strings,
    is not persisted or logged and is discarded on termination;
34. actual-peer, Host, Origin/Referer and CSRF controls are cumulative;
35. every GET is non-mutating;
36. sync, decision and disable are available only through POST;
37. cross-origin requests, invalid Hosts, missing CSRF tokens and invalid CSRF
    tokens cannot execute sync, decision or disable behavior;
38. no productive cookie or session participates in the application;
39. the default productive application exposes no synthetic endpoint;
40. enablement cannot be supplied by a browser request;
41. every UI state visibly states `SYNTHETIC / NOT PRODUCTION`;
42. excerpts, categories, errors and identifiers are rendered only as escaped
    text;
43. synthetic markup and script-like input is displayed as text and never
    incorporated as active markup;
44. no candidate-derived value is passed to `innerHTML` or an equivalent unsafe
    operation;
45. the UI response supplies the required restrictive
    Content-Security-Policy;
46. the UI loads no external script, style, font, image or other asset;
47. no external-provider implementation, Google/Gmail client, network adapter
    or outbound provider connectivity exists;
48. the internal provider-neutral protocol imports no external-provider SDK and
    contains no real endpoint, hostname, scope or credential;
49. logs, errors and UI contain no prohibited content or secret-like value;
50. focused tests and relevant regression tests pass;
51. focused Ruff check and format check pass;
52. focused Pyright passes;
53. `git diff --check` passes; and
54. `git diff --name-only` contains only the Authorized File Boundary.

Conformance evidence must record commands and results without including fixture
message content.

The 10-of-10 synthetic classification result demonstrates only agreement with
constructed fixture oracles. It is not a measurement over real email, does not
satisfy Amendment 018's productive 8-of-10 classification criterion and cannot
be cited as real-pilot evidence.

## Implementation and Conformance Evidence

Implementation was limited to:

- `synthetic_netpay_intake.py`;
- `synthetic_netpay_intake_app.py`; and
- `test_synthetic_netpay_intake.py`.

The accepted functional evidence proves:

- an immutable manifest of 10 fixtures covering all five categories;
- an independent oracle;
- atomicity, concurrency, idempotency and checkpoint behavior;
- sanitization and redaction before the 4096-byte UTF-8 limit;
- explicit synthetic human decisions;
- the synthetic Commercial Intake boundary projection;
- productive isolation;
- cumulative peer, Host, Origin/Referer and CSRF controls;
- restrictive CSP and escaped rendering;
- the fixed entrypoint and human validation of the real TCP process;
- Post/Redirect/Get navigation; and
- fail-closed disable behavior.

Post-commit results were:

- focused synthetic suite: `37 passed, 1 warning in 73.30s`;
- bootstrap/main/NetPay Inbox regression:
  `17 passed, 1 warning in 44.89s`;
- Ruff check: PASS;
- Ruff format `--check`: PASS;
- Pyright: `0 errors, 0 warnings, 0 informations`;
- `git diff --check`: PASS;
- `git show --check HEAD`: PASS;
- Authorized File Boundary: PASS; and
- HUMAN VALIDATION: PASS.

The warning is a deprecation warning internal to Starlette TestClient and is
not a package failure.

Peer evidence is separated by layer: remote, IPv4 and IPv6 peer behavior was
tested through TestClient/ASGI; `client=None` was tested through a manual ASGI
scope; Uvicorn configuration was tested through interception; and the real
Uvicorn TCP process on `127.0.0.1:8765` was confirmed through human validation.
The ASGI remote-peer test is not represented as a real remote TCP connection.

An additional smoke attempt in the automation environment did not find the
local Windows interpreter, opened no listener and is not used as evidence.

The ADR-018 authorized synthetic Netpay intake package is terminally
IMPLEMENTED — CONFORMANT — EVIDENCE GATE PASSED, with no exceptions. This
completion neither satisfies nor opens any productive gate in Implementation
Roadmap Amendment 018.

## Rollback

Rollback consists exclusively of reverting or deleting the three files in the
Authorized File Boundary and stopping the dedicated local process.

Because the package creates no persistent state, migration, contract,
configuration or productive registration, no data rollback is required.

Rollback must leave unchanged:

- the default Yarvis application;
- productive authentication and authority;
- the canonical contract catalog;
- ADR-016 and ADR-017 Dispatch behavior;
- Netpay Inbox;
- Commercial Intake;
- Netpay Master;
- existing Cases; and
- deployment.

## Consequences

### Positive

- Provides a visible end-to-end demonstration before productive prerequisites.
- Exercises exact-once, rollback, classification and human-review semantics.
- Demonstrates the Commercial Intake ownership boundary without mutating it.
- Keeps Google, persistence and productive authority entirely closed.
- Demonstrates a server-side protected local surface without using productive
  identity, cookies or sessions.
- Provides a deterministic classification oracle across the full closed
  synthetic catalog.

### Costs and Risks

- The local application is a second temporary runtime surface.
- In-memory atomicity does not prove PostgreSQL transaction behavior.
- Fake-provider behavior does not prove Gmail API behavior.
- A 10-of-10 constructed-fixture result does not estimate real classification
  accuracy.
- Synthetic redaction does not approve a production sanitization algorithm.
- A standalone UI may diverge from the future productive UI.
- Peer, Host, Origin/Referer and CSRF controls add local harness complexity.
- Synthetic composition could accidentally grow into an unauthorized parallel
  application.

### Mitigations

- Three-file boundary.
- No modification of existing runtime or frontend files.
- Hard-coded IPv4 loopback bind and fail-closed actual-peer validation.
- Closed Host and same-origin mutation validation.
- Random per-process CSRF protection.
- Escaped server-side rendering and restrictive CSP.
- Fixed ten-message manifest with explicit expected results.
- No persistence or outbound provider connectivity.
- Explicit removal-only rollback.
- Separate future ADRs for every productive gate.

## Non-Evidence and Productive Gates

Passing this synthetic slice proves only the behavior explicitly listed in its
Evidence Gate.

It does not prove or satisfy:

- Gmail API behavior;
- OAuth topology or revocation;
- Google project ownership;
- secret storage;
- productive mailbox binding;
- productive Organization, Principal or Membership;
- productive roles or permissions;
- provider cursor/history behavior;
- database persistence or concurrency;
- classification accuracy on real email;
- Amendment 018's productive 8-of-10 classification threshold;
- productive UI security or usability;
- a production sanitization algorithm;
- production readiness;
- deployment readiness; or
- real-pilot GO/NO-GO criteria.

Every productive gate in Amendment 018 remains mandatory and unchanged.

## Open Decisions

This ADR deliberately does not select:

- the production sanitization algorithm;
- productive candidate persistence;
- a Gmail client library;
- an external-provider implementation;
- OAuth topology;
- secret storage;
- productive API or UI paths;
- canonical Gmail contracts;
- worker or scheduler topology;
- real mailbox or label identifiers; or
- productive Commercial Intake integration.

Each requires separate authority.

## Architecture Authority Act

- Decision: **ACCEPTED**
- Architecture Authority: **Guillermo de Hoyos**
- Decision date: **2026-09-06**
- Accepted proposal SHA-256: **`7DC8CD65015D120CFC8D325C04FB9A7C2D47955D9799FCB293FB3D20E4DB7BD5`**
- Hash basis: **Canonical UTF-8 without BOM, with CRLF and lone CR normalized to LF before hashing**
- Authorized package: **`ADR-018 authorized synthetic Netpay intake package`**
- Accepted exceptions: **None**
- Implementation status: **IMPLEMENTED — CONFORMANT — EVIDENCE GATE PASSED**
- Implementation commit: **`6682dd8add34063ac989dbd75ee8ec660ad0d99c`**
- Conformance authority: **Guillermo de Hoyos, Architecture Authority**
- Conformance decision date: **2026-09-06**
- Conformance exceptions: **None**

This act authorizes implementation only within the exact Authorized File
Boundary, Evidence Gate, isolation requirements and rollback defined by this
ADR.

It authorizes only the local/test, opt-in, in-memory and entirely synthetic
application described here. It does not authorize Google, Gmail, OAuth,
secrets, Google resources, real mailbox access, real messages, commercial
data, canonical contracts, business Handlers, productive persistence,
Repositories, models, migrations, productive routes, productive identity,
real Commercial Intake, Cases, workers, deployment or a real pilot.

Synthetic evidence cannot complete, waive or reduce any productive gate in
Implementation Roadmap Amendment 018.
