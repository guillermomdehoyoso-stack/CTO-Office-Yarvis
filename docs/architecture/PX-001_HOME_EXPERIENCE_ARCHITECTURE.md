# PX-001 â€” YARVIS Home Experience Architecture
**Status:** Product-experience proposal; documentation only; not implementation authority
**Authority:** Derived from the Yarvis Constitution and constrained by accepted architecture and experience foundations
**Purpose:** Define the experience of arriving in YARVIS before an operator enters a particular Operational Space, Area, or Structured Workspace.

> **YARVIS Home is an operational briefing generated from living systems.**
>
> It gives an authorized operator enough explainable, current operational context to choose where to begin. It does not become the system of record, a priority engine, or a substitute for structured work.

## 1. Scope and Governing Boundaries

PX-001 defines an experience and information hierarchy only. It does not redefine the architecture, domain ownership, interaction contracts, or the hierarchy in [UX-001](YARVIS_EXPERIENCE_ARCHITECTURE.md), the living-metaphor discovery in [UX-003](LIVING_OPERATIONAL_ECOSYSTEM.md), or the visual semantics in [UX-004](OPERATIONAL_VISUAL_SEMANTICS.md).

Home consumes governed, visible projections. It does not create canonical facts, authority, Decisions, Tasks, alerts, priority policy, Space ownership, or an Operational Space/Area domain model. It remains subject to the projection, provenance, uncertainty, freshness, and intervention boundaries of [Mission Control](MISSION_CONTROL_ARCHITECTURE.md).

The established hierarchy remains:

```text
YARVIS Home
  â†’ Operational Space
    â†’ Operational Area
      â†’ Structured Workspace
        â†’ Resource detail
```

The bubble/cell metaphor is limited to Home and the Space/Area orientation levels. It stops when the operator enters the Structured Workspace, where panels, lists, tables, timelines, filters, and resource details take over.

## 2. Home Philosophy

Home is the operator's operational briefing before work begins. Its desired three-second outcome is confident orientation, not exhaustive understanding:

- What needs my attention?
- Where should I begin?
- What changed recently?
- Which Operational Space needs me?
- What can safely wait?

The intended feeling is: *â€œI understand today's operational landscape.â€* The operator should not need to search for work, reconstruct context from menus, or open several reports before selecting a first destination.

Home is not a dashboard, landing page, menu, report, portal, or chat surface. A dashboard aggregates metrics for observation; Home gives an explainable basis for choosing an operational destination. A menu exposes software structure; Home exposes operational reality. A report explains a period; Home gives a bounded present-time briefing.

## 3. Complete Arrival Sequence

| Transition | Operator experience | Cognitive purpose | Boundary |
| --- | --- | --- | --- |
| Application opens | YARVIS presence establishes an operational orientation surface rather than a generic application shell. | Establish calm attention and a recognizable beginning. | Presence is not logo-only treatment or assistant chat. |
| YARVIS presence â†’ global briefing | A concise visible-scope summary names material attention and meaningful recent change. | Answer â€œwhat deserves review now?â€ without search. | Each material statement needs an explainable source, scope, and freshness. |
| Global briefing â†’ living ecosystem | Labelled Operational Spaces present possible operating universes and explicit state. | Answer â€œwhere should I begin?â€ while preserving alternatives. | Space cells are navigation/projection surfaces, not applications, folders, modules, or automatic bounded contexts. |
| Operator chooses a Space | The selected Space carries forward in the location label and destination context. | Reduce global ambiguity to one operating universe. | Selection does not grant access or change truth. |
| Space â†’ Area | Compact Area choices express a functional view within the selected Space. | Reduce orientation into understandable work intent. | An Area is a UX concept; it is not automatically persisted or a bounded context. |
| Area â†’ Structured Workspace | The spatial metaphor yields to structured panels, lists, tables, timelines, and filters. | Support precise review and governed work with low ambiguity. | The Workspace consumes owner projections; it does not infer lifecycle, authority, or source ownership. |

Each transition reduces abstraction. It must never increase complexity through an unexplained score, mode, menu taxonomy, or visual convention.

## 4. Information Hierarchy

