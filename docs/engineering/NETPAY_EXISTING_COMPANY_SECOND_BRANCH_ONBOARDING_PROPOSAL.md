# Existing Company — Second Branch Onboarding Proposal

Status: **ACCEPTED PROPOSAL — ARCHITECTURE AND DESIGN BASIS ONLY — NO CONTRACT REGISTRATION OR IMPLEMENTATION AUTHORITY**

Draft date: 2026-09-10. Proposed business owner: Netpay Merchant Operations.

## 1. Scope, authority and baseline

Architecture Authority authorized only a reviewable design proposal for Existing Company → Second Branch → Branch Onboarding Case → Versioned Checklist. These are selected candidate design decisions, not ratified decisions or implementation authority. Current gate: documentary design only. Next allowed action: independent review. Verify repository state before any subsequent change.

| Baseline fact | Verified value |
| --- | --- |
| Local and remote HEAD | `98bb791111e19c81dac893d0a9da110c8d731ee1`, branch `feat/operational-intake-spine` |
| ADR-020 SHA-256 | `2F486DE5D00B2F17ACF92C557DB30421E5A614B713FF51C81EDAB1E1DD227EA8` |
| Index / worktree before drafting | Empty index; only `?? AUDIT_REPORT.md`; its contents were not opened |
| Output path | This proposal filename was absent before creation |
| Package B | B1/B2/B3 unauthorized; Amendment 018 §8.3 open; §8.5 and later gates closed |

PROJECT_CONTEXT, CURRENT_STATE and CURRENT_SPRINT were read in order. Historical summaries do not authorize new implementation. Governing sources: [AR-001](../architecture/AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md), [MVP-1 Master](NETPAY_MVP1_MASTER_CONTRACT.md), [Amendment 012](IMPLEMENTATION_ROADMAP_AMENDMENT_012.md), [MVP-2 Inbox](NETPAY_MVP2_INBOX_CASE_CONTRACT.md), [ADR-017](../decisions/ADR-017_RATIFY_DISPATCH_HANDLER_FACTORY_COMPOSITION.md) and [ADR-020](../decisions/ADR-020_RATIFY_TEMPORARY_ROLE_AUTHORITY_ARCHITECTURE.md). Their existing authority and contract scope are preserved. This proposal changes none of those documents.

No real person, tax identifier, address, bank detail, image or commercial document is reproduced. Examples and future tests are synthetic. Amendment 016 D2/Merchant 360 and D3/logistics are excluded.

## 2. Case and discovery evidence

A synthetic existing Client and Company request a TPV for a distinct second physical Branch. The operator selects the existing legal entity, confirms identity, supplies the new location, reviews a pinned checklist and submits one operation. The result is a Branch and linked branch_onboarding Case with missing requirements, responsible Principal and next action. No Store ID or activation is required at opening.

Netpay assigns Store ID to its commercial product/asset. Store ID is not physical serial; e-commerce need not have a serial. Name is not a canonical key. Case.product is requested product, not confirmed enrollment. This slice covers one new physical Branch requesting TPV; it does not redesign multiple product enrollments or Branch/Store cardinality.

In path tables, S means `apps/api/src/yarvis_api/`; W means `apps/web/src/`.

| Physical evidence | Confirmed behavior | Consequence |
| --- | --- | --- |
| S/models/netpay_master.py: NetpayClient, NetpayCompany, NetpayBranch | UUIDs, tenant composite FKs, nullable tenant-unique Company tax_identifier, Company-scoped unique branch_match_key | Select canonical identity; names and browser state are insufficient |
| S/api/routes/netpay_master.py:create_branch | CMD-007 creates under an existing company_id | Reuse domain validation, not its committing HTTP wrapper |
| W/components/netpay/NetpayInboxWorkspace.tsx:CreateCaseFlow.submitMaster | Reuses Client but always creates Company and Branch | Existing-Company path must never call createCompany |
| S/api/routes/netpay_master.py:list_search_master, retrieve_master_detail | Search covers Client name/external_reference; list excludes nested Companies; detail requires branch_id | Explicit selector read profiles are needed |
| S/api/routes/netpay_inbox.py:_masters, create_case | CMD-009 validates Client/Company/Branch chain; Store check only proves tenant and active status | Prove full Store/Branch/Case chain in the new operation |
| Same: _ensure_catalog, classify_case | Creates case types, not templates; selects highest active template; classification may append items repeatedly | Govern activation and prevent snapshot replacement/duplication |
| Same: transition | Checks existing items; an empty collection can satisfy that part of completion | Empty or missing snapshot must fail closed |
| S/models/netpay_inbox.py | Template JSON, template_version, item status, next actions and evidence-reference models | Existing fields alone do not prove immutable snapshot or provisioning |
| S/api/routes/netpay_master.py:assign_or_correct_store_reference | Overwrites the active reference's Store identifier | History-preserving correction requires an explicit profile amendment |
| S/services/netpay_master_receipts.py:execute | Existing Master receipt service uses begin_nested; HTTP route commits | Do not invoke it inside a new ADR-017 Handler |
| S/canonical_contracts.py; S/bootstrap.py | Master RATIFIED/VERIFIED; Inbox RATIFIED/PLANNED despite composed routers | HTTP existence is not Dispatcher admission or authority for promotion |

