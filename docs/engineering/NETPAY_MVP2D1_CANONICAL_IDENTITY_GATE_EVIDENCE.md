# YARVIS
# Netpay MVP-2D1 Canonical Identity Gate Evidence

## Status

**ACCEPTED — CANONICAL IDENTITY EVIDENCE CONFORMANT — NO DOWNSTREAM AUTHORITY**

## 1. Purpose and authority boundary

This document assembles sanitized evidence exclusively for the Canonical
Identity requirements in §3.2 and §8.2 of
`IMPLEMENTATION_ROADMAP_AMENDMENT_018.md`.

It is an evidence record, not an Architecture Decision Record, implementation
authorization, contract allocation, productive configuration, or release
authority. Its material conclusion is provisional until expressly accepted by
the Yarvis Architecture Authority.

This document does not close §12.2 as a whole and does not open §8.3 or any
later productive gate.

## 2. Governing and supporting documents

- `IMPLEMENTATION_ROADMAP_AMENDMENT_018.md` — ratified design authority for
  the current-HEAD MVP-2D1 reconciliation and the controlling gate sequence.
- `AR-001_ARCHITECTURE_RATIFICATION_FRAMEWORK.md` — authority, evidence, and
  ratification framework.
- `NETPAY_MVP2D1_CANONICAL_IDENTITY_PROVISIONING_DISCOVERY.md` — historical
  discovery evidence.
- `NETPAY_MVP2D1_CANONICAL_IDENTITY_PROVISIONING_DISCOVERY_REVIEW.md` — first
  historical review.
- `NETPAY_MVP2D1_CANONICAL_IDENTITY_PROVISIONING_DISCOVERY_SECOND_REVIEW.md` —
  second historical review.

The historical discovery and reviews remain historical evidence. This record
does not rewrite them or treat their earlier partial-path conclusions as proof
of the later productive state.

## 3. Evidence scope

The evidence assembled here is limited to demonstrating:

1. exactly one active canonical Organization at the UUID ratified by Amendment
   018;
2. absence of the historical Organization UUID identified by Amendment 018;
3. the canonical Organization's approved display and legal identity fields;
4. exactly one active Founder Principal and its active Person;
5. exactly one active Identity Binding for that Principal;
6. binding agreement with the effective productive OIDC issuer without
   disclosing the issuer or subject;
7. structurally present normalized subject and valid normalization provenance;
8. absence of active binding ambiguity;
9. exactly one active, non-revoked Membership linking the Principal to the
   canonical Organization;
10. the existing canonical role and permissions on that Membership;
11. at least one current productive session for the same Principal,
    Membership, and Organization;
12. consumption of the Founder handoff;
13. closure of Founder Bootstrap;
14. effective runtime disablement of Founder Bootstrap; and
15. absence of ambiguous issuer-plus-normalized-subject pairs across
    Principals.

No cookie, session hash, token, subject, effective issuer, email, personal
name, secret, productive URL, or exact productive timestamp is recorded.

## 4. Baseline

| Field | Value |
| --- | --- |
| Repository branch | `feat/operational-intake-spine` |
| Documentary repository baseline | `a4006233dc9eea41a339f877295cbff341236bd5` |
| Remote baseline | `origin/feat/operational-intake-spine` at `a4006233dc9eea41a339f877295cbff341236bd5` |
| Evidence environment | Productive Yarvis Web Service on DigitalOcean |
| Evidence dates | 2026-09-06 through 2026-09-07 |
| Exact deployed revision at execution | **[not independently recorded]** |
| Canonical Organization UUID | `6c2bbf37-87d1-4315-8e67-85e9957c9aa7` |

The environment and dates identify the evidence context without disclosing
productive connection details or exact event timestamps. The repository
baseline is documentary context; it is not a claim that the exact deployed
revision was independently attested during the procedure.

## 5. Architecture Authority acts permitting evidence collection

The following narrowly bounded acts were recorded in the governing
conversation:

1. On 2026-09-06, **Guillermo de Hoyos, Architecture Authority**, authorized
   one execution of the canonical original read-only procedure to verify the
   Organization, Founder identity chain, current session, handoff, and
   bootstrap closure.
