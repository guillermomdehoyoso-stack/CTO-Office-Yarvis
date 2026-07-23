# Yarvis Development Operating System

The Development Operating System (DOS) is repository-resident engineering
context. It allows a new contributor or AI agent to reconstruct the active
engineering state without recovering a previous ChatGPT conversation.

The DOS is not part of the Yarvis runtime. It does not define domain semantics,
replace architectural authority, or grant implementation permission. It records
current state, active work, short decisions, session structure, and prompt
locations so work can begin from evidence.

Use the DOS at the start of every session:

1. Read `PROJECT_CONTEXT.md` for identity and authority.
2. Read `CURRENT_STATE.md` for the live gate and next mandatory action.
3. Read `CURRENT_SPRINT.md` for the active scope and exit conditions.
4. Read the relevant roadmap, baseline, design, review, and architecture source.

`AGENTS.md` provides the mandatory bootstrap instruction for AI agents. The
repository, not chat memory, is the source of truth. Facts that cannot be
verified are recorded as `UNKNOWN` or `TO BE VERIFIED`.

The `prompts/` tree stores reusable prompts by category. `PROMPT_INDEX.md` is an
index only; prompts remain separate from their index records.