Search found no productive template-construction/provisioning endpoint; test fixtures do not establish one. NetpayCaseDocumentReference is not a document upload workflow. Evidence is repository inspection, not production inspection.

## 3. Deterministic Company selection

Selected identity is `(resolved organization_id, client_id, company_id)`. A UUID identifies a row, but does not alone prove that it is the intended legal entity. The candidate selector requires active Client and Company, the exact parent relationship and a non-null normalized tax_identifier. Missing tax identifier blocks this slice with COMPANY_IDENTITY_UNVERIFIED. A note, checkbox or manage permission cannot override it. A separately authorized identity-resolution workflow must resolve the missing identity first; this proposal neither supplies that workflow nor creates another Company.

Exact normalized tax lookup must identify one Company inside the resolved tenant. Name search returns candidates only. Ambiguous, inconsistent, inactive or mismatched results block confirmation. The protected confirmation view displays authorized legal name, canonical Client/Company identity and tax identifier only where existing read authority permits. Do not expose tax values in URL query strings, audit payloads, logs or exports; an exact-search value may be carried in a protected request body. RFC is not authentication or permission.

The final Command locks and rereads the chain and checks an expected material Company-identity fingerprint against current identity/status/relationship. It is a scoped server digest for stale-selection detection, never an authority token. A change requires renewed human confirmation. This stricter operation does not invalidate no-RFC Master rows used by unrelated flows.

For this physical Branch, require sufficient address/locality/postal information for disambiguation. The Company-scoped normalized Branch match key remains the existing duplicate defense. Exact matches reject with DUPLICATE_BRANCH unless replay proves this operation's original result. Approximate matches require review; no automatic merge, reparenting or alternate-spelling retry. Homonymous Companies without verified identity cannot be selected solely by label.

## 4. Atomic creation and alternatives

| Alternative | Benefit | Disposition |
| --- | --- | --- |
| Sequential CMD-007 then CMD-009 | Reuses endpoints | Not selected: Branch can commit before Case/template failure; cannot guarantee all-or-none |
| Expand CMD-007 to create Case | Fewer operation names | Rejected: silently expands Master side effects, permissions and result |
| Expand CMD-009 to create Branch | Case-centered | Requires explicit versioned amendment; not selected because it changes existing create-Case semantics |
| New OpenExistingCompanyBranchOnboarding owner Command | One business intent and atomic result | Selected candidate; requires separate allocation and implementation authority |
| Saga / compensating deletion | Distributed recovery | Rejected: unnecessary here; deletion is not safe historical repair |

One Netpay-owned Command creates Branch, linked Case, full checklist snapshot/items, responsible assignment, initial next action, activity, safe Domain Events and original-result receipt. All commit in one Dispatcher-owned Session/UoW through exactly one CommandUnitOfWork facade commit. No nested Dispatch, second UoW, savepoint, autonomous transaction or post-failure persistence. Neither existing committing HTTP wrappers nor savepoint receipt services are participants. Bounded refactoring may extract commit-free domain validation after authorization.

Candidate input: client_id, company_id, expected identity fingerprint, new Branch location/name, requested_product fixed to tpv, safe request summary, expected outcome, active same-tenant responsible_principal_id, initial action/due date, source channel, optional opaque source reference, request_intent_id, idempotency key and expected template UUID/version/digest. Tenant and actor come from trusted context. No Company-creation, Store, serial or activation fields are accepted.