2. On 2026-09-07, **Guillermo de Hoyos, Architecture Authority**, authorized
   one execution of the aggregate read-only session diagnostic identified in
   §7.4 after the canonical procedure found no current Founder Principal
   session.
3. On 2026-09-07, **Guillermo de Hoyos, Architecture Authority**, accepted the
   aggregate diagnostic evidence and authorized one ordinary fresh productive
   OIDC authentication by the same user, followed by one immediate execution
   of the unchanged canonical original procedure within five minutes of a
   newly confirmed successful session response.
4. On 2026-09-07, **Guillermo de Hoyos, Architecture Authority**, renewed only
   the operational five-minute window for that single final execution after
   transport attempts that had not invoked the procedure.

Each act prohibited unrelated writes or changes. No act authorized Founder
Bootstrap, identity repair, Membership or Organization changes, new roles or
permissions, Gmail, OAuth configuration, secrets, deployment, or a second
execution under the same authorization.

## 6. Canonical original procedure

The canonical original read-only procedure used for the conclusive evidence
has this SHA-256:

`D12D2894DA708BC7213FA295114045E83F48EE1624EDA2C3982A32C2EB618749`

The approved script:

- instantiated the canonical application settings;
- obtained the injected database URL in memory through the canonical
  `SecretStr` API without printing it;
- opened an explicit transaction;
- issued `SET TRANSACTION READ ONLY`;
- verified `transaction_read_only`;
- applied a statement timeout;
- executed only evidentiary `SELECT` queries;
- emitted only a controlled, sanitized result;
- rolled back the transaction;
- closed the connection; and
- disposed the engine.

Errors were reduced to controlled codes. Connection values, issuers, subjects,
claims, cookies, tokens, session hashes, PII, and secrets were neither printed
nor extracted.

## 7. Evidence chronology

### 7.1 Transport attempts that were not executions

Three kinds of console transport failure occurred before successful transport:

1. multiline paste attempts that did not start Python and emitted no procedure
   evidence;
2. attempts in which only the SHA-256 text was pasted and Bash returned
   `command not found`; and
3. one truncated attempt that printed the external marker
   `CANONICAL_EVIDENCE_STARTED=true`, omitted the Python invocation entirely,
   and ended with `bash: exit: numeric argument required`.

The isolated external marker in the third case does not constitute the start
of the canonical procedure because the Python invocation was absent. None of
these transport attempts opened a database connection, executed SQL, or
produced evidence, and none is used in the matrices below.

### 7.2 First verifiable canonical execution

The first verifiable invocation of the canonical original procedure completed
cleanup and reported:

```ini
CANONICAL_EVIDENCE_STARTED=true
VERDICT=FAIL CODE=NO_CURRENT_FOUNDER_PRINCIPAL_SESSION
CANONICAL_EVIDENCE_FINISHED=true
PROCEDURE_EXIT_CODE=2
```

The procedure had proved the preceding identity-chain conditions but failed
closed because it found no current productive session for the validated
Founder Principal.

### 7.3 Second authorized canonical execution

After a login that appeared successful in the browser, a second separately
authorized invocation returned the same controlled failure:

```ini
CANONICAL_EVIDENCE_STARTED=true
VERDICT=FAIL CODE=NO_CURRENT_FOUNDER_PRINCIPAL_SESSION
CANONICAL_EVIDENCE_FINISHED=true
PROCEDURE_EXIT_CODE=2
```

That authorized execution was consumed and was not retried under the same
authorization. A later final execution occurred only after separate
Architecture Authority authorization and a newly confirmed OIDC session.

The browser UI state alone was not treated as proof of a current
`productive_session`.

### 7.4 Aggregate session diagnostic

The separately authorized aggregate diagnostic had this SHA-256:

`CE89B4926126B1242D03742C6DC85273E0ABB85A9ED926BD1816291A9692D978`

It ran read-only and completed with `VERDICT=PASS` and
`PROCEDURE_EXIT_CODE=0`. Its sanitized aggregate result established:

- exactly one canonical Founder Principal chain;
- six historical sessions, all belonging to that Founder Principal;
- zero sessions belonging to other Principals in the canonical Organization;
- three sessions stored with active status, two with expired status, and one
  with revoked status;
