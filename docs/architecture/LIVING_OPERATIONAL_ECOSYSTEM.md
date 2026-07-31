# Living Operational Ecosystem Discovery

**Status:** UX-003 experience-design exploration; not a product decision, implementation specification, or architectural authority.
**Scope:** Explore a visual language for the accepted UX-001/UX-002 navigation hierarchy. No runtime, API, model, authentication, UI, component, CSS, SVG, or asset is created by this document.

**Related documents:** [YARVIS Experience Architecture](YARVIS_EXPERIENCE_ARCHITECTURE.md) defines the navigation hierarchy and non-authoritative projection boundary. [Operational Workspace Experience Discovery](OPERATIONAL_WORKSPACE_EXPERIENCE_DISCOVERY.md) records repository evidence and the future Workspace/Document Registry boundary.

## 1. Design Philosophy

**Experience hypothesis.** YARVIS should not resemble ERP, CRM, project-management, or dashboard software because those visual languages optimize records, pipelines, controls, and reports. They make information legible but do not naturally convey the continuous, interconnected, changing character of operating reality.

An operational system has rhythm: work accumulates and releases, dependencies change, evidence arrives, process state moves, and attention shifts. A distinct visual language can make that rhythm perceptible before an operator reads a table. Its purpose is not novelty. It is to reduce the cognitive cost of locating change and attention while leaving structured precision available immediately afterward.

**Architectural invariant.** Perception never replaces explanation. Every experiential layer is a non-authoritative projection over governed facts, rules, provenance, freshness, and permissions.

## 2. Living Entity Metaphor

**UX hypothesis.** An Operational Space can be perceived as an organism rather than a card, circle, or icon. The metaphor has five experiential aspects:

| Metaphor | Intended perception | Required operational explanation |
| --- | --- | --- |
| Membrane | A bounded, recognizable operating universe. | The visible Space identity and permitted scope, never a tenancy claim by shape alone. |
| Internal energy | Work and activity are present within the Space. | Explicit active-work/activity categories and their source read model. |
| Calm movement | The Space changes over time without demanding constant attention. | A named activity/attention state; never decoration-only motion. |
| Presence | The Space has character and is discoverable in a field. | Label, accessible name, and structured equivalent. |
| Operational metabolism | Inputs, work, evidence, decisions, and outcomes flow through operations. | Only an explanatory narrative unless later backed by explicit, owned read models. |

**Architectural invariant.** Membrane, energy, metabolism, and organism are UX metaphors only. They create no backend representation, domain aggregate, health score, or persisted visual state.

## 3. Motion Vocabulary

**Experience hypothesis.** Motion is peripheral information: seen when useful, ignorable when not. It should be slow enough to disappear from focused reading and clear enough to support an explicit status label.

| Vocabulary | Emotional meaning | Candidate restrained behavior | Constraint |
| --- | --- | --- |
| Dormant | Present, quiet, available. | Almost still; reduced emphasis. | Never hidden merely for being quiet. |
| Calm / healthy | Stable and understandable. | Slow breathing; nearly imperceptible internal change. | â€œHealthyâ€ requires a named, explainable category, not a visual inference. |
| Busy | Active work or recent change. | Slightly faster breathing; small internal activity. | Must be paired with active/recent counters. |
| Needs attention | A review-worthy condition is present. | Soft border change, small deformation, restrained pulse. | Reason and count must be explicit; no alarm behavior. |
| Critical | Clear request for prompt human review. | Stable high-contrast marker and explicit Critical Actions count. | Never flashing, shaking, or continuously red-pulsing. |

**Discovery finding.** â€œSoft pulseâ€ is viable only if it has a tested, bounded vocabulary distinct from â€œbusy.â€ Otherwise it risks becoming decoration or an ambiguous second urgency scale.

## 4. Personality Per Space

**UX hypothesis.** A Space might have a restrained behavioral personality based on the operatorâ€™s familiar rhythm, not arbitrary branding.

