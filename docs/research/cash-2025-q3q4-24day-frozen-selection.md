# Cash 2025 Q3/Q4: frozen 24-day pre-registration

Status: **selection frozen before economic outcome evaluation**; read-only control, not acquisition or corpus promotion.

## Exact source and selection evidence

- Historical source readiness: Issue #59, PR #60; source workflow [37754484440](https://github.com/pkking/future-opportunity/actions/runs/37754484440), artifact `11539801691`, sha256:`d1f34518fc4821d4183eb4d009722d6ec7264cc02ac4e5f12172fa16e3ae2da6`.
- Frozen selection file: `docs/historical-acquisition-plans/cash-2025-q3q4-24day-preregistration-v1.json`.
- Selection workflow: [37755705789](https://github.com/pkking/future-opportunity/actions/runs/37755705789), artifact `11539833591`, sha256:`f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74`.
- Deterministic policy: `availability-even-rank-v1`, 12 dates per quarter, no excluded market dates, calendar availability only, no return data input.
- 2025 Q3 availability: 87/87 daily FUTURES archives; control evidence SHA `3449f56506669a382dbc6c7290d762a00d518a84bebc9530eb904c03e3ab70cd`.
- 2025 Q4 availability: 90/90 daily FUTURES archives; control evidence SHA `97c3b6c4f296e5819055eace56b5c396c317e285051ea142be2dcb8799073f8b`.

## Selected date control

| 2025 Q3, BTC-USDT-250926 | 2025 Q4, BTC-USDT-251226 |
|---|---|
| 2025-07-04 | 2025-09-30 |
| 2025-07-11 | 2025-10-08 |
| 2025-07-19 | 2025-10-15 |
| 2025-07-26 | 2025-10-23 |
| 2025-08-02 | 2025-10-30 |
| 2025-08-09 | 2025-11-07 |
| 2025-08-17 | 2025-11-14 |
| 2025-08-24 | 2025-11-22 |
| 2025-08-31 | 2025-11-29 |
| 2025-09-07 | 2025-12-07 |
| 2025-09-15 | 2025-12-14 |
| 2025-09-22 | 2025-12-22 |

Planned cash entry is `00:15 UTC`, using the matching entry-quarter future. Planned pre-expiry exit is `2025-09-25T00:15:00Z` (Q3) or `2025-12-25T00:15:00Z` (Q4). Official contract timestamp and complete 00:15 order books **must still be verified during preparation**.

## What is and is not approved

The controlled sample is a study input. It is not a set of validated complete historical cases. The evidence artifact explicitly sets `acquisition_approved=false` and `promotion_approved=false`. Before acquisition and promotion:

1. Verify each selected date's exact target future contract archive member, SPOT entry/exit archive and actual 00:15 bid/ask snapshots with source checksums.
2. Preserve the full 12+12 selection, including unavailable or economically rejected cases; no post-hoc date replacement.
3. Build a provenance bridge using immutable selection artifact ID/digest and replayable `AvailabilitySelectionRequest` per quarter.
4. Prepare each quarter as an independent batch and inspect sample actuals, rejection counts, realized evidence completeness, and missingness before a human-governed promotion PR.
5. Do not interpret the 24 dates as 24 independent realized-return trials. They add **two expiry cohorts** (from 2 to at most 4), but each cohort shares expiry/exit and overlapping holding-period exposure.

All existing 30 Cash and 32 Funding pinned historical cases remain unchanged. Stage-2 economic return/qualification gates remain disabled.
