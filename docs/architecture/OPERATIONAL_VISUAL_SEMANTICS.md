# Operational Visual Semantics (OVS)

**Status:** UX-004 semantic architecture; governing visual-language proposal pending human approval.
**Scope:** Deterministic meaning for visual behaviors across the accepted UX hierarchy. This is not visual design, animation, React, CSS, SVG, a component library, or an implementation specification.

**Related documents:** [YARVIS Experience Architecture](YARVIS_EXPERIENCE_ARCHITECTURE.md), [Living Operational Ecosystem Discovery](LIVING_OPERATIONAL_ECOSYSTEM.md), and [Mission Control Architecture](MISSION_CONTROL_ARCHITECTURE.md).

## 1. Governing Principle

> Nothing in YARVIS changes its size, color, movement, glow, texture, shape, breathing, or emphasis unless that change corresponds to a visible, deterministic operational fact.

**Architectural invariant.** Trust requires an operator to connect perceived change with an explainable fact. A visual effect without a disclosed source makes the interface seem manipulative, trains users to ignore it, and makes historical/operator reconstruction impossible. OVS therefore treats visual behavior as a projection with source, rule, current value, freshness, and accessible equivalent.

Visual semantics direct awareness; they neither create authority nor replace the source state, a Critical Action, a decision, or an action permission.

## 2. OVS: Operational Experience Language

**Architectural recommendation.** **Operational Experience Language (OXL)** is the semantic grammar used by OVS. It is not a component library, CSS framework, design system, animation system, or domain model. It defines what a visual behavior is allowed to mean before any interface implementation chooses how to render it.

Future OXL artifacts may include an approved semantic registry, source/read-model mapping catalogue, accessibility equivalence specification, per-Space conformance guide, and prototype evaluation record. None is created by UX-004.

## 3. Complete Semantic Dictionary

| Visual property | Operational meaning | Operational source | Deterministic? | Accessible equivalent | Future extensibility |
| --- | --- | --- | --- | --- | --- |
| Size | Operational workload only. | Approved counts of active Tasks, Waiting Items, Pending Decisions, and Pending Reviews. | Yes, once the count scope/time is declared. | Workload label with displayed count/bucket. | Additional explicitly owned work categories; never prestige/revenue. |
| Color | Attention level only. | Deterministic Critical Actions/attention classification. | Yes, after rules are approved. | Named attention label, reason, and count. | More contrast themes, not a second semantic. |
| Breathing | Recent operational activity. | Bounded recent Domain Events, Task changes, or Process transitions. | Yes, with defined time window/event allowlist. | â€œRecent activityâ€ label and timestamp/count. | Different decay windows only through approved policy. |
| Membrane | Operational identity and stable navigational boundary. | Space/Area identity configuration. | Yes. | Text label and semantic control role. | Shape family may vary only without changing meaning. |
| Texture | None in MVP. | No reliable cross-domain source currently. | No. | None; identity remains text/icon. | Research possible domain-character cue, never status. |
| Halo | A recent significant transition. | Approved event allowlist and recency window. | Yes, if transient and bounded. | â€œSignificant change at [time]â€ label. | Event-specific explanation. |
| Internal motion | None initially. | Flow/cadence source not yet defined consistently. | No. | Explicit activity views. | Research only after a governed cadence read model exists. |
| Position | Navigation/layout only. | Layout algorithm and viewport. | Not operational. | Logical DOM/tab order and structured list. | No importance, priority, or hierarchy meaning. |
| Shadow/depth | Visual hierarchy only. | Rendering context, not operations. | Not operational. | None required beyond normal hierarchy. | Must never signal risk/priority/state. |
| Labels | Identity and explicit state. | Space/Area configuration plus approved read models. | Yes. | Labels are themselves the primary equivalent. | Localized text and richer provenance/freshness detail. |
| Badges | Non-zero condition requiring a compact count/category. | Critical Action count, pending review/decision count, or named transient change. | Yes. | Full label and count. | Additional approved count types; absence means zero/not-applicable only when disclosed. |
| Border/emphasis | Repeats attention level; never its own category. | Same source as color. | Yes. | Named attention state and reason. | Theme-specific rendering only. |

## 4. Size: Workload, Not Importance

**Proposed semantic.** Size represents only workload in the declared Space/Area scope: active Tasks, Waiting Items, Pending Decisions, and Pending Reviews. It must never represent importance, revenue, Organization size, prestige, risk, or attention.

| Scaling strategy | Strength | Risk | OVS posture |
| --- | --- | --- | --- |
| Linear | Easy to explain for a small range. | Large ranges dominate the field and imply importance. | Avoid for spatial navigation. |
| Bucketed | Stable, legible, bounded; labels can disclose thresholds. | Threshold edges can look arbitrary. | Recommended MVP candidate. |
| Logarithmic | Compresses large ranges. | Hard for operators to infer without explanation. | Later-only if data range proves buckets inadequate. |

**MVP recommendation.** Use fixed size until a tested workload read model and bounded buckets exist. If enabled, display the bucket and raw count together; zero workload must remain discoverable.

## 5. Color: Attention Level Only

**Proposed semantic.** Color has exactly one operational meaning: **attention level**. It must not simultaneously express risk, urgency, health, domain identity, workload, or recency.

Attention is a projection category sourced from approved Critical Actions/attention rules. It is accompanied by a named label, reason/count, and non-color cue such as border/badge. Operational health remains a separate textual explanation until an owned, deterministic health classification exists.

## 6. Breathing, Halo, and Internal Motion

### Breathing

Breathing represents **recent operational activity**, not urgency, health, workload, or importance. Candidate sources are recent approved Domain Events, Task changes, and Process transitions. The eventual rule must state event types, recency window, decay, source freshness, and whether activity is confirmed or projected.

