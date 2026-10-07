# 2026-10-07-preregistered-corpus-wave: Promote first pre-registered historical wave

Issue: #8
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Promote the seven pre-registered historical compact fixtures from PR #4 onto the post-PR-#3 corpus baseline without losing existing pinned facts or changing Stage-1 economics policy.

## Non-goals

- No live trading.
- No Stage-2 threshold activation.
- No replacement or reselection of sampled dates.
- No strategy economics changes.

## Current facts

- PR #3 was merged first and established Funding 2026-09-03 plus Cash 2026-06-03.
- PR #4 then added five January Funding dates and Cash 2026-06-04/06-08.
- Current main therefore contains 8 Funding and 5 Cash distinct pinned entry-market days.
- Stage-1 provenance-and-semantics policy remains active.

## Acceptance criteria

- [x] Reconcile PR #4 corpus index with latest main while preserving all entries.
- [x] Reuse exact validated fixture blobs from the original PR #4 evidence.
- [x] Add exactly 5 Funding + 2 Cash new strategy/date identities.
- [x] Preserve the distribution-report regression update required by pre-registered fixtures.
- [x] Agent plan integrity passes.
- [x] Static, Code, API, E2E and Historical Backtest Smoke pass on final PR head.
- [x] Merge only after all required checks are green.

## Implementation slices

- [x] 1. Reconcile current main corpus with PR #4 proposal.
- [x] 2. Rebuild PR branch from current main using exact proposal fixture blobs.
- [x] 3. Add GitHub Issue/Plan traceability.
- [x] 4. Verify final CI and Historical Backtest Smoke.
- [x] 5. Merge and close Issue #8.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Plan integrity | CI 37571625158 | passed |
| Static | CI 37571625158 | passed |
| Code | CI 37571625158 | passed |
| API | CI 37571625158 | passed |
| E2E | CI 37571625158 | passed |
| Historical smoke | 37571625155 | passed |
| Main integration | CI 37571708476 / smoke 37571708501 | passed |

## Decision gates

None. The work remained inside accepted ADR-0007 Stage-1 policy.

## Evidence log

- 2026-10-07: PR #3 merged first as 416b47d97fc99ab7ce10dabfdbcb51ccb97795cb.
- 2026-10-07: rebuilt PR #4 on the new baseline, retaining exact validated fixture blobs.
- 2026-10-07: final PR CI 37571625158 and Historical Smoke 37571625155 passed.
- 2026-10-07: PR #4 merged as d6d325d59ee266a3a13d055b99c0868573843380.
- 2026-10-07: main CI 37571708476 and Historical Smoke 37571708501 passed; Issue #8 closed.

## Deviations and discoveries

The first rebuilt CI saw a stale pre-edit PR event body and failed only Plan Integrity; a synchronization commit created a fresh event snapshot and the full gate then passed.

## Resume from here

Completed. Continue corpus growth from the committed 8 Funding / 5 Cash baseline; Stage 2 remains ineligible until at least 30 distinct pinned days per strategy and a separate approved ADR.

## Completion

Final commit: d6d325d59ee266a3a13d055b99c0868573843380
CI run: https://github.com/pkking/future-opportunity/actions/runs/37571708476
Historical smoke: https://github.com/pkking/future-opportunity/actions/runs/37571708501
Remaining unassessed items: Stage-2 policy intentionally remains unassessed and requires separate approval after sufficient evidence
