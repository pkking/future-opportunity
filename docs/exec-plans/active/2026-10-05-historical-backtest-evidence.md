# 2026-10-05-historical-backtest-evidence: Historical strategy backtest evidence

Status: PLANNING
Owner: agent
Started: 2026-10-05
Last checkpoint: 2026-10-05

## Objective

Upgrade strategy E2E evidence from deterministic reference scenarios to
reproducible historical-market backtests that can answer whether the current
Funding Carry and Cash-and-Carry strategies meet versioned targets on captured
real market history.

## Non-goals

- No live trading.
- No ML return prediction.
- No portfolio optimization.
- No dependence on paid/proprietary market-data SaaS as the only evidence source.
- Do not replace the fast deterministic reference E2E; historical replay is an
  additional evidence layer.

## Must-read context

- `AGENTS.md`
- `docs/agents/testing.md`
- `docs/design-baseline-v0.1.md`
- `docs/adr/0001-isolated-capital-model.md`
- `docs/adr/0005-liquidity-bounded-deployment.md`
- `tests/e2e/strategy-targets.json`

## Current facts

- CI has deterministic offline reference E2E with machine-readable evidence.
- Final liquidity-policy repository CI run 37217265012 is green on
  6b6c765caca720796165088887b810aa3e7bd891.
- Current E2E evidence artifact ID is 11308912872; 3 scenarios passed.
- Existing replay fixtures are synthetic/versioned reference cases, not
  historical exchange datasets.
- Backtest evidence must preserve execution costs, liquidity/capacity, return
  attribution, risk states, and evidence completeness.

## Constraints and invariants

- Historical provenance and checksum must be captured.
- CI must not depend on live network availability.
- Raw historical data may be prepared outside CI, but the CI input must be
  versioned/pinned and reproducible.
- Prefer official exchange public archives and open-source tooling.
- Never fabricate missing order-book depth. Missing market evidence is
  `UNASSESSED`.
- Historical target changes are product/strategy changes, not test-only edits.
- Keep the existing fast reference E2E as a separate gate.

## Acceptance criteria

- [ ] Select an official/open historical data source with documented provenance.
- [ ] Define a canonical historical replay dataset format.
- [ ] Implement import/normalization tooling with checksums.
- [ ] Implement strategy backtest runner over multiple timestamps/periods.
- [ ] Produce actual-vs-target aggregate metrics and per-sample diagnostics.
- [ ] Funding Carry historical evidence includes funding history and market price evidence.
- [ ] Cash-and-Carry historical evidence includes dated-future basis through expiry/close evidence.
- [ ] CI has an offline pinned historical-backtest smoke/acceptance dataset.
- [ ] Evidence artifact is uploaded even on failure.
- [ ] README/testing docs describe provenance and reproduction.
- [ ] Final CI green.

## Implementation slices

- [ ] 1. Research official/open historical data sources and reusable tooling.
- [ ] 2. Record data/evidence design and any material decision as ADR.
- [ ] 3. Add canonical replay-domain format and importer.
- [ ] 4. Add backtest application workflow and metrics.
- [ ] 5. Add pinned historical fixtures + provenance/checksum manifest.
- [ ] 6. Add historical strategy targets and CI evidence.
- [ ] 7. Document reproduction and close the plan.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | existing static gate | zero violations | pending |
| Code | code-level test gate | importer/replay/metrics tests | pending |
| API | API contract gate | no regression | pending |
| Reference E2E | existing strategy E2E | 3 scenarios remain green | pending |
| Historical backtest | new offline replay gate | metrics + provenance artifact | pending |

## Decision gates

None yet. Research first.

## Evidence log

- 2026-10-05: previous liquidity-policy plan completed and archived.
- 2026-10-05: final repository CI run 37217265012 passed all four gates;
  strategy-e2e-evidence artifact ID 11308912872.

## Deviations and discoveries

None.

## Resume from here

Research official/open historical market-data archives and reusable backtest
tooling. Determine whether they provide the depth/funding/dated-future evidence
required by the existing domain model without inventing missing data.

## Completion

Final implementation commit:
CI run:
Historical evidence artifact:
Remaining unassessed items:
