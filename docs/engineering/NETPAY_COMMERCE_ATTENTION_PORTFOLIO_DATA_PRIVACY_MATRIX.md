# Netpay Commerce Attention Portfolio — Data, Privacy and Assurance Matrix

## Status

**RATIFIED — P0/P1 DATA AND PRIVACY BASELINE**

**Authority:** [Amendment 024](IMPLEMENTATION_ROADMAP_AMENDMENT_024.md) and [IG-011](IG-011_NETPAY_COMMERCE_ATTENTION_PORTFOLIO_P0_P1_AUTHORIZATION.md)

| Data | Source | PII/profile | P0/P1 treatment | Required permission |
| --- | --- | --- | --- | --- |
| Organization | Backend authority envelope | No; C | Resolved server-side; never selected by caller | `netpay.portfolio.read` |
| Commerce label | NetpayClient | Possibly; C | `display_name`, source-labelled | `netpay.portfolio.read` |
| Legal name | NetpayCompany | Possibly; B/C | `legal_name`, distinct from commerce label | `netpay.portfolio.read` |
| RFC | NetpayCompany | Sensitive; B/C | Masked in list; full only in detail; never full in URL/log/reason/metric | General masked; sensitive full |
| Branch | NetpayBranch | Address/contact may be PII; B/C | Safe name and canonical ID | `netpay.portfolio.read` |
| Store ID | active NetpayStoreReference | Controlled identifier; C | Store ID only; never MID | `netpay.portfolio.read` |
| MID | No authorized source | Controlled identifier; C | `No disponible` | None |
| Registered contact | Client/Company/Branch fields | Sensitive; B/C | Presence/redacted list; source/scope/verification/freshness; full detail only; no inferred role/action | General minimized; sensitive full |
| Case availability | NetpayServiceCase | Possibly sensitive; B/C | Neutral authorized aggregate only | `netpay.portfolio.read` |
| Linked pre-Master | Candidate/CommercialIntakeItem/Dossier | Possibly sensitive; B/C | Neutral authorized availability after exact link | `netpay.portfolio.read` |
| Unlinked pre-Master | Candidate/CommercialIntakeItem/Dossier | Possibly sensitive; B/C | Separate safe queue; no Gmail/attachment content | `netpay.portfolio.reconciliation.read` |
| Profitability/no-use | D1 facts | Business-sensitive; C | **No incorporado en P0/P1** | Closed until P2 |
| Terminals | No authorized canonical source | Identifier/PII risk; B/C | `Sin fuente canónica autorizada` | Closed |
| Attention color | Future evaluator | Derived; C/D | Excluded | Closed until P3 |

## Existing permission inventory and decision

| Existing permission | Resource/action | Current routes | Roles | Exact for Portfolio? | Excess access |
| --- | --- | --- | --- | --- | --- |
| `netpay.master.read` | Master/read | `GET /netpay/master`, `GET /netpay/master/branches/{id}` | `netpay_master_viewer`, `netpay_master_operator`, `netpay_operations_operator` | No: current Master schemas include unminimized legal/contact fields and do not distinguish sensitive detail | Existing Master detail beyond minimized Portfolio |
| `netpay.master.manage` | Master/manage | Master Client/Company/Branch/StoreReference mutations | `netpay_master_operator`, `netpay_operations_operator` | No: mutation is unnecessary | All Master writes |
| `netpay.inbox.read` | Inbox/read | Inbox/case/contact reads; Gmail source/candidate/follow-up/qualification/intake/dossier reads; operational-data reads | `netpay_inbox_viewer`, `netpay_inbox_operator`, `netpay_operations_operator` | No: broader than safe reconciliation queue | Gmail, Inbox and operational-data reads unrelated to queue |
| `netpay.inbox.manage` | Inbox/manage | Inbox, Gmail candidate, dossier and operational-data mutations | `netpay_inbox_operator`, `netpay_operations_operator` | No: mutation is unnecessary | All covered writes |

No current permission exactly separates full RFC/phone/email. Therefore no
existing scope is reused as the new Portfolio boundary.

## Future permissions authorized by IG-011

| Permission | Enabled | Excluded | Isolation and negative tests |
| --- | --- | --- | --- |
| `netpay.portfolio.read` | Minimized Master hierarchy, masked RFC, redacted contact presence, permitted neutral badges/counts | Full PII, unlinked detail, D1, colors, terminals, mutations | Backend Organization; missing/wrong scope, forged authority, cross-tenant IDs and count leakage |
| `netpay.portfolio.sensitive.read` | Full RFC/phone/email in explicit QRY-024 fields | Queue, communications, export, unrelated Inbox/Gmail data | All general tests plus omission/redaction and sensitive audit behavior |
| `netpay.portfolio.reconciliation.read` | Safe unlinked Candidate/CommercialIntakeItem/Dossier IDs, labels, state, reason, source, freshness | Gmail content, attachments, full contacts, promotion/merge/mutation | All general tests plus queue/count concealment without scope |

General Portfolio read is initially eligible for Master viewer/operator and
operations operator roles. Sensitive and reconciliation permissions are
initially eligible only for operations operator. The future role-map edit and
tests create the grant; this document alone changes no runtime permission.

## Privacy and assurance rules

- Return only fields necessary for the operator function.
- Never log, export or place full RFC, phone or email in URLs, reasons or
  metrics.
- Do not infer a contact role or use inferred data to contact anyone.
- Do not overwrite contradictions; expose controlled conflict and provenance.
- Filter rows and aggregates by permissions before calculating counts.
- Provide no email, WhatsApp, SMS, call, copy, export or mutation action.
- Record source level, available verification, last update and freshness.
- Validate positive/negative authorization, least disclosure, cross-tenant
  concealment, schema redaction and no side effects.

P2–P5, D1 use, colors, expanded contacts/follow-up, terminals, export,
communications and persistent preferences remain outside this baseline.