Successful result: operation/receipt ID, Branch UUID, Case UUID/folio, snapshot UUID/version/digest, responsible Principal, initial action ID and original Case state. Persist this safe response snapshot atomically. Replay returns it unchanged; current-detail Query is separate and may show later state. Stored result is not current authority.

For Cases created by this operation, Branch and snapshot references are mandatory. A unique creation-operation relationship identifies the pair. Existing standalone Branches remain valid under their original contracts; this slice does not delete or retroactively label them orphans. Adopting an existing Branch is a distinct intent, not repair for failed opening.

## 5. Idempotency, concurrency and failures

Use a receipt unique on `(organization_id, command identity, idempotency_key)` and an operation intent unique on `(organization_id, operation kind, request_intent_id)`. The UI retains both across retries and uncertain outcomes. Same intent with the same functional fingerprint returns the original result even if the transport key changed; differing functional content conflicts. A different intent cannot bypass Branch uniqueness. External references are provenance, not uniqueness keys unless an approved source namespace guarantees that property.

The server computes the functional fingerprint from canonical IDs, expected identity, normalized Branch input, requested product, safe request/source references, responsible/action and pinned template identity. Exclude credentials and documents. Hashing sensitive input does not make it anonymous; protect fingerprints and never export them as public audit data. Receipt stores safe result/identifiers, not full input or raw RFC.

Admission precedes replay. Proposed lock order: established authority protection; selected Client then Company; checklist activation binding then immutable template; operation-intent/receipt key; new Branch/Case and child state. Sort IDs within each class. All participating Company/template/profile writers must be inventoried and aligned before implementation claims this order. Fresh rereads follow waits; stale ORM objects are not proof. No acquiring earlier-order resources after later-order writes.

Company locking serializes new Branch creation under that Company; unique Branch and intent/receipt constraints remain final defenses. Uniqueness/deadlock failure aborts completely; no internal second UoW reads a winner. A later independently admitted request resolves/replays. Same-request committed replay uses its original snapshot even if that version was later retired; it creates no new Case under the retired version.

| Outcome | Durable state | Response / recovery |
| --- | --- | --- |
| Admission/validation failure | No new resources | Controlled error; foreign/unknown targets concealed equally |
| Confirmed rollback, including evidence/receipt failure | No Branch/Case/snapshot/action/result from this operation | Preserve primary exception, never success; no SQL repair |
| Acknowledged commit | Complete resource set and receipt | Original safe result |
| Lost commit acknowledgment | All or none, unknown to caller | UNCERTAIN_RESULT; later governed readback/replay, no second UoW in original Command |
| Replay after revoked authority | No mutation or result disclosure | Deny before receipt lookup |

Error precedence: current authentication/permission; tenant-safe target admission; replay/intent conflict; identity/duplicate validation; pinned-template validation; write/concurrency failure; commit outcome. Absence of a receipt during an in-flight operation is not proof of rollback. Canonical authority unavailable means denial, not inferred success or repair permission.

## 6. Versioned checklist and provisioning

Netpay Merchant Operations owns policy and Case compliance. Document Registry or a separately authorized evidence repository owns files. This slice includes safe references and human assessments only, not file storage, image recognition or automatic fetching. References must be opaque, tenant-validated and access-controlled; their existence does not prove compliance.

Candidate PublishBranchOnboardingChecklist Command accepts a reviewed artifact/reference and digest, scope/version and expected active binding. It inserts an immutable version and atomically changes the activation binding for `(Organization, branch_onboarding, tpv)`. First publication explicitly expects no active version. Positive monotonic versions and one active binding per scope are required. Retired content is preserved for existing Cases. No runtime seed, startup auto-provisioning, direct SQL or unrestricted template editor.

No current permission authorizes checklist publication. Ordinary netpay.inbox.manage must not silently gain policy-administration power. A future act must allocate a narrow publication capability and admission mechanism; until then provisioning is denied. This proposal allocates no permission string, role or contract number. An artifact reference or environment flag is not authority.

The UI pins template UUID/version/content digest. The opening Command checks the same version is active under lock; a change yields TEMPLATE_CHANGED and renewed review, not silent selection of a newer template. Snapshot copies scope, UUID, version, digest, requirement definitions, cardinalities, applicability, evidence classes, reason vocabulary and completion rules. Snapshot definitions are immutable; assessment history is separate mutable-by-command state.

Missing/empty/invalid template, duplicated keys or unsupported product aborts opening. Case.checklist_template_version alone is insufficient. A candidate creation-profile discriminator scopes mandatory Branch/snapshot constraints to these new Cases without falsely certifying or backfilling historical Cases.

