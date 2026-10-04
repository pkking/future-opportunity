# 2026-10-05-historical-backtest-evidence: Historical strategy backtest evidence

Status: IMPLEMENTING
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

- [x] Select an official/open historical data source with documented provenance.
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

- [x] 1. Research official/open historical data sources and reusable tooling.
- [x] 2. Record data/evidence design and any material decision as ADR.
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
- 2026-10-05: selected OKX public historical market-data catalog as the initial
  unified history source. Official contract supports SPOT/FUTURES/SWAP plus
  funding and 400/5000-level order-book archives and returns direct archive
  URLs with filename/date/size metadata.
- 2026-10-05: official catalog contract requires SPOT instIdList and derivative
  instFamilyList; order-book archive dates use UTC while funding and other
  modules use UTC+8. Availability is typically T+3 for books and T+2 for
  funding/other modules.
- 2026-10-05: derivative historical size cannot be normalized without pinned
  instrument metadata (ctVal/ctMult/ctValCcy/settleCcy). Historical FUTURES
  metadata must be captured in the dataset manifest rather than inferred from
  symbol naming.
- 2026-10-05: OKX public history-mark-price-candles provides 1m historical mark
  price candles from recent years. Official funding formula is position value
  multiplied by funding rate; USDT-margined position value depends on contract
  size/multiplier and mark price.
- 2026-10-05: initial local environment could not fetch archive bytes, so raw
  parsing remained blocked rather than guessed.
- 2026-10-05: non-gating GitHub Actions probe resolved the evidence gap. Run
  37218442680 produced okx-historical-schema-probe artifact ID 11309790145.
  Official module-4 L2 files are tar.gz archives containing JSONL .data files.
  The stream starts with action=snapshot and continues with action=update;
  asks/bids levels are [price,size,orderCount], and zero size removes a level.
- 2026-10-05: probe captured SPOT USDC-USDT raw SHA-256
  25c59d54bc4797e6353e01f2fb1e0ec4a63b2e00986761821ce516359c3b6b9a
  and SWAP USDC-USDT-SWAP raw SHA-256
  c21b083f6116cb9411d6738d85a2776db2db5fde579d0fd2d8cfbba2b5426835.
  SWAP metadata captured ctVal=10, ctMult=1, ctValCcy=USDC, settleCcy=USDT.
- 2026-10-05: hftbacktest is useful reference material for deterministic L2
  replay methodology, but is not required as a dependency for the current
  taker/capacity execution model.

## Deviations and discoveries

None.

## Resume from here

Implement the verified streaming tar.gz JSONL order-book replayer. Require an
initial snapshot, fail closed on unknown actions/schema, and require pinned
contract metadata before normalizing derivative sizes.

## Completion

Final implementation commit:
CI run:
Historical evidence artifact:
Remaining unassessed items:
