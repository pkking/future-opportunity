# 2026-10-08-preregister-cash-2025-cohorts

Issue: #61
Status: READY_FOR_REVIEW
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Pre-register 12 entry-market dates in each newly verified 2025 Cash quarterly expiry cohort using deterministic availability-only selection, before any target date strategy return evaluation.

## Frozen source baseline

- Prior source work: Issue #59 / PR #60, main b03111bda5ada6812a2ae7457a6f335838aaeed5.
- Official catalog run 37754484440, artifact 11539801691, digest d1f34518fc4821d4183eb4d009722d6ec7264cc02ac4e5f12172fa16e3ae2da6.
- Q3 source coverage 87/87 days, window 2025-07-01..2025-09-25.
- Q4 source coverage 90/90 days, window 2025-09-27..2025-12-25.
- SPOT fixed-date catalog identities and both future exit archive members verified.
- Actual 00:15 SPOT/FUTURES snapshots, costs and realized returns remain unassessed.
- Main Cash 30 pinned, Funding 32 pinned. No Cash pinned days in 2025.

## Selection contract

- Availability-only deterministic even rank buckets, policy availability-even-rank-v1.
- Exact quota: 12 per quarter; immutable after outcome observation.
- No economically attractive date filtering, no missing date backfill after observing PnL.
- Q3 quarter future BTC-USDT-250926, planned exit 2025-09-25T00:15:00+00:00.
- Q4 quarter future BTC-USDT-251226, planned exit 2025-12-25T00:15:00+00:00.
- Entry: 00:15:00 UTC at each selected market day.
- Selection control artifact is read-only and explicitly not promotion permission.

## Acceptance criteria

- [x] Two deterministic, immutable quarter-specific selections use official pre-outcome source coverage.
- [x] Exactly 12/12 unique dates per quarter, 24 total distinct, no 2026 pinned overlap.
- [x] Full replay matches versioned dates and recorded selection evidence hashes.
- [x] Q3/Q4 contract and pre-expiry exit match prior human-approved quarter-aligned rule.
- [x] Read-only workflow publishes exact selection control artifact and no acquisition side effects.
- [x] Unit tests cover replay, boundary dates, drift and disjointness.
- [ ] All 5 required CI and Historical Smoke pass at PR review/final heads.
- [ ] Completed plan, squash merge, main verification and issue closure.

## Implementation slices

- [x] 1. Create issue, branch and plan anchored to official 2025 source evidence.
- [x] 2. Freeze versioned pre-selection JSON with exact quarter windows and selected days.
- [x] 3. Validate deterministic replay and add automated immutable selection artifact workflow.
- [ ] 4. Run CI/Smoke, archive, verify final head, merge and verify main.

## Verification matrix

| Gate | Expected |
|---|---|
| Q3 population | 87 ready days |
| Q4 population | 90 ready days |
| New Q3 selected | 12 |
| New Q4 selected | 12 |
| Total new selection | 24 |
| Source validation | run 37754484440, artifact 11539801691 |
| Historical economics inspected | false |
| Acquisition / promotion | false |
| Existing main pinned counts | Cash 30 / Funding 32 |
| Economics gate | disabled |
| CI & Smoke | pending PR review head |

## Resume from here

Selection control artifact from run 37755705789, ID 11539833591, digest sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74; Q3 replay SHA 3449f56506669a382dbc6c7290d762a00d518a84bebc9530eb904c03e3ab70cd; Q4 SHA 97c3b6c4f296e5819055eace56b5c396c317e285051ea142be2dcb8799073f8b. Exact 12+12 dates and source are committed. Open governed PR and verify final-head CI/Smoke before merge. Once merged, separate reviewed acquisition preparation must validate 00:15 source data for all 24 dates; do not replace failed/rejected outcomes.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: exact selected date freeze, evidence, tests and governed merge