Use NOT NULL, same-row CHECK and unique constraints for structural invariants. Cross-row photo counts, ownership and completeness require protected owner validation, not a CHECK that reads other rows. All assessment writers serialize on Case and validate the pinned snapshot. Generic classify/checklist/action/state endpoints must enforce the same profile or reject its mutation. Reclassification, silent snapshot replacement and duplicate snapshot append are prohibited. Unknown profiles fail closed.

### 6.1 Candidate documentary rules

| Requirement | Cardinality / predicate | Human decision |
| --- | --- | --- |
| Interior photos | Exactly two distinct accepted references: interior_1, interior_2 | Confirm appropriate interior evidence; missing/rejected slot blocks |
| Exterior/facade photos | Exactly two distinct accepted references: exterior_1, exterior_2 | Confirm category and acceptable image; missing/rejected slot blocks |
| Operating business | Explicit operating and not-under-construction assessment | Controlled finding and safe evidence; construction blocks |
| Bank evidence | One current accepted item with recognizable original-document format | Original-document photo potentially acceptable; screenshot without original format invalid; redacted figures alone do not invalidate |
| Other fiscal/service evidence | May be referenced without inventing official requirements | Required status and legal validation need a separately approved policy; this checklist does not certify full Netpay compliance |

Exactly two refers to the current accepted set per category. Rejected/replaced historical submissions remain. A third item cannot silently become accepted; replacement retires the old slot association and appends history atomically. The same evidence item cannot fill multiple photo slots. Human review checks duplicate content; distinct opaque IDs alone do not prove distinct images. No automated authenticity guarantee.

A bank photo or redaction is never auto-approved. Reviewer must establish recognizable original format and sufficient nonsensitive context. Otherwise leave pending/rejected. No banking numbers or redacted values enter summary fields. The screenshot rule specifically rejects missing recognizable original format; it does not invent a blanket rejection of all screenshots.

Assessment states: missing, pending_review, confirmed, rejected. Mandatory rules in this profile cannot use not_applicable as a waiver. Each revision records actor Principal, time, previous/new state, controlled reason, safe explanation and evidence reference. Candidate reason codes: EVIDENCE_MISSING, WRONG_EVIDENCE_CATEGORY, DUPLICATE_EVIDENCE, PHOTO_CARDINALITY_MISMATCH, BUSINESS_NOT_OPERATING, BUSINESS_UNDER_CONSTRUCTION, BANK_ORIGINAL_FORMAT_MISSING, EVIDENCE_UNREADABLE, EVIDENCE_REPLACED, HUMAN_REVIEW_CONFIRMED. These are local candidate codes, not registered Events.

Whenever an active Case has unresolved requirements, one open next action with active same-tenant responsible Principal, safe description and due date is mandatory. Creation supplies it. Closing/cancelling that action requires atomic replacement while missing/pending/rejected requirements remain. Rejection preserves or updates the action in the same transaction. It may summarize multiple missing items. Terminal cancellation preserves history and is not reopening authority.

Initial state is received with unresolved items. Existing triage/information_pending semantics remain. Profile-specific guards block ready/submitted/completed on empty snapshot, invalid counts or unresolved mandatory assessment. No missing-action escape is permitted. Checklist completion means only this pinned policy is satisfied, not bank approval, fiscal verification, confirmed product enrollment or external activation.

## 7. Store ID received later

Netpay creates Store ID. Existing CMD-008 allows a current netpay.master.manage operator to record its source/confirmation on a Branch; this proposal grants that permission to no one. Confirmation identifies the external reference, not activation or first sale. Keep the current one-active-reference-per-Branch limit; multi-product Store cardinality is outside scope.

CMD-008 alone does not atomically update Case linkage and preserve complete identifier-correction history. Selected candidate RecordOnboardingStoreReference requires both master.manage and inbox.manage, a Case/Branch pair from this operation, expected current reference/version, externally assigned identifier, source type/reference, confirmation flag and safe reason. Validate the full Organization/Client/Company/Branch/Case chain and Store uniqueness; reject cross-Branch transfers and serial input.

Initial recording creates or confirms the same-Branch reference, updates the current Case Store link and appends link history, activity and original-result receipt in one UoW. A different active identifier requires the explicit correction variant and expected version; never silently overwrite it. A separately registered Store reference may remain linkage-pending until the new Command runs; that is not partial initial Branch/Case creation.

