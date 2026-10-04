# 2026-10-05-agent-development-discipline: Agent-first repository discipline

Status: COMPLETED
Owner: agent
Started: 2026-10-05
Last checkpoint: 2026-10-05

## Objective

Make AGENTS.md the canonical map for plan-first, interruptible, reproducible,
evidence-driven agent development, and make CI explicitly prove code/API/E2E
strategy behavior.

## Non-goals

- No change to strategy economics.
- No live trading capability.
- No resolution of the pending liquidity-policy decision.

## Current facts

- The repository already has a frozen design baseline and ADRs.
- CI previously ran lint plus one undifferentiated pytest suite.
- API smoke tests and many domain/integration tests already exist.
- No repository-local execution-plan protocol existed.
- No dedicated deterministic strategy-acceptance E2E artifact existed.

## Acceptance criteria

- [x] Root AGENTS.md maps the repository and mandatory agent protocol.
- [x] Detailed workflow/testing rules are versioned under docs.
- [x] Active/completed execution-plan convention exists.
- [x] Interrupted liquidity-policy work is captured as an active resumable plan.
- [x] CI has explicit code/API/E2E gates.
- [x] Deterministic strategy target/evidence E2E exists.
- [x] E2E evidence is uploaded even when the E2E gate fails.
- [x] Final CI green.

## Implementation slices

- [x] 1. Add root AGENTS.md.
- [x] 2. Add agent workflow/testing documentation.
- [x] 3. Add execution-plan template and directories.
- [x] 4. Capture paused liquidity decision as active plan.
- [x] 5. Add deterministic E2E strategy targets/scenarios.
- [x] 6. Split CI into explicit gates and upload E2E evidence.
- [x] 7. Add contract test for the agent-development map.
- [x] 8. Record final CI/evidence and mark completed.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | `uv run ruff check .` | zero violations | passed |
| Code | code-level test job | pytest result | passed |
| API | API contract job | pytest result | passed |
| E2E | strategy acceptance job | JSON + JUnit | passed |

## Decision gates

None. The pending liquidity-policy decision is intentionally captured in a
separate active execution plan.

## Evidence log

- 2026-10-05: reviewed existing CI, design baseline, implementation status, and
  repository test inventory.
- 2026-10-05: consulted the AGENTS.md convention and agent-first repository
  guidance before choosing a short root map plus deeper repository docs.
- 2026-10-05: CI run 37215823464 completed successfully for commit
  41aaf4dc56642b5074000499fa7bcbaf4b574bc8.
- 2026-10-05: E2E strategy acceptance ran 2 deterministic strategy scenarios;
  both passed. JUnit and JSON evidence were uploaded as
  `strategy-e2e-evidence`, artifact ID 11308007417.

## Deviations and discoveries

- Existing CI has good coverage but does not separate evidence categories.
- Existing strategy behavior can support deterministic reference E2E without
  using live exchange network calls.

## Resume from here

Completed. Resume product development from the active liquidity-policy plan:
`docs/exec-plans/active/2026-10-05-liquidity-policy.md`.

## Completion

Final implementation commit: 41aaf4dc56642b5074000499fa7bcbaf4b574bc8
CI run: https://github.com/pkking/future-opportunity/actions/runs/37215823464
E2E artifact: strategy-e2e-evidence (artifact ID 11308007417)
Remaining unassessed items: none for the agent-development discipline itself.
