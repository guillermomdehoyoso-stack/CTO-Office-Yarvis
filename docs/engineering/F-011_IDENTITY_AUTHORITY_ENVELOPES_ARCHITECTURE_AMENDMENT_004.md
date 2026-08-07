# F-011 Identity and Authority Envelopes Architecture Amendment 004

## Status

**RATIFIED — F COMMAND/EVENT CONTRACTS — IMPLEMENTATION NOT AUTHORIZED**

**Date:** 2026-08-06
**Authority:** Guillermo de Hoyos, Architecture Authority

## 1. Scope

This Amendment ratifies only the remaining F contract and durable-receipt design
for existing Radar commands. It preserves E/F tenancy under Amendment 003. It
does not authorize implementation, migration, backfill, cutover, final
constraints, header removal or new Radar capability.

## 2. Uniform Command Receipt

Use one generic durable `radar_command_receipts` record, transactionally
co-located with mutation, RadarActivity and DomainEvent. Required fields are:
`command_id UUID`, `organization_id`, `command_type`, `contract_version`,
`idempotency_key`, `request_fingerprint`, `actor_principal_id`,
`correlation_id`, optional input `causation_id`, result status/body reference,
and timestamps. Uniqueness is `(organization_id, command_type, idempotency_key)`.
Retention is deferred to Data Governance; no automatic purge is authorized.

Every command requires `Idempotency-Key`. The fingerprint is SHA-256 over
contract version, canonical target when applicable and normalized functional
payload, excluding headers and client authority fields. Authority resolves
before receipt lookup. Equal replay returns original status and semantically
identical body/metadata without mutation, activity or event. Different
fingerprint returns `409` without side effects. Keys may repeat across
Organizations or command types.

## 3. Correlation, Causation and Actor

Each accepted command has server `command_id`; valid supplied correlation
metadata is preserved, otherwise generated. Receipt and event retain it. A
direct event has `causation_id = command_id`; replay retains the original chain.
Rejected commands emit neither event nor activity. `actor_principal_id` is the
durable actor. RadarActivity is an operational projection, not DomainEvent.
`received_by` is functional data only; display projection is non-authoritative
and deferred.

## 4. Command and Event Profiles 1.0.0

All profiles obtain Organization and Principal from the Envelope, conceal
foreign targets as `404`, and atomically persist mutation, receipt, activity
and event.

| Command | Endpoint | Aggregate / permission | Event type | Safe payload beyond common envelope |
| --- | --- | --- | --- | --- |
| CreateMerchant | `POST /radar/merchants` | RadarMerchant/new ID; `radar.merchant.create` | `radar.merchant_created` | `command_id` |
| CreateRequest | `POST /radar/requests` | RadarRequest/new ID; `radar.request.create` | `radar.request_created` | `command_id`, merchant ID, classification |
| UpdateChecklist | `PATCH /radar/requests/{id}/checklist/{item}` | RadarRequest/request ID; `radar.checklist.update` | `radar.request_checklist_updated` | `command_id`, item ID, received |
| SetNextAction | `PATCH /radar/requests/{id}/next-action` | RadarRequest/request ID; `radar.request.update` | `radar.request_next_action_set` | `command_id`, changed-field names |
| AddNote | `POST /radar/requests/{id}/notes` | RadarRequest/request ID; `radar.note.create` | `radar.request_note_added` | `command_id`; never note text |
| CloseRequest | `POST /radar/requests/{id}/close` | RadarRequest/request ID; `radar.request.close` | `radar.request_closed` | `command_id`, justified flag |
| ReopenRequest | `POST /radar/requests/{id}/reopen` | RadarRequest/request ID; `radar.request.reopen` | `radar.request_reopened` | `command_id` |

Each event uses version `1.0.0` and the DomainEvent envelope: event ID, type,
occurred time, aggregate type/ID, organization, correlation and causation. Its
payload contains `event_version`, `actor_principal_id` and only listed safe
fields. Radar events are separate from `IC-GOVERNANCE-EVT-001 AuthorityChanged`,
which remains Membership-only.

## 5. Selector and Acceptance

`X-Yarvis-Organization-Selector` is the sole temporary Membership selector. It
is optional only with one active Membership; multiple memberships without it
conflict, and nonexistent/foreign/inactive/revoked selection fails closed.
`X-Yarvis-Workspace` is compatibility data only; its physical removal belongs
to H. Required evidence for every command: first success, equal replay, no
duplicate activity/event, incompatible `409`, organization-scoped key, foreign
`404`, revocation before replay, forged headers ignored, correlation/causation,
atomic rollback, canonical actor and no event for rejection. The 62 excluded
historical records remain intact and invisible.

G retains backfill/reconciliation/NOT NULL/final constraints; H retains legacy
header removal; I retains integral regression and factual closure. F remains
incomplete pending a separate implementation mandate.
