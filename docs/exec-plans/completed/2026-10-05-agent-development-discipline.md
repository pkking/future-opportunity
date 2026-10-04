# 2026-10-05-agent-development-discipline: Agent-first repository discipline

Status: VERIFYING
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
- [ ] CI has explicit code/API/E2E gates.
- [ ] Deterministic strategy target/evidence E2E exists.
- [ ] E2E evidence is uploaded even when the E2E gate fails.
- [ ] Final CI green.

## Implementation slices

- [x] 1. Add root AGENTS.md.
- [x] 2. Add agent workflow/testing documentation.
- [x] 3. Add execution-plan template and directories.
- [x] 4. Capture paused liquidity decision as active plan.
- [ ] 5. Add deterministic E2E strategy targets/scenarios.
- [ ] 6. Split CI into explicit gates and upload E2E evidence.
- [ ] 7. Add contract test for the agent-development map.
- [ ] 8. Record final CI/evidence and mark completed.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | `uv run ruff check .` | zero violations | pending |
| Code | code-level test job | pytest result | pending |
| API | API contract job | pytest result | pending |
| E2E | strategy acceptance job | JSON + JUnit | pending |

## Decision gates

None. The pending liquidity-policy decision is intentionally captured in a
separate active execution plan.

## Evidence log

- 2026-10-05: reviewed existing CI, design baseline, implementation status, and
  repository test inventory.
- 2026-10-05: consulted the AGENTS.md convention and agent-first repository
  guidance before choosing a short root map plus deeper repository docs.

## Deviations and discoveries

- Existing CI has good coverage but does not separate evidence categories.
- Existing strategy behavior can support deterministic reference E2E without
  using live exchange network calls.

## Resume from here

Add versioned strategy targets and deterministic E2E acceptance tests.

## Completion

Final commit:
CI run:
E2E artifact:
Remaining unassessed items:
