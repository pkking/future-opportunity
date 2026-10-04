# 2026-10-05-liquidity-policy: Liquidity-bounded deployment policy

Status: IMPLEMENTING
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
- [ ] Opportunity exposes capacity and qualification reason.
- [ ] StrategyPlan records requested vs actual deployable amount where relevant.
- [ ] Execution cannot exceed the accepted impact/capacity limit.
- [ ] API/CLI/Web expose the policy without hidden resizing.
- [ ] Deterministic E2E scenario proves behavior at/over capacity.
- [ ] Final CI green.

## Implementation slices

- [x] 1. Record ADR for selected policy.
- [ ] 2. Add capacity/impact domain model.
- [ ] 3. Apply qualification gate.
- [ ] 4. Apply plan/execution semantics.
- [ ] 5. Expose API/CLI/Web fields.
- [ ] 6. Add code/API/E2E tests and evidence.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | `uv run ruff check .` | zero violations | pending |
| Code | code-level test gate | liquidity semantics tests | pending |
| API | API contract gate | capacity fields/rejection semantics | pending |
| E2E | strategy E2E gate | oversized-capital scenario artifact | pending |

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

## Deviations and discoveries

None.

## Resume from here

Implement the shared DeploymentAssessment domain model and targeted unit tests,
then update this plan with the verification result.

## Completion

Final commit:
CI run:
E2E artifact:
Remaining unassessed items:
