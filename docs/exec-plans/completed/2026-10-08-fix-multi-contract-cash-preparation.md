# 2026-10-08-fix-multi-contract-cash-preparation

Issue: #49
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Make Cash historical fixture preparation support OKX module-4 FUTURES chain archives that contain multiple expiry-contract .data members, selecting the exact approved future by instrument ID while preserving legacy single-member behavior.

## Failure evidence

- Q1 preparation run: 37730394342
- Failed job: 113158075740
- Case: 2026-01-11 / BTC-USDT-260327
- Error: historical L2 archive must contain exactly one .data member
- Discovery had already verified that BTC-USDT-260327 exists in the same archive.

## Constraints

- Do not change the frozen 25 Cash dates.
- Do not change the approved quarter-aligned policy.
- Selection must be by exact expected instrument identity, not first-match order.
- Missing or duplicate matching members must fail closed.
- Existing single-member SPOT and derivative archives must remain compatible.
- No corpus mutation or promotion in this task.

## Acceptance criteria

- [x] Shared OKX L2 adapter can select one exact archive member from a multi-member archive.
- [x] Multi-member FUTURES archive selects BTC-USDT-260327 when requested.
- [x] A missing expected instrument fails closed.
- [x] Duplicate members for the same expected instrument fail closed.
- [x] Legacy single-member archive behavior remains valid.
- [x] Cash fixture provenance records the exact selected archive member.
- [x] Full CI and Historical Smoke pass.

## Implementation slices

- [x] 1. Reproduce and diagnose Q1 preparation failure from workflow logs.
- [x] 2. Implement exact archive-member selection in shared OKX L2 adapter.
- [x] 3. Update Cash preparation provenance to use the same exact selector.
- [x] 4. Add focused unit tests.
- [x] 5. Run review-head CI/Smoke and archive for final-head validation.
- [x] 6. Stop at the post-merge preparation boundary; Q1 requires re-dispatch on fixed main, while Q2 may reuse its successful pre-fix run if complete.

## Verification matrix

| Gate | Expected |
|---|---|
| Exact multi-member selection | expected instrument only |
| Missing target | fail |
| Duplicate target | fail |
| Single-member SPOT | unchanged |
| Single-member FUTURES | unchanged |
| Frozen dates | unchanged |
| Quarter policy | unchanged |
| Required CI | run 37730714500: 5/5 successful |
| Historical Smoke | run 37730714490: successful |

## Resume from here

PR #50 passed review-head CI/Smoke. Validate the archival head and merge. After merge, re-dispatch Q1 on the fixed main revision. Reuse Q2 run 37730401199 only if all 13 Cash jobs and the workflow summary finish successfully.

## Completion

Final commit: 7ac73d582c16f427876cde13b60069573b37f1d8
CI run: 37730714500 (all five required jobs successful); Historical Backtest Smoke 37730714490 successful
Remaining unassessed items: final-head validation, merge, Q1 re-dispatch, and prepared-fixture review
