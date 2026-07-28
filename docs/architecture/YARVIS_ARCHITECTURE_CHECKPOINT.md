# Yarvis Architecture Checkpoint

**Checkpoint:** AC-001B
**Baseline:** `63740d8` / `ws006a-process-domain-complete`
**Status:** Evidence-based implementation checkpoint; it does not ratify new architecture.
**Purpose:** Record what exists in the repository, what remains partial or planned, and the technical debt that must shape subsequent work.

## Scope and Reading Rule

This is an As-Is checkpoint, not an architectural amendment. The Constitution and ratified artifacts remain authoritative. Where repository evidence and older operational documentation differ, this checkpoint records the implementation evidence without silently changing architectural authority.

<details>
<summary><strong>Executive state</strong></summary>

Yarvis currently operates as a modular-monolith API with a React/Vite frontend and PostgreSQL persistence. The mature operational path is deterministic intake, operational-context association, rebuildable Mission Inbox projection, transactional Mission Work, and its append-only Work Timeline. WS-006A adds generic, organization-scoped Process Definitions with versioned immutable publication, but not a runtime for process instances.

</details>

<details>
<summary><strong>Implemented capabilities</strong></summary>

- FastAPI composition, typed settings, PostgreSQL 16, SQLAlchemy, Alembic, Unit of Work, module/contract registries, and a synchronous Dispatcher foundation.
- Organizations, people, cases, checklists, evidence, observations, controlled data intake, NetPay operations, and store/recovery views.
- Deterministic inbound intake with tenant-bound idempotency and trace events.
- Organization → Site → Project → optional ConnectorMapping association for deterministic Intake.
- Mission Inbox as a rebuildable tenant-scoped projection over `DomainEvent`.
- Mission Work as the transactional source of truth, with stable source identity and a dedicated append-only Timeline.
- Generic Process Definition drafts, stages, transitions, validation, publication, retirement, and version cloning.
- Development Workspace as an authenticated, read-only repository corpus surface.

</details>

<details>
<summary><strong>Partial, foundational, planned, and exploratory capabilities</strong></summary>

| Classification | Repository evidence |
| --- | --- |
| **Partial** | Observation/resolution, NetPay intake, data intake, operational policies, store intelligence, and legacy frontend surfaces exist but do not yet form one governed end-to-end operating model. |
| **Foundation** | Dispatcher, handler registry, worker/scheduler settings, generic events, module registry, and contract registry exist; handlers, worker runtime, scheduler runtime, query/event/notification dispatch and production authority are not implemented. |
| **Planned** | Process instances, automation, decision intelligence, execution authorization, knowledge lifecycle runtime, external integrations, and Process frontend administration. |
| **Exploratory** | Energy Fotónica operational domain, AI-assisted intelligence, and external system connectors. No specialized implementation is present. |

</details>

<details>
<summary><strong>Known technical debt</strong></summary>

1. `DomainEvent` is append-only by application convention, not by a database-level update/delete guard; `MissionWorkEvent` has such a guard.
2. `tests/test_workspace_api.py::test_workspace_uses_the_configured_container_corpus` has a historical sprint expectation that conflicts with the later Workspace corpus.
3. Process contracts and Process services exist, but `canonical_modules.py` does not yet declare a Process canonical module.
4. Newer capabilities use application services and Unit of Work; several legacy routes still own persistence and event recording directly.
5. The authentication provider is deterministic and restricted to `local` and `test` environments.
6. Dispatcher is composed with an empty handler set; worker and scheduler are settings only, with no runtime service in Compose.
7. The frontend combines governed Mission Work and Workspace surfaces with older pages that use a simpler API client.
8. `CURRENT_STATE.md`, `CURRENT_SPRINT.md`, and portions of `README.md` were stale before this checkpoint and are updated only to the extent documented here.

</details>

## Evidence Index

## Companion Views

- [As-Is Architecture](YARVIS_AS_IS_ARCHITECTURE.md)
- [Target Architecture](YARVIS_TARGET_ARCHITECTURE.md)
- [Roadmap and Technical Debt](YARVIS_ROADMAP_AND_TECHNICAL_DEBT.md)

- Application composition: `apps/api/src/yarvis_api/bootstrap.py`
- Persistence and migration lineage: `apps/api/src/yarvis_api/persistence/`, `apps/api/migrations/versions/`
- Mission Inbox and Work: `apps/api/src/yarvis_api/services/mission_inbox.py`, `services/mission_work.py`
- Process Domain: `models/process.py`, `services/process.py`, `api/routes/process.py`
- Frontend: `apps/web/src/App.tsx`, `components/mission-work/`, `workspace-shell/`
- Engineering evidence: `apps/api/tests/`, `docs/engineering/WS-003_*` through `WS-006A_*`

## Next Allowed Architectural Step

WS-006B should begin as a Process Runtime design review. It must define Process Instance ownership, immutable reference to a published Process Definition version, stage-transition authority, association to Mission Work, and event semantics before runtime implementation begins.
