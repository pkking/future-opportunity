# Stage-2 historical evidence expansion: cohort and ex-ante regime protocol

Status: implementation protocol; source feasibility not yet confirmed.

## Why the next samples are different

Cash has 30 pinned daily cases but only **two expiry cohorts** (2026-03-27 and 2026-06-26). The eight qualified realized-return cases share those settlement regimes and overlapping time exposure. They cannot be treated as eight independent contract-expiry experiments. Funding has 32 pinned days and zero qualified cases; selecting from dates that are known to have profitable funding outcomes would undermine its denominator and decision quality.

The next evidence expansion should increase **independent expiry coverage for Cash**, and **ex-ante observable market regime coverage for Funding**, not optimize observed backtest returns.

## Cash: additional expiry cohorts

Candidate cohort selection is conditional upon official source checks, not a claim of current archive availability.

1. Enumerate distinct BTC-USDT historical quarterly FUTURES expiries besides the existing March/June 2026 expiries. Identify entry and pre-expiry exit windows for each candidate, using the approved quarter-aligned policy. Only include quarters supported by an unambiguous instrument identity, expiry specification and correct archive dates. Do **not** infer that an expiry must be downloadable merely because it falls on the calendar.
2. Probe canonical OKX module-4 L2 FUTURES chain archive and corresponding spot archives at **both entry and exit**, plus relevant market metadata, for each candidate cohort. Log every query and response, inaccessible time range, missing instrument member, and checksum. For settlement-specific evidence, record verified or unassessed status rather than fabricating historical delivery observations.
3. Freeze eligible date and expiry/cohort labels **before** opening expected-net-return, qualification, or realized-return artifacts. Exclude dates already pinned and dates with unknown provenance. Generate cohort-balanced deterministic candidate dates using `plan_stratified_evidence_days`; persist seed, exact population and unavailable/unknown counts.
4. Choose proposed quotas based on verified independent cohort availability and resource cost, not economics. Every missing source/case remains recorded; never substitute dates after looking at outcomes.
5. Acquire immutable compact cases only after complete evidence/provenance review; run planner → explicit promotion → PR CI/Smoke → main verification through existing governed workflow.

**Immediate obstacle:** existing source evidence confirms 177/177 daily FUTURES archives for Jan–Jun 2026, but does not establish complete historical source access to earlier or later quarters. This is a **source coverage investigation**, not an approval to claim ≥3 independent cohorts today.

## Funding: ex-ante regime stratification

The current `systematic-stratified-sha256-v1` sampler partitions calendar dates, not funding-rate/volatility/basis *market states*. Do not label it a market regime sampler.

Before opening historical strategy outcomes, version a new *point-in-time* regime feature source with timestamp, instrument, input window, publication availability and source SHA. Candidate features:

- **Funding sign/magnitude:** use funding rate **known before** the frozen entry timestamp (not subsequent realized funding).
- **Volatility:** rolling lagged price-return volatility from observations available before entry. Disclose measurement window, gaps and instrument.
- **Basis:** lagged spot/perpetual or dated-future basis observed before entry (do not use exit prices).
- **Market direction:** lagged returns computed over a frozen backward-looking interval.

Freeze numeric cut points, missingness treatment and regime priority **before inspecting qualification or realized outcomes**. A feasible first protocol is to use a single primary two/three-level regime label per candidate day; high-dimensional cross-products may create tiny/unobserved strata. Thresholds must come from a designated pre-registration calibration subset or external ex-ante convention, not outcome-optimized backtests.

The selection planner must receive *already frozen labels*, not raw returns or economics. It produces a deterministic digestible mapping of selections, capacities and shortfalls. Every selected and rejected case remains in the pinned-case denominator. Report `qualified / evaluated` as **pinned-case qualification**, never market-wide opportunity arrival.

## Why the code helper is deliberately pure

`src/future_opportunity/backtest/stratified_evidence_selection.py` has **no network calls, price access, expected-return fields, or fixture writes**. It accepts explicit date labels, fixed per-stratum quota and seed; ranks dates with SHA-256; records unavailable/unassessed dates and shortfalls. This is a planning primitive, **not** a claim that feature construction or official historical source verification is implemented. Consumers must store verified population/labels/feature provenance alongside the plan before acquisition.

## Evidence and decision boundaries

| Dimension | Current verified state | Next evidence gate |
|---|---|---|
| Cash pinned days | 30 | Preserve existing 30 |
| Cash expiry cohorts | 2 | Verify at least one **new** eligible expiry cohort before expanding |
| Funding pinned days | 32 | Freeze ex-ante feature provenance and labels before new sampling |
| Funding qualified cases | 0 | No profitable-date selection or economic filtering |
| Stage-2 decision quality | Both accepted | Continue unchanged |
| Economic thresholds | Disabled | Separate human approval required |
| Market-wide arrival rate | Unassessed | Do not infer from pinned cases |

## Proposed execution sequence

1. Complete a **read-only official source feasibility scan for additional Cash expiry cohorts**, with exact data dates and future IDs, and a machine-readable archive catalog evidence artifact.
2. Independently prototype Funding *point-in-time* regime labelling and validate all data timestamps precede entry. Freeze thresholds and input source digests before sample selection.
3. Only once both steps have reliable evidence, author immutable, outcome-blind per-cohort/per-regime sampling manifests.
4. Use current acquisition/promotion workflows; do not introduce another promotion bypass.

This document does not freeze new market data dates, claim third-party archive availability, or authorize any profitability thresholds.
