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
- [x] Define a canonical historical replay dataset format.
- [x] Implement import/normalization tooling with checksums.
- [x] Implement strategy backtest runner over multiple timestamps/periods.
- [ ] Produce actual-vs-target aggregate metrics and per-sample diagnostics.
- [x] Funding Carry historical evidence includes funding history and market price evidence.
- [x] Cash-and-Carry historical evidence includes dated-future basis through expiry/close evidence.
- [ ] CI has an offline pinned historical-backtest smoke/acceptance dataset.
- [ ] Evidence artifact is uploaded even on failure.
- [ ] README/testing docs describe provenance and reproduction.
- [ ] Final CI green.

## Implementation slices

- [x] 1. Research official/open historical data sources and reusable tooling.
- [x] 2. Record data/evidence design and any material decision as ADR.
- [x] 3. Add canonical replay-domain format and importer.
- [x] 4. Add backtest application workflow and metrics.
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

### Historical target semantics

Implementation can continue through pinned offline fixtures and actuals. Before
turning historical evidence into a pass/fail acceptance gate, human approval is
required on whether historical targets:

1. reuse deterministic reference per-opportunity return thresholds;
2. use separate historical aggregate/distribution thresholds; or
3. gate evidence/provenance/strategy semantics while reporting historical return
   distributions without requiring every historical period to hit the reference
   return target.

Do not lower the existing reference targets to make historical data pass.

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
- 2026-10-05: funding schema probe run 37249021018 verified the official
  BTC-USDT-SWAP monthly funding archive. It is a ZIP containing CSV with exactly
  `instrument_name,funding_rate,funding_time`; sampled rows are 8-hour funding
  events. Raw SHA-256:
  ce5a600e578678a73294a316592afea9cc2a7f0702bf15d56eb0c9ee68fa5a65.
  The funding archive contains no mark price, so historical funding cash-flow
  evidence requires a separately pinned mark-price source.
- 2026-10-05: fail-closed module-4 tar.gz/JSONL L2 parser implemented and CI
  verified. Derivative quantity normalization requires pinned contract metadata
  and refuses price-dependent normalization when ctValCcy is not the base asset.
- 2026-10-05: canonical full-book JSONL schema v1 implemented with deterministic
  serialization and SHA-256 round-trip verification.
- 2026-10-05: asynchronous book alignment implemented as explicit as-of join
  with max-staleness; missing/stale samples are counted instead of silently
  filled forward.
- 2026-10-05: strict module-3 funding ZIP/CSV parser implemented and CI verified.
- 2026-10-05: Cash-and-Carry historical multi-case runner implemented through
  the production Discover -> Simulate -> Delivery Close workflow; CI run
  37249303268 passed.
- 2026-10-05: module-6 BTC 50-level files are not suitable as small fixtures:
  2026-10-01 SPOT catalog size 228.7 MB, SWAP 318.11 MB; FUTURES had no module-6
  candidate.
- 2026-10-05: real BTC Funding fixture preparation run 37250411433 succeeded.
  Dataset `okx-btc-usdt-funding-carry-2026-09-01-v1` pins:
  SPOT raw SHA-256
  3651c6a1764da45b37192ea1f70c9b5e16ecb1baa9bd9044f3713ed74a40c3dd,
  SWAP raw SHA-256
  0578d114ceee62b2997c1a8b1b52a63fc046ab3a7235c74ffe5c3b26d0f41b80,
  funding raw SHA-256
  ce5a600e578678a73294a316592afea9cc2a7f0702bf15d56eb0c9ee68fa5a65.
  At 15-minute cadence, 95/96 SPOT/SWAP samples aligned within 5 seconds
  (coverage 98.95833333333333333333333333%); no aligned sample was stale.
  Three funding events and matching confirmed 1-minute mark-price candles were
  pinned. Artifact ID 11320128320.
- 2026-10-05: historical Funding actuals run 37311428410 evaluated the real
  dataset through production Discover -> Simulate semantics. The
  2026-09-01T00:15Z..23:45Z one-day case was correctly rejected:
  expected_net_return=-0.001309413091319054999999999910 and reason
  `expected_net_return_not_positive`. This is a valid negative historical
  result, not a fixture failure. Artifact ID 11346790352.
- 2026-10-05: module-4 FUTURES coverage is date-dependent, not absent. Probe run
  37250372698 found BTC-USDT futureschain archives on 2026-03-01 (44.19 MB) and
  2026-06-01 (20.74 MB), but none on sampled 2026-07-01/08-01/09-01 dates.
  The 2026-06-01 archive contains exactly one member,
  `BTC-USDT-260626-L2orderbook-400lv-2026-06-01.data`, so the existing strict
  single-instrument L2 replay shape applies.
- 2026-10-05: real Cash-and-Carry preparation run 37312871269
  succeeded for `okx-btc-usdt-cash-and-carry-2026-06-v1`. The case uses
  2026-06-01T00:15Z entry and 2026-06-25T00:15Z pre-expiry close for
  `BTC-USDT-260626`, with four official module-4 L2 archives and explicit
  product-spec metadata provenance. Canonical books are all within 28 ms of
  their requested sample times. Fixture artifact ID 11346248569 (17 KB).
- 2026-10-05: the first real Cash-and-Carry case was correctly rejected:
  entry spot ask=73812.1, future bid=73955.9, expected_net_return=
  -0.0007469851510475881110930647630, reason
  `expected_net_return_not_positive`. Actuals artifact ID 11346154209.
- 2026-10-05: Funding optimistic-horizon run 37312306663 scanned all 30
  September daily entries at a 30-day horizon using real official funding
  history and the production economics formula with zero slippage/infinite
  liquidity. 27/30 optimistic returns were positive, but 0/30 reached the
  deterministic reference threshold of 0.005. Best entry was 2026-09-20 with
  optimistic_net_return=0.001984296236776657714285714286. This is an upper
  bound before real L2 impact and establishes a product target decision gate;
  it is not permission to lower the reference target.
- 2026-10-05: querying the expired `BTC-USDT-260626` through current
  `/api/v5/public/instruments` returns OKX 51001. Historical derivative
  metadata therefore cannot be reconstructed from the current-instrument API.
  Official OKX expiry-futures documentation states BTCUSDT expiry futures use
  face value 0.01 BTC and contract multiplier 1; this rule must be preserved as
  explicit provenance when used for expired-contract normalization, alongside
  delivery-history evidence. It must not be presented as a recovered historical
  instrument row.

## Deviations and discoveries

None.

## Resume from here

Finish the June-1 full-day Cash-and-Carry entry scan and record its qualification
distribution. Then commit a compact, derived historical smoke fixture (raw
archives remain out of git) and add an offline historical smoke CI that verifies
checksums, provenance, qualification semantics, and machine-readable actuals.
After all non-target implementation is complete, stop at the historical target
semantics decision gate; do not change existing reference return targets.

## Completion

Final implementation commit:
CI run:
Historical evidence artifact:
Remaining unassessed items:
