# UX-002 — YARVIS Interactive Experience Prototype

**Status:** Isolated frontend prototype; ready for hands-on product review, not a production route or implementation baseline.
**Scope:** Static-data validation of the UX-001 experience hierarchy. No backend/API/authentication/storage/runtime integration is included.

## Purpose and Isolation

UX-002 validates this flow:

```text
YARVIS Home → Operational Space → Operational Area → Structured Operational Workspace
```

It tests whether controlled cellular navigation can remain calm, explainable, accessible, responsive, and compatible with a precise structured workspace. The prototype is deliberately not imported by `apps/web/src/App.tsx` or `apps/web/src/main.tsx`, and has no production route.

## Development Preview

From `C:\Python Projects\CTO Office\apps\web`, run this PowerShell command:

```powershell
npm.cmd exec vite -- --host 127.0.0.1 --open /prototypes/yarvis-experience.html
```

The standalone development-only HTML entrypoint is `apps/web/prototypes/yarvis-experience.html`; it mounts `src/prototypes/yarvis-experience/main.tsx` directly. It does not alter the application entrypoint, router, or production route table.

## Files

- `apps/web/prototypes/yarvis-experience.html`
- `apps/web/src/prototypes/yarvis-experience/main.tsx`
- `apps/web/src/prototypes/yarvis-experience/YarvisExperiencePrototype.tsx`
- `apps/web/src/prototypes/yarvis-experience/yarvisExperiencePrototype.css`
- `apps/web/src/prototypes/yarvis-experience/YarvisExperiencePrototype.test.tsx`

## Interaction and Hierarchy Review

The current level is named on every screen: **YARVIS Home**, **Operational Space**, **Operational Area**, or **Structured Operational Workspace**. Selected Space/Area identity remains visible in headings and breadcrumbs. Back and Escape move exactly one level at a time; Home is reached after Space → Home. After every level transition, focus moves to the destination heading.

The prototype’s controls are intentionally non-persistent: scenario, normal/reduced motion, and spatial/structured fallback. They are prototype-only controls, not production settings.

## Static Scenarios and Transparent Semantics

| Scenario | Exact static semantics | Intended experience |
| --- | --- | --- |
| Stable day | Energía Fotónica: 14 active / 1 critical / stable; NetPay: 11 / 1 / active; Trading: 9 / 1 / active. | Mostly still with low attention and no chaos. |
| Energía Fotónica needs attention | Energía Fotónica: 21 active / 5 critical / strained / critical; the other Spaces retain their base state. | Immediate explicit attention through label, counter, badge background, and border—not flashing. |
| Multi-space active day | Each Space is watch/active with 2 critical actions; active work increases by 7–9 and recent activity is 6–8 updates today. | Distributed activity using the same bounded animation, not a busier layout. |

Area data is static. Its labels, classification, active count, and critical count are displayed without being treated as a domain model or source of truth.

## Cellular and Motion Review

| Visual signal | Current meaning | Review outcome |
| --- | --- | --- |
| Size | None. Space cells have a fixed bounded presentation. | Clear; cell size does not imply a hidden volume/priority score. |
| Border | Attention/health category. | Redundant text/counters remain visible. |
| Counter/badge | Explicit active-work and Critical Action counts. | Clear and keyboard/screen-reader exposed. |
| Movement/breathing | Active and critical attention categories only. | CSS-only, bounded `translateY(-4px)`/scale breathing; stable cells have no autonomous animation. |
| Central proximity | Not used. | Removed because it competed with the breathing transform and lacked a sufficiently clear independent explanation. |
| Central YARVIS presence | Global Critical Action briefing only. | Deliberately bounded; human review must confirm it is useful rather than dominant. |

There is no physics library, collision simulation, flashing, shaking, particle effect, continuous critical pulse, color-only meaning, or composite operational score. CSS `prefers-reduced-motion` and the visible control disable autonomous animation. On mobile, autonomous animation is also disabled.

## Accessibility Review

- Space and Area cells are semantic buttons with accessible names containing identity, active work, Critical Actions, health/attention, and latest activity.
- Native buttons provide Enter/Space activation; visible focus styles are present.
- Escape and Back navigate one level at a time; focus is asserted on the destination heading by focused tests.
- Labels, counters, borders, and structured fallback preserve state without reliance on color, size, movement, position, hover, or icon.
- The structured fallback is a non-animated list for Space and Area navigation.

## Responsive Review

| Width/form factor | Verified CSS behavior |
| --- | --- |
| Desktop | Three-column spatial field, bounded gaps, clear labels, practical cell targets. |
| Tablet | Fluid grid contracts through `minmax`; controls wrap rather than overlap. |
| Mobile (`≤700px`) | Cells become a stable one-column stack; metrics/workspace columns stack; autonomous animation is disabled; controls and labels remain visible. |

The layout uses grid/flex constraints and has no fixed viewport-width element or horizontal scroll rule. Hands-on review at actual device widths remains required.

## Dependencies and Limitations

No dependency was introduced. UX-002 uses existing React, Testing Library, Vitest, Vite, and CSS only. It has no dynamic Space discovery, URL/history integration, user preference persistence, real Critical Actions read model, Area configuration model, production visual system, or user research evidence.

## Human Review Checklist

- Does the interface feel alive rather than decorative?
- Is the movement helpful or distracting?
- Is the attention-needing Space immediately identifiable?
- Are Space and Area levels distinguishable?
- Does the transition into structured work feel natural?
- Is the central YARVIS presence useful or visually dominant?
- Should cell size encode work volume, critical count, or remain fixed?
- Should attention affect movement, center proximity, or only explicit badges?
- Is structured fallback good enough to be a permanent parallel view?

## Validation Record

- Focused prototype tests passed: 3 tests.
- Full frontend suite passed: 13 files, 43 tests. Existing React Router future-flag warnings remain unrelated to UX-002.
- Isolated preview validation passed: Vite served `/prototypes/yarvis-experience.html` and returned the expected standalone HTML without importing the production application.
- Normal production build: `npm.cmd run build` remains blocked by `EPERM` on `C:\Python Projects\CTO Office\apps\web\dist\assets` before bundling. Do not claim it passes until the lock is released.

After the lock is released, use:

```powershell
Remove-Item -LiteralPath 'C:\Python Projects\CTO Office\apps\web\dist\assets' -Recurse -Force
npm.cmd run build
```

Run the cleanup only after confirming no process is using that generated output directory. No production route, API, dependency, or backend change is authorized by this prototype.