| Example Space | Possible personality | Benefit | Risk / guardrail |
| --- | --- | --- | --- |
| Energy company | Slow, stable, predictable, heavy. | Supports a sense of long-lived installation/project cycles. | Do not make urgent field/safety conditions visually slow or less visible. |
| Payments | Fast, constant, fluid. | Recognizes frequent transaction and recovery flow. | More motion can create anxiety and imply volume/priority without evidence. |
| Trading | Session-dependent, alert during market activity, quiet outside it. | Aligns rhythm with a genuine time context. | Requires explicit market-session source/timezone semantics before use. |
| Construction | Massive, slow, momentum-driven. | Evokes long-duration dependency and physical progress. | Must not imply project progress from animation. |
| Healthcare | Soft, continuous, careful. | Encourages calm attention under sensitivity. | Avoid clinical/surveillance symbolism and any health-state ambiguity. |

**Deferred question.** Is Space personality a useful operator-recognition aid, or would it create inconsistent semantics across Spaces? Any later personality system must have a small shared vocabulary, explicit rationale, and a static/reduced-motion equivalent.

## 5. YARVIS as a Gravitational Center

**UX hypothesis.** YARVIS may be perceived as a quiet gravitational center: not a dashboard title or logo, but a focal presence that summarizes transversal awareness while Spaces occupy a calm field around it.

This can communicate that YARVIS observes relationships among operating universes. It must not imply that the center owns their state, decides priority, or has an autonomous authority role. â€œOrbitâ€ is conceptual: no physics engine, force field, or continuous orbital motion is implied.

**Exploration boundary.** The center is useful only if it offers one explainable functionâ€”such as global Critical Actions or an attributable briefing. A purely decorative center should be rejected.

## 6. Attention Attraction

Attention can become more noticeable through several low-intensity mechanisms.

| Mechanism | Explainable when | Risk | Discovery posture |
| --- | --- | --- | --- |
| Explicit badge/counter | It displays deterministic Critical Action or active-work count. | Low; remains readable. | Strong candidate. |
| Border emphasis | It repeats a named attention category. | Color-only interpretation. | Candidate only with text/badge. |
| Slight brightness/contrast | A named state is already disclosed. | Can look decorative or be inaccessible. | Secondary cue only. |
| Slightly larger presence | A displayed bounded category justifies it. | Area implies magnitude and can hide small but critical Spaces. | Experimental only. |
| Slightly closer to center | A disclosed attention tier justifies it. | Position is imprecise, changes with layout, and may create false hierarchy. | Research only. |
| Slightly more activity | A named active/attention state exists. | Can conflate busy with urgent and add anxiety. | Experimental only. |

**Architectural invariant.** No hidden composite score may determine attraction. A user must be able to answer â€œwhat fact made this more noticeable?â€ from visible text and a traceable read-model explanation.

## 7. Transitions and Visual Depth

**UX hypothesis.** Transitions can express operational depth without replacing normal navigation:

1. Entering a Space feels like moving closer to one organism.
2. Entering an Area feels like entering a localized region of that operating context.
3. Entering the Structured Workspace deliberately resolves organic exploration into clean, deterministic precision.

Soft shadow, ambient glow, translucency, restrained gradients, organic borders, and a membrane-like edge may suggest depth. They are acceptable only when they preserve contrast, hierarchy, focus, and text readability. Internal particles and visual noise are speculative: they should not be used without a demonstrated information role.

**Rejected direction.** Skeuomorphismâ€”literal biological skin, fluids, organs, or laboratory imageryâ€”would distract from operational comprehension and risk illness/contamination associations. The goal is an abstract living quality, not biological simulation.

## 8. Calm Technology

**Experience principle.** YARVIS belongs at the edge of attention until an operator needs it. Motion should disappear into peripheral vision, while governed critical information emerges through calm but clear redundancy.

- Default to quiet fields, not always-on stimulation.
- Let the operator choose reduced motion and structured presentation without losing information.
- Reserve stronger contrast, motion, and proximity for explainable attention states.
- Do not use animation to compensate for unclear data, weak categorization, or missing workflow decisions.
- Make a structured Workspace the place for sustained reading, comparison, and action.

## 9. Explainability and Accessibility

**Architectural invariant.** Every visual behavior must answer: â€œWhat operational fact does this represent?â€ Effects without an answer are rejected.

| Requirement | Living-interface response |
| --- | --- |
| Reduced motion | Disable autonomous motion and preserve labels, counts, borders, and structured view. |
| Keyboard | Cells remain semantic buttons/links with logical order, visible focus, predictable destination focus, and standard Back/Escape behavior. |
| Screen reader | Announce identity, current state, active/critical counts, latest activity, and destination; never require motion/position to understand state. |
| Color independence | Pair color/brightness with text, border, icon/badge, and explicit count. |
| Structured equivalent | Every ecosystem/cell field has a static list/grid and the Workspace remains structured. |
| Responsive use | Mobile makes structured/list navigation primary if a spatial field harms tapping or reading. |

