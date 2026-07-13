# Yarvis Engineering Workflow v1.0

## 1. Purpose

Define a single execution workflow for engineering work in Yarvis, including authority order, approval classes, stop conditions, and closure evidence.

This workflow is mandatory for implementation, review, and release preparation.

## 2. Roles

- Product/Founder Owner: defines priorities, approves sensitive/destructive actions, accepts delivery.
- Engineering Owner: technical decisions, scope control, risk management.
- Implementing Agent: executes approved tasks under active prompt constraints.
- Reviewer: validates compliance, security posture, and closure evidence.

## 3. Sources of Authority

Authority order is strict:

1. Active user prompt (current explicit instruction).
2. Repository governance documents and ADRs.
3. Previous prompts and prior assumptions.

Rules:

- A posterior negative instruction prevails over any prior instruction.
- An agent cannot execute a Class C or Class D operation if the active prompt prohibits it.
- Designing a script does not authorize executing that script.
- An agent cannot self-approve its own sensitive operation.
- Keep does not mean commit, push, or deployment.
- A report must reflect the real content of files on disk.
- If report and repository differ, the repository is authoritative.

## 4. Stages 0–9

- Stage 0: Intake and scope lock.
- Stage 1: Baseline inventory.
- Stage 2: Risk and constraints validation.
- Stage 3: Design and plan.
- Stage 4: Controlled implementation.
- Stage 5: Non-destructive validation.
- Stage 6: Sensitive/destructive action gate.
- Stage 7: Evidence capture.
- Stage 8: Closure recommendation.
- Stage 9: Handoff for next phase.

## 5. Approval Classes A–D

- Class A (safe/read-only): inventory, read, search, lint-like checks, non-destructive documentation updates.
- Class B (controlled/write-non-destructive): source/doc updates, config hardening, scripts creation without execution.
- Class C (sensitive operational): backup generation, security scans across history, operations that touch sensitive data paths.
- Class D (destructive or high-impact): restore, drop/truncate/overwrite operations, history rewriting, irreversible changes.

Mandatory mappings:

- Backup is Class C.
- Restore is Class D.

## 6. Security Rules

- Trust by Design.
- Least Privilege.
- No secrets in Git.
- Local-first while authentication is absent.
- Human confirmation before destructive actions.
- Security claims must reflect real current state, never future assumptions.

## 7. Database and Migrations

- Do not modify existing migrations without explicit approval.
- Preserve development data unless explicit destructive authorization exists.
- Restore must target a temporary/non-primary database by default.
- The development restore script must never point to the primary database by default.
- The development restore script can never restore over `yarvis`.
- Restore against primary requires explicit exceptional approval outside normal workflow.

## 8. Dependencies

- Audit first, modify later.
- No automatic dependency upgrades in security hardening sprints unless explicitly approved.
- Record vulnerability findings with remediation plan and owner.

## 9. Documentation Discipline

- Every sprint closure must include: what changed, what was validated, what remains blocked.
- Security and operational gates must be explicit and binary (READY/BLOCKED).
- Deviations from process must be documented as deviations, not hidden as success.

## 10. Evidence of Closure

Minimum closure evidence:

- required command outputs;
- file-level change list;
- risk deltas;
- blocked items;
- recommendation status.

## 11. Stop Conditions

Stop and escalate immediately when:

- prompt prohibits the next required operation;
- required approval for Class C/D is absent;
- a potential secret exposure is detected;
- destructive impact cannot be bounded;
- environment inconsistency invalidates test evidence.

## 12. Commit Discipline

- Small, reversible changes.
- No commit unless explicitly requested.
- No push unless explicitly requested.
- No deployment unless gate is READY and explicitly authorized.

## 13. Keep / Keep With Notes / Undo

- Keep: changes are acceptable as-is for current scope. This does not authorize stage, commit, push, or deployment.
- Keep With Notes: changes are acceptable with explicit residual risks/debt documented.
- Undo: changes are not acceptable and must be reverted or replaced.

## 14. Definition of Done

Work is Done only when:

- scope instructions are fully satisfied;
- all prohibitions were respected;
- required validations were executed or explicitly blocked with reason;
- security claims match observed reality;
- closure evidence is complete;
- recommendation is explicit: Keep, Keep With Notes, or Undo.
