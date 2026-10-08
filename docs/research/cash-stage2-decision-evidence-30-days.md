# Cash Stage-2: 30-day decision-quality evidence

Status: analysis complete for current pinned historical corpus; **Cash Stage-2 activation is not approved**. No numerical historical economics gate is active.

## Evidence chain

- Corpus promotion: PR #52, merge `a5124f804a603731a55125563959e1c6811a10d8`.
- Main Historical Backtest Smoke: [37747210353](https://github.com/pkking/future-opportunity/actions/runs/37747210353), completed successfully.
- Distribution evidence: artifact ID `11536670411`, artifact name `historical-backtest-smoke-evidence`, digest `sha256:762ef5d6f7f10fc4ccc37e75cf722012af65ad91c383fb260e97c33aca033950`, member `corpus-distribution.json`.
- Inputs: 30 distinct Cash entry-market days, with one frozen case per day. Twenty-five of the new days were selected before outcomes were observed using availability-only even-rank buckets.
- Active historical gate: `provenance_and_semantics`.
- `stage2_decision_quality.enabled_strategies` remains `["funding-carry"]`; `economics_gate=disabled`.

## Decision-quality evidence summary

| Metric | Cash-and-Carry | Funding Carry | Semantics |
|---|---:|---:|---|
| Pinned days / cases | 30 | 32 | One frozen case per entry-market day |
| Pre-registered days | 27/30 (90%) | 29/32 (90.625%) | Legacy-untracked remain in denominators |
| Expected-net-return assessed | 30/30 | 32/32 | Covers all pinned cases |
| Qualified cases | 8 | 0 | Cash pinned-case qualification rate = 26.6667% |
| Rejected cases | 22 | 32 | Cash reason counts can overlap |
| Qualified with fully assessed realized return | 8/8 | 0/0 | Only conditional realized cases count |
| Minimum 30-day evidence | met | met | Proposal eligibility, not automatic policy activation |
| Stage-2 human enablement | **not approved** | accepted under ADR-0008 | Authorization is separate from evidence sufficiency |
| Numerical economics gate | disabled | disabled | No profitability, win-rate or frequency threshold |

Cash rejected reason frequencies: `expected_net_return_not_positive=22`, `future_not_in_contango=1`. One case has *both* reasons; 23 total reason occurrences therefore represent **22** unique rejected cases.

### Cash expected-net-return distribution — all 30 cases

All figures below are fractional per-case returns, not percentage-point rates.

| Statistic | Fractional return | Approx. percent |
|---|---:|---:|
| Minimum | -0.00170610486147714453 | -0.17061% |
| P25 | -0.00095979852938462478 | -0.09598% |
| Median | -0.00066990055002672364 | -0.06699% |
| Mean | -0.00025817908635050432 | -0.02582% |
| P90 | 0.00162750151882358122 | +0.16275% |
| Maximum | 0.00284845182531102307 | +0.28485% |

### Cash realized-net-return distribution — **only 8 qualified and fully assessed cases**

| Statistic | Fractional return | Approx. percent |
|---|---:|---:|
| Minimum | 0.00075299589652752969 | +0.07530% |
| P25 | 0.00113775899943055379 | +0.11378% |
| Median | 0.00160812021204621480 | +0.16081% |
| Mean | 0.00178898646935635615 | +0.17890% |
| P90 | 0.00281184976275558815 | +0.28118% |
| Maximum | 0.00310278477621142383 | +0.31028% |

**The 22 rejected days are not counted as zero-realized-return days.** The realized distribution is conditional on entry qualification and sufficient close evidence. Eight observed positive closed-case returns do not establish a stable annual return or an out-of-sample production performance estimate.

## By expiry cohort and holding horizon

| Historical expiry | Pinned | Pre-registered | Qualified | Rejected | Entry-to-exit holding calendar days (min / median / max) |
|---|---:|---:|---:|---:|---|
| BTC-USDT-260327 / 2026-03-27 | 12 | 12 | 5 | 7 | 5 / 43.5 / 81 |
| BTC-USDT-260626 / 2026-06-26 | 18 | 15 | 3 | 15 | 2 / 31 / 89 |

- Q1 qualified dates: 2026-01-04, 01-11, 01-18, 01-25, 01-31.
- Q2 qualified dates: 2026-03-28, 04-03, 04-10.
- Each cohort closes on a common pre-expiry date. Cases within a cohort have **overlapping holding intervals, common expiry risk, and serially correlated market exposures**. Treating all eight as eight independent investment trials would be misleading.
- Holding horizon varies substantially both within and between cohorts; direct comparisons of per-case returns conflate cost/carry exposure with length of holding. Report actual holding-day distributions; do **not** silently annualize using a short-period extrapolation.
- The evidence sample does not enumerate all intra-day candidate opportunities. Market-wide opportunity arrival rate is **unassessed**, not 8/30.
- Selection is not a random, independent and identically distributed sampling of returns; not all markets or contract structures are covered. Treat the two expiry cohorts as exploratory evidence.

## Why 30 days matters — and what it does not establish

The Cash evidence meets the already accepted ADR-0008 **factual evidence prerequisites** (>=30 distinct pinned days, >=80% pre-registered, all expected net returns assessed). Its eight qualified cases also have complete, recorded conditional realized-return evidence. However, ADR-0008 human approval is Funding-specific. A machine field `evidence_requirements_met=true` must not be conflated with `enabled=true` or `decision_quality_ready=true`.

It does **not** establish statistical independence, robustness across regimes and maturities, or a numerical economics threshold. The preferred >=90-day threshold-freezing evidence level has not been reached, and there are only two common expiry cohorts.

## Recommendation and next decision

1. **Propose** expanding the already accepted Stage-2 *decision-quality observability* framework to Cash, without activating economic thresholds. This requires explicit approval under the Cash-specific ADR proposal.
2. Keep `provenance_and_semantics` as the active historical acceptance gate for both strategies.
3. Prioritize additional pre-registered Cash evidence across **more non-overlapping expiry cohorts and multiple entry-to-expiry horizon buckets**, rather than treating 8/8 positive realized observations as sufficient.
4. If later studying an economic gate, predefine the statistical unit (expiry cohort vs market day), horizon normalization, uncertainty treatment, out-of-sample validation, and the minimum qualified cohort evidence. No threshold is set here.

## Reproduce

```bash
uv run python scripts/report_historical_corpus_distribution.py \
  --output artifacts/historical-smoke/corpus-distribution.json
```

Read `strategies.cash-and-carry`, `stage2_decision_quality.strategies.cash-and-carry`, and `cash_stage2_expiry_horizon_evidence`. Both unit and historical smoke tests enforce the evidence/enablement separation and cohort arithmetic.