## 10. Future Technology Options

**Exploration only.** No technology choice follows from UX-003.

| Technology | Complexity / maintainability | Performance / accessibility | Appropriate exploration | Avoid when |
| --- | --- | --- | --- | --- |
| Pure CSS | Low; easy to inspect and reduce-motion control. | Strong for bounded transitions; semantic DOM remains primary. | MVP breathing, borders, gradients, and controlled depth. | Layout needs deterministic simulation or data visualization beyond CSS. |
| SVG | Low/medium; explicit, scalable shapes and paths. | Good accessibility when accompanied by DOM text; careful focus semantics needed. | Membranes, organic borders, simple static/internal diagrams. | Used as the only interactive/accessibility layer. |
| Canvas | Medium; custom drawing/state management. | Efficient for many visuals but weak native semantics. | Performance prototype with DOM overlay/equivalent. | Early MVP or when accessibility is not separately funded. |
| React Spring / Motion | Medium; adds API/dependency and motion policy surface. | Can provide controlled transitions; still needs reduced-motion governance. | Later prototype comparing declarative motion ergonomics. | Added before CSS/SVG limits are demonstrated. |
| Matter.js | High; introduces physical model semantics. | Simulation can be costly and hard to make explainable. | Research-only collision behavior experiment. | Production-like UX without a proven information benefit. |
| Three.js / WebGL | High; rendering, input, performance, accessibility overlays. | Visually powerful but accessibility and device constraints are substantial. | Visual research only. | Operational MVP, dense work, or any experience needing simple semantics. |

**Candidate technologies for later investigation:** CSS and SVG first; Canvas only for a measured density/performance problem; a motion library only after a prototype proves CSS insufficient. **Technologies to avoid for the foreseeable MVP:** Matter.js, Three.js, and WebGL.

## 11. MVP, Later Evolution, Experimental, and Research

| Horizon | Scope |
| --- | --- |
| MVP | Labelled Space/Area entities; fixed/bounded presentation; explicit counters/badges; calm CSS-level optional motion; visible focus; reduced-motion mode; structured equivalent; deterministic transition to Workspace. |
| Later evolution | Approved Space/Area configuration, explainable health categories, tested per-Space personality, richer direct activity context, and attributable global briefing. |
| Experimental | Membrane deformation, modest attention attraction, richer transition depth, and carefully scoped internal activity. Each needs prototype evidence and accessibility review. |
| Research only | Physics/orbit simulation, particle systems, Canvas at scale, Matter.js, Three.js, WebGL, and any behavior based on composite scoring. |

## 12. Open Questions Requiring Human Approval

1. Does the organism metaphor feel premium and memorable to target operators, or does it read as decorative?
2. Should every Space have a distinct personality, and what shared vocabulary prevents semantic inconsistency?
3. Is a central YARVIS presence helpful as transversal awareness or visually dominant?
4. Which explicit facts may control border, brightness, breathing, deformation, or proximityâ€”and which must remain fixed?
5. Is â€œhealthyâ€ an acceptable operator-facing category, and which owned rule produces it?
6. Should Critical Actions be the sole initial attention signal, or may recent activity have a separate visible behavior?
7. What evidence threshold must a motion prototype meet before introduction into an operational UI?
8. When must a structured list replace spatial exploration, especially on mobile and for high-density Spaces?

## 13. Rejected Ideas

- Generic organisms, bubbles, or visual-layout records persisted as Core data.
- Hidden â€œoperational energy,â€ health, or priority scores.
- Flashing, shaking, alarm colors, continuous critical pulses, and decorative particles.
- Literal biology, skeuomorphism, pathology/contamination imagery, or game-like simulation.
- Motion that denotes a fact unavailable to reduced-motion, keyboard, or screen-reader users.
- A force/physics engine decision before evidence that simpler, accessible techniques fail.

## Validation Record

This document is intentionally prose-only: no Mermaid fence or runtime artifact is introduced. Local links and `git diff --check` must be validated before handoff. No file is staged or committed by UX-003.