- all six beyond both idle and absolute expiry at diagnostic time;
- zero current sessions;
- all six aligned with the canonical Membership and Organization;
- two created within the prior 24 hours and zero within the prior 8 hours; and
- transaction read-only enforcement and orderly cleanup.

The diagnostic distinguished session expiration from identity or tenant
misbinding. A stored active status did not make an already time-expired session
current.

### 7.5 Fresh OIDC authentication

The Architecture Authority accepted the aggregate result and authorized one
normal, fresh productive OIDC authentication by the same user. A full reload
then produced a newly successful session response. No Founder Bootstrap,
identity, Membership, role, permission, Organization, configuration, or manual
data repair was authorized or performed as part of that act.

### 7.6 Final canonical execution

Within the renewed authorized window, the unchanged canonical original
procedure completed with the following sanitized result:

```ini
CANONICAL_EVIDENCE_STARTED=true
VERDICT=PASS
TRANSACTION_READ_ONLY=true
CANONICAL_ORGANIZATION_COUNT=1
CANONICAL_ORGANIZATION_ACTIVE=true
CANONICAL_ORGANIZATION_ID=6c2bbf37-87d1-4315-8e67-85e9957c9aa7
CANONICAL_ORGANIZATION_DISPLAY_NAME=Yarvis en NetPay
CANONICAL_ORGANIZATION_LEGAL_NAME=GMDHO
CANONICAL_ORGANIZATION_TYPE=organization
HISTORICAL_ORGANIZATION_EXISTS=false
FOUNDER_PRINCIPAL_COUNT=1
FOUNDER_PRINCIPAL_ID=<verified-opaque-principal-uuid>
FOUNDER_PRINCIPAL_ACTIVE=true
FOUNDER_PERSON_ACTIVE=true
ACTIVE_BINDING_COUNT=1
BINDING_ISSUER_MATCH=true
BINDING_SUBJECT_PRESENT=true
BINDING_PROVENANCE_VALID=true
FOUNDER_MEMBERSHIP_COUNT=1
FOUNDER_MEMBERSHIP_ID=<verified-opaque-membership-uuid>
FOUNDER_MEMBERSHIP_ACTIVE=true
FOUNDER_MEMBERSHIP_REVOKED=false
FOUNDER_ROLE=netpay_operations_operator
FOUNDER_PERMISSIONS=netpay.inbox.manage,netpay.inbox.read,netpay.master.manage,netpay.master.read
FOUNDER_PRINCIPAL_CURRENT_SESSION_COUNT=1
SESSION_CHAIN_CONSISTENT=true
HANDOFF_CONSUMED=true
BOOTSTRAP_CLOSED=true
BOOTSTRAP_RUNTIME_DISABLED=true
AMBIGUITY_COUNT=0
CANONICAL_EVIDENCE_FINISHED=true
PROCEDURE_EXIT_CODE=0
```

The opaque placeholders attest that UUID-shaped values were verified without
publishing the productive Principal or Membership identifiers.

## 8. Requirement-to-evidence matrices

### 8.1 Amendment 018 §3.2

| §3.2 requirement | Evidence | Result |
| --- | --- | --- |
| Exact active Organization row | Final canonical execution found exactly one row for the ratified UUID and reported it active. | PASS |
| Canonical UUID and display name | Final output reported `6c2bbf37-87d1-4315-8e67-85e9957c9aa7` and `Yarvis en NetPay`. | PASS |
| Whether the historical Organization exists | Final output reported `HISTORICAL_ORGANIZATION_EXISTS=false` for the historical UUID governed by Amendment 018. | PASS |
| Relationship between current and historical values | The current canonical row exists exactly once and the historical UUID has zero rows; there are not two records requiring alias, rename, or supersession reconciliation. | PASS |
| Active Membership used by the intended human actor | Exactly one active, non-revoked Membership linked the verified Founder Principal to the canonical Organization; its UUID is withheld. | PASS |
| Absence of Organization ambiguity for the intended operation | Exact Organization count was one, historical count was zero, the Membership chain was consistent, and `AMBIGUITY_COUNT=0`. | PASS |

