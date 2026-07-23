# Yarvis Engineering Agent Bootstrap

This repository is the authoritative source of engineering context. Chat history,
memory, screenshots, and external attachments are not authoritative.

At the beginning of every engineering session, read in this order:

1. `docs/development/PROJECT_CONTEXT.md`
2. `docs/development/CURRENT_STATE.md`
3. `docs/development/CURRENT_SPRINT.md`
4. The relevant roadmap or roadmap amendment.
5. The relevant ratified design, baseline, review, and architecture documents.

Then determine and state:

- the current engineering gate;
- the current work package;
- the next allowed action; and
- whether the repository state must be verified before changes.

Repository documentation overrides remembered conversation. If documentation and
implementation evidence disagree, do not assume; inspect the repository and
record the discrepancy. If a required fact cannot be verified, mark it `UNKNOWN`
or `TO BE VERIFIED` rather than inventing it.

Do not treat a proposed document as ratified authority. Preserve the authority
order declared by the Constitution, ratified architecture, interaction contracts,
decision trace, Technical Blueprint, component baselines, and roadmap governance.

Before modifying implementation, confirm that the requested work is permitted by
the current gate and relevant baseline. Keep documentary changes, architecture
changes, and implementation changes explicitly separated.
