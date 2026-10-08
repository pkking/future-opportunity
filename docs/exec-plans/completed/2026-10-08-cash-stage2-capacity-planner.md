# 2026-10-08-cash-stage2-capacity-planner

Issue: #45
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Determine whether already-published OKX module-4 FUTURES L2 history can supply the 25 additional Cash-and-Carry pinned days needed to move the strategy from 5 to 30 days, and produce a deterministic pre-registration candidate set without acquiring or promoting data.

## Current facts

- Cash main corpus contains 5 distinct pinned days.
- ADR-0007 requires 30 distinct pinned days for Stage-2 proposal eligibility.
- Capacity run 37714282539 scanned 2026-01-01 through 2026-06-26.
- All 177 scanned dates have exactly one canonical module-4 BTC-USDT FUTURES archive; 0 missing, 0 ambiguous, 0 query errors.
- Excluding 5 already-pinned Cash dates leaves 172 unique-ready unpinned days.
- The planner froze exactly 25 dates using availability-only even-rank-bucket selection.
- Corrected contract discovery run 37714773301 succeeded for all 25 selected dates.
- Historical chain archives legitimately contain multiple expiry futures on early dates; the previous discovery implementation failed because it assumed exactly one .data member per archive.
- BTC-USDT-260626 is present on all 25 frozen dates; BTC-USDT-260327 is present on the 12 selected dates through 2026-03-21.
- Contract/holding-period selection remains explicit and is not decided by this task.

## Constraints and invariants

- Read-only source discovery only.
- No automatic acquisition, promotion, or corpus mutation.
- Keep module-4 / FUTURES / BTC-USDT-family evidence semantics.
- Exclude dates already pinned as Cash.
- Select candidate dates using availability only; never inspect returns before selection.
- Candidate selection must be deterministic and reproducible.
- Existing fixed 28-date readiness monitor remains unchanged.
- Multi-contract discovery must preserve candidates rather than silently choosing one.

## Acceptance criteria

- [x] Planner computes remaining days to the 30-day target from corpus state.
- [x] Planner distinguishes unique-ready, missing, ambiguous, and query-error dates.
- [x] Planner scans a backward historical window ending at the known publication frontier.
- [x] Already-pinned Cash dates are excluded.
- [x] Capacity is sufficient and planner emits exactly 25 deterministic pre-registration candidates.
- [x] Selection is spread across the usable interval rather than cherry-picked by economics.
- [x] Evidence is bound to exact workflow run/artifact/digest and frozen pinned-date context.
- [x] Workflow uploads a read-only capacity-plan artifact and summary.
- [x] Unit tests cover capacity, insufficiency, ambiguous/error states, deterministic selection, and multi-contract archive enumeration.
- [x] Exact 25-day selection is versioned before contract discovery.
- [x] Corrected discovery succeeds for 25/25 frozen dates without choosing a contract.
- [x] Full repository CI and Historical Smoke pass.

## Implementation slices

- [x] 1. Create Issue/branch/plan and inspect existing readiness/frontier code.
- [x] 2. Implement pure capacity planning and deterministic date selection.
- [x] 3. Implement live read-only OKX catalog probe script.
- [x] 4. Add workflow and tests.
- [x] 5. Prove already-published history has enough capacity and freeze exact 25 dates.
- [x] 6. Fix historical multi-contract discovery and preserve all candidate futures.
- [x] 7. Run exact discovery for all 25 frozen dates and record contract coverage.
- [x] 8. Run PR CI/Smoke and archive; merge after final archival-head validation.
- [ ] 9. Start a separate acquisition-wave task only after explicit contract/holding-period policy approval.

## Verification matrix

| Gate | Result |
|---|---|
| Current Cash pinned count | 5 |
| Target | 30 |
| Needed | 25 |
| Canonical source | module 4 / FUTURES / BTC-USDT / daily |
| Capacity run | 37714282539 |
| Capacity artifact | 11522419694 / sha256:48c202548ebeb98a4531c6a11cdd4ced61305f32754ba689fb45225a6a4a2da1 |
| Scan | 177/177 unique-ready |
| Unique-ready unpinned | 172 |
| Frozen selection | 25 dates |
| Discovery run | 37714773301 |
| Discovery result | 25/25 success |
| BTC-USDT-260626 coverage | 25/25 |
| BTC-USDT-260327 coverage | 12/25 |
| Acquisition side effects | none |
| CI / Smoke | CI 37715376097: 5/5 success; Historical Smoke 37715376138: success |

## Decision gate

Acquisition requires an explicit future/expiry/exit template. Evidence supports at least two source-valid policies:

1. fixed `BTC-USDT-260626` across all 25 dates;
2. quarter-aligned `BTC-USDT-260327` for the 12 dates through 2026-03-21 and `BTC-USDT-260626` for the 13 later dates.

This task must not choose between them because that changes holding-period semantics.

## Evidence log

- 2026-10-08: capacity run 37714282539 proved 172 unique-ready unpinned days are already published.
- 2026-10-08: exact 25 dates frozen in `docs/historical-acquisition-plans/cash-stage2-30day-wave-001.json` before contract discovery.
- 2026-10-08: initial discovery run 37714545325 exposed the invalid one-member archive assumption.
- 2026-10-08: discovery was corrected to preserve multiple expiry-future candidates.
- 2026-10-08: corrected run 37714773301 completed 25/25 discovery jobs successfully.
- 2026-10-08: contract coverage: 260109=1, 260116=2, 260123=2, 260130=4, 260227=8, 260327=12, 260626=25.
- 2026-10-08: detailed evidence and decision options recorded in `docs/research/cash-stage2-source-capacity-and-contract-options.md`.

## Resume from here

PR #46 passed review-head CI/Smoke. Keep Issue #45 open until the archival head is fully green and the PR merges. After merge, stop at the explicit contract/holding-period decision boundary before creating an acquisition wave.

## Completion

Final commit: 0205e93de93787b1c0231dee70ed0a4b37f61492
CI run: 37715376097 (all five required jobs successful); Historical Backtest Smoke 37715376138 successful
Remaining unassessed items: archival-head validation, merge, and human contract/holding-period policy choice