For identifier-changing correction, preserve old Store reference identity/value, end its active association, create a replacement with supersedes linkage, and append Case linkage history, actor, source, evidence and safe reason. Accepted facts, Events and receipts continue to reference the original UUID; they are never relabeled or rewritten. Same-ID confirmation appends evidence without inventing a new Store. Stale/conflicting correction rolls back fully.

Existing CMD-008 must enforce equivalent history rules or reject overwrite of references protected by this profile. It cannot remain a bypass. This therefore requires an explicit contractual/profile amendment, not merely a new UI button. It does not authorize physical transfer or batch reconciliation. Requested product remains Case.product; confirmed product/activated_at remain No disponible absent a separately governed source. No serial is mandatory for e-commerce; this slice creates no physical-asset model.

## 8. Contract inventory and candidate semantics

Inventory sources: INTERACTION_CONTRACT_CATALOG.md, canonical_contracts.py, Master/Inbox profiles, ratified Amendments and route composition at the baseline. Absence from runtime does not make an ID free: Amendment 016 includes future D2/D3 allocations; Gmail/Intake IDs are separate. No new numeric ID is selected, allocated, reserved or registered. Semantic candidates below require later complete inventory recheck and explicit allocation authority.

All numeric entries below have prefix `IC-NETPAY-`.

| Existing contract | Existing purpose | Proposed disposition |
| --- | --- | --- |
| CMD-005 / CMD-006 | Client / Company creation | Separate deliberate new-Company workflow; not called by this slice |
| CMD-007 | Branch under Company | Preserve standalone semantics; reuse commit-free validation only |
| CMD-008 | Store reference assign/correct/remove | Explicit history guard/amendment for protected references |
| QRY-003 / QRY-004 | Master search / detail | Versioned Company-selection profiles, including canonical-ID detail |
| CMD-009 / CMD-010 | Case creation/classification | Preserve generic intent; block new-profile bypass and duplicate snapshots |
| CMD-011..015 | Checklist, assignment, next action, transition, activity | Explicit profile guards for cardinality, assessment history and mandatory action |
| QRY-005 / QRY-006 | Inbox list/detail | Explicit safe snapshot/assessment read profiles |
| EVT-003..006 | Case creation/classification/state/activity | Retain meanings; exact mappings and payloads require owner review |

Legacy CMD-001..004 are not repurposed. Master metadata is RATIFIED/VERIFIED; Inbox remains RATIFIED/PLANNED despite direct HTTP routes. The new implementation gate must reconcile its own admission/composition explicitly; no filter change or implicit operational promotion. This proposal changes no current catalog or dispatch component.

| Candidate semantic label; numeric ID unassigned | Input / result | Authority and boundary |
| --- | --- | --- |
| OpenExistingCompanyBranchOnboarding | Section 4 intent → immutable Branch/Case/snapshot/action result | Both netpay.master.manage and netpay.inbox.manage; one UoW |
| PublishBranchOnboardingChecklist | Reviewed content, version and expected binding → publication receipt | Narrow publication authority must be allocated separately |
| RecordOnboardingStoreReference | Section 7 identifiers/source/expected version → Store/Case-link/history result | Both manage scopes; no transfer; one UoW |
| ResolveOnboardingOperationResult | Original opaque intent/operation ID → original result or not-established outcome | Fresh tenant-safe read admission; absence during in-flight processing is not proven rollback |

Selected selector alternative is explicit QRY-003/QRY-004 profile amendments, because normative search/detail intent already includes Company/tax search. Version compatibility and owner review are mandatory, not implicit permission for endpoints. If incompatible, a new Query requires separate allocation. Operation-result lookup may be a reviewed detail-profile extension; it is never an ungoverned receipt endpoint. Checklist provisioning is a governed Command, not startup configuration.

No transport is implemented. Future HTTP shape must map to approved contract semantics and composition. Real Dispatcher tests require separately authorized dispatchable definitions/composition using existing statuses. Neither an HTTP route nor this proposal promotes contracts. No temporary role or Package B dependency is introduced.

## 9. UI and security

Flow: search → select existing Client/Company → protected identity confirmation → distinct Branch location → requested TPV and pinned checklist preview → responsible/action → final summary → one compound submission → Branch/Case result links. Never auto-select a search hit. Ambiguity or missing verified identity disables confirmation with a safe explanation.

