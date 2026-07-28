# Yarvis As-Is Architecture

**Baseline:** `63740d8` / `ws006a-process-domain-complete`
**Status:** Repository-evidence view; not a replacement for ratified architecture.

## Context

```mermaid
flowchart LR
    Source["Deterministic inbound / uploads"] --> Intake["Intake and evidence"]
    Intake --> Events["DomainEvent"]
    Intake --> Context["Operational context: Organization, Site, Project"]
    Context --> Events
    Events --> Inbox["Mission Inbox: rebuildable projection"]
    Inbox --> Work["Mission Work: transactional aggregate"]
    Work --> Timeline["Mission Work Timeline: append-only evidence"]
    Work --> Web["Mission Work frontend"]
    Process["Process Definition: versioned template"]
```

`ProcessDefinition` is intentionally disconnected from runtime work: no Process Instance exists at this baseline.

## Deployment

```mermaid
flowchart TB
    Browser["Browser"] --> Web["React/Vite web :5173"]
    Browser --> API["FastAPI API :8000"]
    Web --> API
    API --> DB[("PostgreSQL 16")]
    API --> Data["/data document storage"]
    API --> Corpus["/workspace-repository: read-only corpus"]
    Corpus --> Docs["AGENTS.md, development and engineering docs"]
```

## Components

```mermaid
flowchart TB
    Bootstrap["bootstrap.py composition root"] --> Auth["Deterministic authentication"]
    Bootstrap --> Persistence["PersistenceRuntime and UnitOfWork"]
    Bootstrap --> Contracts["Module, Contract, Handler registries"]
    Bootstrap --> Routes["FastAPI routes"]
    Routes --> Services["Application services: newer capabilities"]
    Routes --> Legacy["Legacy direct route persistence"]
    Services --> Models["SQLAlchemy models"]
    Services --> Events["DomainEvent"]
    Services --> WorkEvents["MissionWorkEvent"]
    Models --> DB[("PostgreSQL")]
```

## End-to-End Operational Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant I as Deterministic Intake
    participant E as DomainEvent
    participant P as Mission Inbox Projection
    participant W as Mission Work
    participant T as Work Timeline
    C->>I: POST /intake/deterministic
    I->>E: intake.received
    C->>P: project pending events
    P->>E: read ordered events
    P->>P: rebuildable Inbox item
    C->>W: create from Inbox item
    W->>E: work lifecycle event
    W->>T: append ordered Work event
    C->>W: assign, status, priority, comment
    W->>T: append timeline evidence
```

## Transactional Ownership versus Projections

```mermaid
flowchart LR
    Intake["IntakeItem: transactional"] --> DE["DomainEvent"]
    Context["Context association: transactional, immutable"] --> DE
    DE --> Inbox["MissionInboxItem: rebuildable projection"]
    Inbox --> Work["MissionWorkItem: transactional source of truth"]
    Work --> WorkEvent["MissionWorkEvent: append-only timeline"]
    Definition["ProcessDefinition: transactional versioned template"]
    style Inbox stroke-dasharray: 5 5
```

## Current Boundary Notes

- Workspace routes require `x-yarvis-workspace-token` and expose only an allowlisted corpus mounted read-only in Docker.
- Mission Work reads and writes require distinct authority scopes and conceal cross-organization resources as `404`.
- Process Definition reads require `process.definition.read`; lifecycle and draft changes require `process.definition.manage`.
- The generic `DomainEvent` stream supports projections but lacks a database append-only trigger.
