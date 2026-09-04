# Yarvis Roadmap and Technical Debt

**Baseline:** `9751d45` / `ws006f-operational-workspace-ui-complete`
**Status:** Evidence-based planning boundary; it does not authorize implementation.

## Implemented Sequence

```mermaid
flowchart LR
    WS006A["WS-006A Process Definition"] --> WS006C["WS-006C Process Runtime"]
    WS006C --> WS006D["WS-006D Work/Process association"]
    OV001["OV-001 Economics design"] --> OV002["OV-002 Economics foundation"]
    WS006D --> WS006E["WS-006E Workspace read model"]
    OV002 --> WS006E
    WS006E --> WS006F["WS-006F Workspace UI"]
    WS006F --> OE001["OE-001 Operational Execution architecture"]
    OE001 --> WS007A["WS-007A Task Core"]
```

## Approved Future Boundaries

1. **Foundation completion:** production authority, dispatch handlers, worker and
   scheduler runtime, and conformance evidence before autonomous consumers.
2. **Operational Economics deferred scope:** explicit roll-up membership, metric
   snapshots, then separately ratified FX/adapters if required. No implicit relation
   may substitute for those designs.
3. **Operational Execution:** OE-001 accepts the neutral Task context. WS-007A must
   allocate its accepted command contracts in the canonical catalog before public
   endpoint exposure, then implement the Task Core without expanding scope.
4. **Work extensions:** Waiting, Checklist association, SLA, and Documents each need
   a separately owned aggregate/reference design and contracts; they must not be
   smuggled into the initial Task lifecycle.
5. **Operator surfaces:** Process administration and future workspace sections may
   consume owner queries; they may not embed lifecycle or economics rules.
   [UX-001 Experience Architecture](YARVIS_EXPERIENCE_ARCHITECTURE.md) is a
   non-ratified product-experience proposal for the future Home → Space → Area →
   Structured Workspace hierarchy; it creates no implementation authorization.
6. **Automation and AI:** only after authority, evidence, event dispatch, and
   execution controls are operational.
7. **Data intake and documents:** DI-001 is ratified for DI-002 only through
   [ADR-001](../decisions/ADR-001_RATIFY_DI001_DOCUMENT_ARCHITECTURE.md).
   DI-003 through DI-006 and connector work remain separately scoped; no connector
   may create authoritative business state without an owner contract.

## Technical Debt Register

| ID | Debt | Boundary | Priority |
| --- | --- | --- | --- |
| TD-001 | Generic `DomainEvent` remains append-only by convention rather than a database update/delete guard. | Event infrastructure | High |
| TD-002 | Process is not reconciled with `canonical_modules.py`. | Module governance | High |
| TD-003 | Legacy route-owned persistence coexists with service/Unit-of-Work ownership. | Application boundary conformance | High |
| TD-004 | Superseded — see [ADR-015](../decisions/ADR-015_PRODUCTION_SECRETS_IAC_OWNERSHIP.md): production OIDC login and founder bootstrap are operational; the remaining concern is configuration governance. | Production governance | Closed |
| TD-005 | Dispatcher mechanism proven with the zero-persistence `IC-PLATFORM-CMD-DISPATCH-PROBE` handler; zero business handlers are wired. Worker/scheduler runtime remains absent. | Foundation execution | High |
| TD-006 | The frontend contains governed Mission Work/Workspace and older simple API surfaces. | UI boundary consistency | Medium |
| TD-007 | Frontend production build can be blocked by an `EPERM` lock on generated `dist/assets`. | Local build environment | Medium |
| TD-008 | Development current-state/sprint documents required AC-002 reconciliation after WS-006E/F. | Development Operating System | Medium |
| TD-009 | Repository/Session-injection design for real Command handlers remains unresolved and unauthorized; existing service-owned transactions cannot be wired through Dispatch until separately ratified. | Dispatch handler composition | High |

## Superseded Planning Statements

The earlier sequence that treated Process Runtime, Mission Work/Process association,
Operational Economics foundation, and Operational Workspace as planned is complete.
Those statements remain historical evidence only; AC-002 is the current navigation
point.

TD-004 is superseded by the productive execution of the founder-bootstrap
ceremony on 2026-09-03/04: live OIDC login, `create-first-organization`, and
`enroll` completed against the production environment. The remaining gap is
configuration-governance drift in production connection strings and deployment
templates, governed by [ADR-015](../decisions/ADR-015_PRODUCTION_SECRETS_IAC_OWNERSHIP.md),
not an absence of production authentication capability.
