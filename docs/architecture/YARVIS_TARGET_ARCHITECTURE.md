# Yarvis Target Architecture

**Status:** Derived target view from existing architecture and roadmap; no new authority is created here.

## Target Operating Loop

```mermaid
flowchart LR
    Source["External source"] --> Observation["Observation and evidence"]
    Observation --> Knowledge["Governed knowledge"]
    Knowledge --> Reasoning["Situation and decision intelligence"]
    Reasoning --> Decision["Authorized decision"]
    Decision --> Plan["Execution plan and authorization"]
    Plan --> Execution["Execution and eligible automation"]
    Execution --> Evidence["Execution evidence and outcome"]
    Evidence --> Observation
```

## Target Component Boundaries

```mermaid
flowchart TB
    subgraph Memory["Operating Memory"]
        OE["Observation and Evidence"]
        Identity["Identity and Governance"]
        Knowledge["Knowledge Lifecycle"]
    end
    subgraph Reasoning["Operating Reasoning"]
        DI["Decision Intelligence"]
    end
    subgraph Execution["Operating Execution"]
        Process["Process Definition and Process Instance"]
        Work["Mission Work"]
        Automation["Automation Engine"]
        MC["Mission Control"]
    end
    OE --> Identity --> Knowledge --> DI --> Process --> Work
    DI --> Automation
    Work --> MC
    Automation --> MC
```

## Process Target

The existing Process Definition aggregate is a versioned template. The target runtime must introduce a separate Process Instance aggregate that references one published definition version. It must not mutate published templates, convert a Mission Inbox projection into transactional truth, or make Mission Work the owner of process semantics.

## Non-Goals of this Target View

- It does not select workflow engines, queues, vendors, BPMN, deployment topology, or AI models.
- It does not authorize implementation of Process Runtime, Automation, or Knowledge runtime.
- It does not collapse NetPay, Energy Fotónica, or future domains into one domain model.