Summary distinguishes reused Company, new Branch, requested product, checklist version/faltantes, responsible/action and not-yet-assigned Store ID. Do not commit intermediate Client/Company/Branch changes before confirmation. Retain intent/key on retry; uncertain outcome displays verification pending rather than success or a new identity-generating retry.

Create new Company is a separate deliberate entry using its own contract/authority/dedupe review; it exits this flow. It cannot silently copy a selected candidate or bypass missing identity. No real record is created by this proposal.

Combined operations require the intersection of existing master/inbox manage scopes, never their union. Read profiles require relevant master/inbox read scopes. Server-resolved Organization and current authority govern every lookup and replay; body values, headers and UI flags do not grant permissions. Unknown/foreign targets are concealed equally. Publication requires separately authorized narrow authority. No new broad role.

Evidence references are tenant-validated opaque handles, not arbitrary URLs to fetch or credentials. No OCR, fetching images, bank extraction, real documents or PII in Git/tests/logs/Events. Constrain safe activity text; free text is not a document repository. Existing privacy obligations remain; no new real-document storage or privacy gate is opened.

## 10. Candidate File Boundary — not authorization

Only this proposal is writable now. Existing candidates below are bounded suggestions, not blanket refactoring, promotion or implementation permission. S/W expand as defined in section 2.

| Existing path | Candidate purpose |
| --- | --- |
| S/api/routes/netpay_master.py | Selector profiles and protected-reference history guard |
| S/api/routes/netpay_inbox.py | Enforce snapshot/assessment/action/transition guards |
| S/models/netpay_master.py | Scoped operation identity and Store history linkage |
| S/models/netpay_inbox.py | Snapshot/profile discriminator and assessment integrity |
| S/schemas/netpay_master.py | Company-selection schema |
| S/schemas/netpay_inbox.py | Snapshot, evidence and compound result |
| S/services/netpay_master_receipts.py | Bounded commit-free extraction if necessary; no savepoint reuse inside Handler |
| S/bootstrap.py | Separately authorized composition only |
| S/canonical_contracts.py | Later explicit registration/profile changes only |
| W/api/netpay.ts | Reviewed selector/compound clients |
| W/components/netpay/NetpayInboxWorkspace.tsx | Existing-Company flow |
| W/components/netpay/NetpayInboxWorkspace.test.tsx | Synthetic selection/retry/no-duplicate UX |
| apps/api/tests/test_netpay_master.py | Dedupe, tenancy and history regressions |
| apps/api/tests/test_netpay_inbox.py | Profile guard and completion regressions |
| docs/architecture/INTERACTION_CONTRACT_CATALOG.md | Later explicit allocation only |
| docs/engineering/NETPAY_MVP1_MASTER_CONTRACT.md | Selector/protected-reference amendments |
| docs/engineering/NETPAY_MVP2_INBOX_CASE_CONTRACT.md | Snapshot/assessment/action profiles |

| New proposed path, not an existing artifact | Candidate purpose |
| --- | --- |
| apps/api/src/yarvis_api/application/branch_onboarding.py | Closed intent/result interfaces |
| apps/api/src/yarvis_api/services/branch_onboarding.py | Commit-free owner orchestration and factory |
| apps/api/src/yarvis_api/services/branch_onboarding_checklist.py | Policy publication and assessment rules |
| apps/api/src/yarvis_api/services/branch_onboarding_store.py | Atomic Store/Case linkage and history |
| apps/api/src/yarvis_api/models/branch_onboarding.py | Operation receipts, snapshots/assessment and link history where existing models cannot suffice |
| apps/api/tests/test_branch_onboarding.py | Real handler atomicity/replay evidence |
| apps/api/tests/test_branch_onboarding_concurrency.py | Isolated PostgreSQL races/uncertain results |

An additive migration will be required if this schema is authorized. No filename, revision or parent is allocated; baseline head 20260823_47 must be rechecked. A permission-definition file, publication admission adapter, route or migration not listed must be named and separately approved in the exact implementation boundary. Unresolved artifact names are not edit allowances. No asset, dashboard, provider or worker artifact is proposed.

## 11. Candidate Evidence Gate

No proposed gate has run or passed. Use synthetic fixtures and real isolated PostgreSQL for transaction/FK/unique/concurrency claims. Existing Master/Inbox tests are regressions, not proof of the new slice.