| Candidate element | Home disposition | Reason and constraints |
| --- | --- | --- |
| Global Critical Actions | **Required when visible items exist.** | A transversal, deterministic attention projection with an explainable destination. It coexists with Spaces and never replaces them. |
| Operational Spaces | **Required.** | The primary choice architecture. Each visible Space has an identity label, named state, and structured equivalent. |
| Global operational briefing | **Required, concise.** | A short orientation statement that makes scope, material attention, and recent change understandable; never a hidden composite score. |
| Recent operational change | **Required when qualifying visible change exists.** | Named events/categories, count or timestamp, and destination. Absence does not imply nothing changed outside visible scope. |
| Today's operational summary | **Optional.** | Useful only when it gives actionable orientation, not a decorative KPI strip. |
| Recent activity | **Optional.** | A bounded, explainable summary; detailed chronology belongs in a Space/Area Workspace timeline. |
| Unread operational changes | **Future.** | Requires a per-operator read/acknowledgement model, retention rules, and accessibility semantics; unread never silently means important. |
| Operator greeting | **Optional.** | A small human acknowledgement may establish context, but cannot consume briefing attention or disclose unnecessary personal data. |
| System health | **Future, separately classified.** | Technical and operational health remain distinct; use only with a named, explainable source and routing decision. |

Home reveals enough to orient, not every open item, historical event, or filter. Space, Area, and Workspace progressively reveal the necessary detail.

## 5. What Must Never Appear on Home

| Anti-pattern | Why it is excluded |
| --- | --- |
| Large tables | They demand comparison and scanning before orientation; structured tables belong in the Workspace. |
| Long task lists | They collapse cross-Space awareness into work inventory and blur owner/work semantics. |
| Reports | Period analysis is not an arrival briefing. |
| Configuration | Setup diverts the operator from operational understanding. |
| Charts without a decision or destination | Decorative aggregation adds interpretation burden without helping the operator choose where to go. |
| Dense forms | Data entry is precision work, not arrival orientation. |
| Navigation trees or application menus as the primary surface | They reveal software structure rather than operational landscape and make the operator guess a route. |
| CRUD interfaces | Generic records and management controls conflate orientation with administration. |
| Hidden composite health, energy, or priority scores | They cannot be safely understood, challenged, or traced. |
| Alarm animation or urgency theatre | Flashing, shaking, persistent red pulse, and competing alerts create anxiety and alarm fatigue. |

## 6. YARVIS Presence

YARVIS is a calm operational narrator and briefing coordinator: a recognizable presence that frames the global briefing, explains scope when needed, and helps the operator move from awareness to an operational destination.

It is not merely branding, a static logo, or an assistant chat that demands a prompt. It must not impersonate authority, assert uncertain conclusions as facts, hide provenance, or become visually dominant enough to compete with the Space field and explicit critical attention.

In the MVP, YARVIS is visually central enough to establish orientation, but quieter than a Critical Action and no more prominent than the operator's next clear destination. Its central placement is compositional, not an operational ranking signal. Any generated briefing remains identifiable as generated, traceable to governed inputs, and usable without AI.

## 7. Global Briefing and Critical Actions

The global briefing is a short, bounded answer to what is active, what needs review, what changed, and where the operator can proceed. It may use counts, categories, or sentences, but PX-001 does not prescribe a fixed universal metric set.

Every material briefing claim must disclose or lead to:

- the visible scope to which it applies;
- the named condition or category summarized;
- source/provenance and freshness appropriate to the claim;
- a destination for further structured inspection; and
- material uncertainty, conflict, or missing information.

Critical Actions are transversal projections. They can dominate only when their approved classification indicates prompt human review and the visible scope contains one or more such actions. They remain secondary when no such condition exists or when a local Space/Area marker preserves orientation. They never replace Spaces, create authority, or convert every active task into an emergency.

## 8. Operational Spaces and Discovery

An Operational Space is a living operational system summarized for orientation. It is not an application, folder, module, report category, or automatic domain boundary. Its Home representation may show only explainable OVS/OXL semantics: identity label, named attention state, named badge/count, and bounded recent activity. Size, color, border, breathing, halo, and position may never carry an undisclosed meaning.

