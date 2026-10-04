# Agent Execution Plans

This directory is durable work-in-progress state for coding agents.

- `active/` — unfinished, paused, blocked, implementing, or verifying work.
- `completed/` — work whose final commit passed all required CI gates.
- `TEMPLATE.md` — mandatory structure for non-trivial work.

The plan is deliberately repository-local so a different agent can resume
without access to the previous conversation or scratchpad.

Do not use this directory as a design-decision substitute. Durable architecture
choices belong in `docs/adr/`.