| Area | Mandatory future evidence |
| --- | --- |
| Selection | Company/tenant/Client exact match; name-only and missing-RFC blocks; homonyms, inactive/foreign/stale identity; sensitive-search redaction |
| No duplicated Company | Existing-Company flow makes no CMD-005/006 calls; unchanged Client/Company rows |
| Atomic opening | Inject failure after every Branch/Case/snapshot/action/Event/receipt write; no partial durable combination; real Dispatcher and exactly one UoW/facade commit |
| Replay | Same key/intent; changed fingerprint; regenerated key; lost ack/restart; original result after later Case changes; denial before replay after authority loss |
| Concurrency | Same Branch/intent; activation versus opening; Company change versus opening; competing assessments/action replacement; Store confirmation/correction |
| Template | Missing/empty/invalid template fails; one active binding; pin/digest mismatch; immutable versions and existing snapshots; no reclassification bypass |
| Evidence | Exactly two distinct accepted photos per category; extra/replaced/duplicate evidence; operating/construction checks; invalid bank screenshot; no automatic photo/redaction approval |
| Completion | Empty snapshot never passes; mandatory items cannot waive; unresolved requirements require open action/assignee; readiness/submission/completion guards; no inferred activation |
| Store later | Initial absence; full-chain linkage; foreign/other Branch denial; correction preserves old UUID/facts/receipt; no serial requirement |
| Authority | Combined scopes, no publication without narrow authority, no metadata promotion/filter bypass, all alternate profile writers guarded |
| UI/privacy | Synthetic references only; no bank/RFC leakage or external fetch; explicit ambiguity/uncertain state and safe reload |
| Structural | Authorized additive migration and empty-schema rollback; historical compatibility; lint/type/build and bounded backend/UI regression |

Exact contract/admission/composition authority must precede tests needing operational definitions. Direct service invocation or Session doubles alone are insufficient. Future implementation authorization must name files, migration, admission, evidence, rollback and independent conformance. No real assignment or provider access is test setup.

## 12. Rollback and recovery

This document creates no runtime state. Withdrawal of the untracked proposal requires separate explicit instruction; no removal is performed. Future release rollback first disables admission to the new operation and preserves readers of committed snapshots/history. Reverting UI must not reactivate unsafe legacy mutation paths for protected Cases.

Confirmed failed opening leaves none of its resources. Lost acknowledgment requires later governed readback/idempotency; never delete Branch because a client saw an error. No SQL repair, receipt reset, fingerprint alteration, historical deletion or new key to evade conflict. Cancellation is an owner operation preserving Branch/snapshot/history, not a compensating delete.

Downgrade is permitted only when scoped data is proven absent in an authorized isolated environment. With committed Cases or history, preserve schema/read compatibility and use a reviewed forward fix. Template retirement affects new requests only; existing snapshots remain authoritative for their Cases. A new policy cannot silently rewrite past compliance.

## 13. Risks, subsequent sequence and limits

| Risk | Treatment / later requirement |
| --- | --- |
| Legitimate Company lacks RFC | Deliberate slice block; separate identity-resolution authority, no name exception |
| Semantic expansion | New compound intent and explicit profile amendments need owner acceptance/allocation |
| Publication authority absent | Provisioning denied until narrow capability/admission are separately authorized |
| Existing wrapper transactions | Extract only commit-free logic; align bypass writers and prove one UoW |
| Stale policy | Preserve snapshots; mandated reassessment needs a separate governed operation |
| Human review errors | Audited decisions; no automated authenticity/bank-approval claim |
| Store correction and imported facts | Preserve original reference identities; no analytical rewrite or Merchant 360 |
| PLANNED metadata/direct routes | Explicit reconciliation before new composition; no inferred promotion |
| Candidate boundary incomplete | Exact migration, admission paths, schemas and IDs need later approval, not developer inference |

Sequence: independent review; expressly authorized corrections; Architecture Authority acceptance as design input; required architecture/contract amendments and allocation; separate bounded implementation authorization; synthetic implementation/evidence; independent conformance; separately authorized release/operation. Naming these steps executes none. Immediate next action is review.

Excluded: Merchant 360/D2, consolidated sales, Core/Salesforce APIs, Gmail intake, assets/serials, batch Store/serial reconciliation, Package B B1/B2/B3, pricing, deployment and production. Amendment 018 §8.3 remains open; §8.5 and later gates closed. No role, permission, Membership, temporary assignment, contract reservation, secret or real document is created. ADR-019/020 and policy sources remain unchanged.

## 14. Independent Review — PENDING