### Halo

A halo represents one **recent significant transition**. It is transient, expires under a disclosed time rule, and links to its transition explanation. A permanent halo is prohibited because it loses event meaning and becomes decoration.

### Internal motion

Internal motion is distinct from breathing: it would represent operational flow, transaction density, or event cadence. No consistently owned cross-Space source currently exists. **OVS recommendation:** omit it until a governed, explainable cadence/flow read model is available.

## 7. Membrane, Texture, Position, and Shadow

**Membrane.** Shape, thickness, continuity, and stability communicate a Space/Areaâ€™s recognizable boundary only. They must not encode health, risk, priority, or authority. A damaged/broken membrane is prohibited unless a precisely defined operational fact and accessible equivalent justify it; otherwise it implies instability or illness.

**Texture.** Payments, Energy, Trading, Construction, and Healthcare may eventually have distinct visual texture, but that risks inconsistent semantics and accessibility issues. OVS excludes texture from MVP status. Future texture may express domain identity onlyâ€”not condition, attention, or workloadâ€”and must retain a neutral theme equivalent.

**Position.** Position is purely navigation/layout. It never means importance, priority, Organization hierarchy, authority, risk, or workload. Any perceived centrality is accompanied by explicit controls and structured ordering.

**Shadow.** Shadow/depth is aesthetic hierarchy and focus context, not operational semantics. It may improve separation/readability but cannot indicate state.

## 8. Labels and Badges

**Mandatory labels for an Operational Space** are: name; named attention level; active-work count; Critical Actions count; and last activity/freshness statement. A Space/Area must remain understandable if every graphical cue is removed.

Badges appear only for a disclosed non-zero (or explicitly not-applicable) condition. A badge must name/count its condition and resolve to a structured explanation. Its absence means only â€œzero for this badge ruleâ€ or â€œnot applicable,â€ never â€œhealthy,â€ â€œsafe,â€ or â€œnothing has changed.â€

## 9. Motion Language

| State | Observable trigger | Motion behavior | Text equivalent | Reduced-motion behavior |
| --- | --- | --- | --- | --- |
| Dormant | No active workload and no recent qualifying activity, subject to scope policy. | Almost still. | â€œDormantâ€/â€œNo active workâ€ plus last activity. | Still; same label. |
| Healthy | Only if a future named health classification is approved. | Slow, calm optional breathing. | Health category and source reason. | No autonomous motion. |
| Busy | Recent qualifying activity. | Slightly faster bounded breathing. | â€œRecent activityâ€ with timestamp/count. | No autonomous motion. |
| Attention | Non-critical approved attention classification. | Border/emphasis; optional restrained breathing distinct from busy only after testing. | Attention label, reason, and count. | Border/badge/text only. |
| Critical | Approved Critical Action threshold/classification. | No alarm animation; stable explicit emphasis only. | â€œCriticalâ€ plus count/reasons. | Same text/badge/border. |

**Invariant.** Breathing never changes meaning between Spaces: it always means recent activity. Color/border never changes meaning: both repeat attention level. Size never changes meaning: it remains workload only when enabled.

## 10. Semantic Consistency and Evolution

All future Spacesâ€”Trading, Manufacturing, Healthcare, Energy, Finance, and othersâ€”inherit OVS. A Space may add labels, owned workload categories, or identity texture only through an approved extension that preserves the base meanings. It may not repurpose color as risk, breathing as urgency, size as revenue, or position as hierarchy.

Each extension must declare source owner, deterministic rule, freshness, empty/unknown behavior, accessibility equivalent, reduced-motion behavior, and structured fallback. Unknown, stale, missing, or conflicting data must remain distinct from a favorable condition.

## 11. Recommended MVP Semantics

1. **Labels:** mandatory identity, attention, active-work count, Critical Actions count, and last activity.
2. **Badges:** only explicit Critical Actions and other approved non-zero named counts.
3. **Color/border:** one attention-level semantic, always accompanied by text and badge/reason.
4. **Size:** fixed/bounded until workload sources and buckets are approved; then bucketed workload with raw count.
5. **Breathing:** optional and only for an approved recent-activity rule; reduced motion makes it static.
6. **Position and shadow:** navigation/aesthetic only; no operational meaning.
7. **Halo, texture, internal motion, proximity/deformation:** excluded from MVP.

## 12. Rejected Semantic Ideas

- Color encoding both risk and attention, or any second operational meaning.
- Size encoding revenue, prestige, Organization scale, importance, or urgency.
- Breathing encoding health, workload, or urgency.
- Permanent halos, decorative glow, or unsupported internal motion.
- Position/centrality encoding priority or hierarchy.
- A Space-specific redefinition of shared visual semantics.
- Hidden composite â€œenergy,â€ health, attention, or priority scoring.

## 13. Human Decisions Requiring Approval

1. Which owner/read model supplies the initial workload categories and their scope?
2. What bucket thresholds, zero-state treatment, and freshness rules govern size?
3. What deterministic attention classification may drive the single color/border semantic?
4. Which event types and recency/decay window make breathing meaningful?
5. Is a user-facing â€œhealthyâ€ classification appropriate, and which approved source owns it?
6. Which transitions qualify as significant enough for a transient halo?
7. When may a Space add identity texture without compromising semantic consistency?
8. What review/conformance process approves future OXL extensions and protects reduced-motion/structured equivalence?

## 14. Validation Record

This document is prose-only and contains no Mermaid diagram. Local links and `git diff --check` must pass before handoff. No runtime, backend, API, frontend implementation, prototype file, or component is modified by UX-004.
