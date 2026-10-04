# 2026-10-05-liquidity-policy: Liquidity-bounded deployment policy

Status: COMPLETED
Owner: agent
Started: 2026-10-05
Last checkpoint: 2026-10-05

## Objective

Define how a user capital intent interacts with finite order-book capacity,
then implement that policy consistently across Opportunity qualification,
StrategyPlan, paper execution, API/CLI/Web, and E2E evidence.

## Non-goals

- No live trading.
- No portfolio optimization.
- No cross-venue execution.

## Must-read context

- `AGENTS.md`
- `docs/design-baseline-v0.1.md`
- `docs/adr/0001-isolated-capital-model.md`
- `docs/agents/workflow.md`
- `docs/agents/testing.md`

## Current facts

- Capital allocation uses the accepted isolated-capital model.
- Market-order simulation walks order-book depth and can detect insufficient
  liquidity.
- Opportunity qualification already gates execution.
- The unresolved semantic question is whether an oversized user capital intent
  is rejected or silently/explicitly reduced to available liquidity capacity.
- Recommendation already presented: default reject; optional partial deployment
  only through an explicit future opt-in.

## Constraints and invariants

- Never silently deploy materially less capital than the user requested.
- Capacity must be visible as business data, not hidden as an execution error.
- Plan/Execution must remain traceable to the qualified Observation.
- Any material liquidity-policy choice changes user semantics and requires an ADR.
- Paper-only boundary remains unchanged.

## Acceptance criteria

- [x] Human accepts one liquidity-deployment semantic.
- [x] ADR records the accepted policy.
- [x] Opportunity exposes capacity and qualification reason.
- [x] StrategyPlan records requested vs actual deployable amount where relevant.
- [x] Execution cannot exceed the accepted impact/capacity limit.
- [x] API/CLI/Web expose the policy without hidden resizing.
- [x] Deterministic E2E scenario proves behavior at/over capacity.
- [x] Final CI green.

## Implementation slices

- [x] 1. Record ADR for selected policy.
- [x] 2. Add capacity/impact domain model.
- [x] 3. Apply qualification gate.
- [x] 4. Apply plan/execution semantics.
- [x] 5. Expose API/CLI/Web fields.
- [x] 6. Add code/API/E2E tests and evidence.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | `uv run ruff check .` | zero violations | passed |
| Code | code-level test gate | liquidity semantics tests | passed |
| API | API contract gate | capacity fields/rejection semantics | passed |
| E2E | strategy E2E gate | oversized-capital scenario artifact | passed |

## Decision gates

### Decision: oversized requested capital

Options:

1. Reject when target notional exceeds configured liquidity/impact capacity.
2. Automatically reduce the deployment.
3. Default reject, with an explicit partial-deployment opt-in.

Evidence:

- Silent partial deployment changes the user's capital intent.
- Existing domain semantics treat StrategyPlan as an explicit executable intent.
- Capacity is observable from order-book depth and can be represented before
  execution.

Recommendation:

Option 3: default reject; partial deployment only when explicitly requested.

Consequence:

This creates an explicit liquidity policy and makes unused capital visible.

Status: ACCEPTED

## Evidence log

- 2026-10-05: implementation paused before selecting liquidity policy.
- 2026-10-05: repository agent-development discipline established before
  resuming this decision.
- 2026-10-05: user instructed development to continue under AGENTS.md; accepted
  the previously recommended Option 3: STRICT by default, explicit PARTIAL
  opt-in. ADR-0005 records the decision.
- 2026-10-05: shared DeploymentAssessment implemented; strict and partial
  application tests pass in CI.
- 2026-10-05: API contract verifies strict rejection and explicit partial
  execution; Web contract added after discovering and repairing a previously
  corrupted index.html.
- 2026-10-05: E2E run 37216924324 passed 3 deterministic scenarios in 0.12s,
  including oversized-capital strict/partial semantics. Evidence uploaded as
  strategy-e2e-evidence artifact ID 11308153322.
- 2026-10-05: CI runs 37217071178 / 37217073749 / 37217076939 exposed one
  CLI contract-test defect: Rich ANSI styling split the rendered option token.
  The business CLI options were present; the evidence assertion was fixed by
  stripping ANSI rather than weakening the option-name assertion.
- 2026-10-05: final implementation CI run 37217156199 succeeded on commit
  f2a0ad643e0faff0b8cb70307513860eb29c1832. Static, code-level, API contract,
  and E2E strategy acceptance gates all passed.
- 2026-10-05: final E2E strategy acceptance passed 3 scenarios in 0.11s;
  strategy-e2e-evidence artifact ID 11308397969.

## Deviations and discoveries

None.

## Resume from here

Completed. The next non-trivial change must start from a new active execution
plan under docs/exec-plans/active/.

## Completion

Final implementation commit: f2a0ad643e0faff0b8cb70307513860eb29c1832
CI run: https://github.com/pkking/future-opportunity/actions/runs/37217156199
E2E artifact: strategy-e2e-evidence (artifact ID 11308397969)
Remaining unassessed items: none for ADR-0005 liquidity deployment semantics.