| Field | Value |
| --- | --- |
| Status | PENDING |
| Reviewer | [not recorded] |
| Reviewed version / canonical hash | [not recorded] |
| Review date | [not recorded] |
| Verdict | [not recorded] |
| Mandatory findings / disposition | [not recorded] |

Documentary validation is not independent review or acceptance.

## 15. Architecture Authority Act

| Field | Value |
| --- | --- |
| Act ID | [not recorded] |
| Architecture Authority | Guillermo de Hoyos, Architecture Authority of Yarvis |
| Decision | ACCEPTED PROPOSAL — architecture and design basis only |
| Decision date | 2026-09-11, local date of Architecture Authority; not adjusted to server time or UTC |
| Reviewed proposal version | Commit `e8a7b980375eaec6fe1466f3ac33d4de167b8cd7` |
| Reviewed canonical SHA-256 | `9F488CE5D5B02E2600CD5BCDDD9511B4E90CB1BA4041E7D46838A25030E121D9` |
| Independent review reference | Terminal independent verdict expressly accepted by Architecture Authority in this act; no separate report identifier supplied |
| Independent review verdict | ACCEPT |
| Accepted scope | Existing Company → Second Branch → Branch Onboarding Case → Versioned Checklist, exclusively as an architecture and design basis |
| Mandatory findings remaining | None; no CRITICAL, HIGH or MEDIUM findings and no mandatory amendments pending |
| Contract allocation authority | None; no contract identifiers assigned, registered or promoted |
| Implementation work packages | None authorized |
| Exact Authorized File Boundary | This proposal only, solely to record and publish this acceptance; no implementation boundary authorized |
| Evidence Gate | No implementation gate opened or passed; a later applicable instrument must define it |
| Rollback authority | None granted for implementation or operation; a later applicable instrument must define rollback |
| Release / operation authority | None |
| Exceptions | None |
| Downstream authority | None |

This records the acceptance issued by Guillermo de Hoyos, acting as Architecture Authority of Yarvis. It accepts the terminal independent verdict ACCEPT and the reviewed proposal solely as an architecture and design basis. It is not architectural ratification or implementation authority. No Act ID is invented. The preparation-time status, pending review table in section 14 and delivery instructions elsewhere remain historical records; this dated act supersedes only their current acceptance, next-action and documentary-publication readings. It does not identify an unsupplied reviewer or review date, and does not alter the reviewed technical body.

Legal identity must be resolved through canonical tenant-scoped references, using Company UUID and normalized RFC when available. Commercial name is not sufficient identity. Ambiguous or cross-Organization selection must fail closed. This acceptance does not create a name-based exception to the reviewed slice's missing-RFC guard.

The following are accepted as design decisions only:

- Explicit reuse of existing Client and Company, with no silent creation of another Company.
- Coherent, atomic creation of Branch, Case and checklist snapshot.
- Idempotency through `request_intent_id` and a functional fingerprint, with governed resolution of uncertain outcomes.
- A versioned checklist with an immutable snapshot; a missing, empty or invalid template must prevent opening or closing the case.
- Explicit documentary cardinality and human, audited document assessment.
- Later incorporation of the Store ID assigned by Netpay.
- Separation of requested product, confirmed product, assigned Store ID and external activation.
- Strict Organization scoping, sanitized document references and no real documents in Git.

This acceptance assigns no contractual identifiers, registers or promotes no contracts, and authorizes no implementation, migrations, code, tests, configuration, data, production access or deployment. It does not authorize Merchant 360/D2, D3, Core/Salesforce integration, Gmail intake, asset models, serial numbers, batch Store ID–serial reconciliation, pricing or Package B B1/B2/B3. Amendment 018 §8.3 remains open; §8.5 and later gates remain closed.

Before any implementation, the architectural or authorization instrument required by AR-001 must exist, with exact contracts, an Authorized File Boundary, an Evidence Gate, rollback and independent review. This act authorizes only recording this acceptance in this proposal and publishing a commit that changes this document alone. Accepted exceptions: None. Downstream authority: None.

## 16. Documentary delivery checks

Only this proposal is created. Verify UTF-8 without BOM and LF, tables/headings/fences, synthetic-only content, candidate path classifications, git diff --check including this untracked file, unchanged baseline/ADR-020 hash, empty index and final status. Report canonical SHA-256 externally, not self-referentially inside the document. No staging, commit or push. Stop for independent review.