Discovery comes from the briefing and labelled Space field, not search, navigation trees, reports, or menu exploration. A Space answers â€œthis is an operating universe I can enterâ€; explicit labels and the structured fallback explain why it may merit attention. The experience must also work as a logical list/grid with the same information and destinations.

When an operator selects a Space, its identity remains visible. When an operator selects an Area, both Space and Area remain visible. Back/Escape removes one level of abstraction at a time, while Home is always available. These interaction rules preserve the hierarchy but do not authorize runtime implementation.

## 9. Emotional and Cognitive Principles

Home should feel calm, confident, aware, controllable, curious, and trustworthy. It reduces cognitive load by answering orientation questions before the operator must formulate a search query or remember a system-specific route.

It rejects urgency theatre, visual overload, alarm fatigue, constant interruption, and decorative motion. Stable Spaces are nearly still; critical attention is explicit in text/badges and never depends only on motion, color, size, or center proximity. Progressive disclosure protects attention: Home orients, Space explains local context, Area narrows purpose, and Workspace supports precise work.

## 10. Relationship to OXL and Architecture

| Concern | Responsibility |
| --- | --- |
| Architecture | Defines truth, ownership, authority, contracts, provenance, and allowed projections. |
| OVS/OXL | Defines deterministic meaning and accessible equivalent of visual signals. |
| PX-001 Home | Defines arrival experience, information hierarchy, and progressive disclosure of those signals. |

PX-001 consumes OXL semantics; it does not redefine them. It does not make position a priority signal, use size for importance or revenue, invent health from animation, create a hidden composite score, or make an Operational Area a persistence or domain-model requirement.

## 11. Success Outcomes

Success is observable in operator behavior and comprehension rather than visual novelty:

- An operator identifies the most material visible priority within seconds.
- An operator enters the appropriate Space without exploring menus or reports.
- The path from Home to relevant structured work requires less unnecessary navigation and context switching.
- Operators can explain why a Space or Critical Action was shown as needing attention.
- The structured fallback produces the same orientation for keyboard, screen reader, reduced-motion, and small-screen use.

Future quantitative measurement requires a separately approved instrumentation design and must respect privacy and authority.

## 12. Evolution Horizons

| Horizon | Permitted direction | Boundary |
| --- | --- | --- |
| MVP | Concise briefing; labelled configured Spaces; explicit Critical Action/recent-change signals; structured equivalent; deterministic navigation into Space, Area, and Workspace. | No dynamic Space model, persisted layout, hidden score, or new owner state. |
| Near-term evolution | Approved Space read model, explainable attention, attributable recent change, richer local context, and reviewed briefing copy. | Each field needs an owner query/projection, visibility rules, freshness, and destination. |
| Long-term evolution | Governed personalization, richer role-aware briefing, identifiable AI-generated narrative, and approved health categories. | Personalization cannot hide mandatory governance items or broaden authority; AI cannot replace accountability. |
| Research only | Attention attraction, expressive motion/depth, cadence-aware personality, and alternate briefing compositions. | Requires prototype evidence, OXL mapping, accessibility review, and human approval. |

## 13. Open Human Decisions Requiring Approval

1. Which initial Operational Spaces are visible to which operator scopes, and what authoritative mapping supplies visibility?
2. What deterministic classification makes an item a Global Critical Action, including ordering, freshness, and empty-state behavior?
3. Which changes belong in the global briefing, and what recency window and event sources apply?
4. Is an operator greeting valuable in the first release, and what privacy/personalization constraints apply?
5. Should YARVIS provide authored briefing copy only, or later provide an identifiable generated summary under evidence/provenance review?
6. What is the approved MVP visual prominence of YARVIS relative to Critical Actions and Space cells?
7. Which OXL MVP signals are enabled on Home: fixed versus bucketed size, recent-activity breathing, transient halo, and attention border/badge treatment?
8. Is the structured fallback a permanent parallel view, and how is it selected or made primary on mobile/reduced-motion contexts?
9. What distinguishes a briefing-worthy operational change from routine activity without creating notification or alarm fatigue?
10. When should technical system health appear separately from operational conditions, and which governed source owns it?

## 14. Validation Record

- Local Markdown links must resolve from this document.
- `git diff --check` must pass.
- This work creates no runtime, frontend, backend, API, schema, route, CSS, SVG, or prototype change.