### 8.2 Amendment 018 §8.2

| §8.2 requirement | Evidence | Result |
| --- | --- | --- |
| Exact productive Principal | The procedure resolved exactly one active Founder Principal through the canonical enrollment and binding chain; its UUID is represented by `<verified-opaque-principal-uuid>`. | PASS |
| Exact productive Membership | The procedure resolved exactly one active, non-revoked Membership for that Principal and canonical Organization; its UUID is represented by `<verified-opaque-membership-uuid>`. | PASS |
| Exact productive Organization | Exactly one active Organization matched the ratified UUID, approved display name, legal identity, and Organization type. | PASS |
| Active Person backing the Principal | `FOUNDER_PERSON_ACTIVE=true`. | PASS |
| Active, unique Identity Binding | `ACTIVE_BINDING_COUNT=1`; issuer match, normalized-subject presence, and provenance validation all passed. | PASS |
| No conflicting identity ambiguity | No conflicting active binding existed for the Principal and `AMBIGUITY_COUNT=0` across issuer-plus-normalized-subject identity. | PASS |
| Current productive session on the same chain | `FOUNDER_PRINCIPAL_CURRENT_SESSION_COUNT=1` and `SESSION_CHAIN_CONSISTENT=true`. | PASS |
| Founder handoff and bootstrap closure | `HANDOFF_CONSUMED=true`, `BOOTSTRAP_CLOSED=true`, and `BOOTSTRAP_RUNTIME_DISABLED=true`. | PASS |

## 9. Provisional conclusion

The assembled material evidence is **PASS** for the requirements exclusively
within §3.2 and §8.2 of Amendment 018.

That conclusion remains pending express Architecture Authority acceptance. It
creates no downstream authority while this document remains a draft with an
empty acceptance block.

## 10. Attribution limitation

The final procedure proves that one productive session was current for the
verified Founder Principal, canonical Membership, and canonical Organization
at procedure time. It does not cryptographically correlate that database row
to a particular browser tab, cookie, token, or browser process because no such
credential or identifier was transferred to or emitted by the procedure.

## 11. Effect on Amendment 018 §12.2

This evidence does **not** declare §12.2 completely satisfied. It records only
that the canonical read-only Organization, Principal, and Membership evidence
prerequisite in §12.2 item 2 has been materially demonstrated, pending express
Architecture Authority acceptance of this evidence document.

Items 3 through 9 of §12.2 remain unsatisfied unless and until their own
separately governed evidence and authority exist. No synthetic evidence waives
or satisfies them.

## 12. Downstream gates remain closed

Amendment 018 §8.3, Contract and role allocation, remains closed. All later
productive gates remain closed, including privacy and retention, secrets,
productive OAuth topology, Google project and consent, real connector
implementation, worker or scheduler, real pilot, GO/NO-GO, and deployment.

The next productive gate in sequence is §8.3, but this draft neither opens nor
authorizes it.

## 13. Prohibitions and non-effects

This evidence document does not:

- assign or modify a contract;
- create or change a role or permission;
- create or change a Person, Principal, Identity Binding, Membership, or
  Organization;
- authorize productive configuration or persistence;
- authorize implementation, models, migrations, routes, workers, or
  scheduling;
- authorize secrets, Google resources, OAuth, Gmail, mailbox access, or
  synchronization;
- authorize deployment or a real pilot;
- alter the synthetic/productive gate separation; or
- grant authority to any downstream action by implication.

## Future Architecture Authority Acceptance

- Authority: **Guillermo de Hoyos, Architecture Authority**
- Decision date: **2026-09-07**
- Accepted evidence-document Draft SHA-256: **`3029A7F66419655661FB77049FEB4449DA28E127DD627138FC2E3780770721A4`**
- Accepted scope: **Amendment 018 §3.2 and §8.2 only**
- Exceptions: **None**
- Downstream authority: **None**

This acceptance declares Amendment 018 §3.2 and §8.2 satisfied. It satisfies
only the Canonical Identity prerequisite referenced by §12.2; it does not
declare §12.2 complete, open §8.3 or any later productive gate, or grant
downstream authority.
