# 2026-10-07-preregistered-corpus-wave: Promote first pre-registered historical wave

Issue: #8
Status: VERIFYING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Promote the seven pre-registered, previously validated historical compact fixtures from PR #4 onto the current main corpus after PR #3, without losing existing pinned facts or changing Stage-1 economics policy.

## Non-goals

- No live trading.
- No Stage-2 threshold activation.
- No replacement or reselection of sampled dates.
- No changes to strategy economics.

## Current facts

- PR #3 has been merged into main and adds Funding 2026-09-03 plus Cash 2026-06-03.
- PR #4 proposes five Funding dates (2026-01-01, 01-08, 01-13, 01-22, 01-29) and two Cash dates (2026-06-04, 06-08).
- The proposed strategy/date identities are disjoint from current main.
- PR #4 also contains a regression-test update that derives expected pre-registration coverage from indexed manifests rather than assuming zero pre-registered fixtures.

## Acceptance criteria

- [x] Reconcile PR #4 corpus index with latest main, preserving all existing entries.
- [x] Reuse exact validated fixture blobs from the existing PR #4 head.
- [x] Add exactly 5 Funding + 2 Cash new strategy/date identities.
- [x] Preserve the distribution-report test adjustment required by pre-registered fixtures.
- [ ] Agent plan integrity passes.
- [ ] Static, code, API, E2E, and Historical Backtest Smoke pass on the final head.
- [ ] Merge only after all required checks are green.

## Implementation slices

- [x] 1. Reconcile current main corpus with PR #4 proposal.
- [x] 2. Rebuild PR branch from current main using exact proposal fixture blobs.
- [x] 3. Add GitHub Issue/Plan traceability required by the repository contract.
- [ ] 4. Verify final CI and Historical Backtest Smoke.
- [ ] 5. Merge and close Issue #8.

## Verification matrix

| Gate | Expected evidence | Status |
|---|---|---|
| Plan integrity | PR #4 -> Issue #8 -> this plan | pending |
| Static | CI | pending |
| Code | CI | pending |
| API | CI | pending |
| E2E | CI | pending |
| Historical smoke | offline pinned historical replay | pending |

## Decision gates

None. This is a review/promotion of already pre-registered evidence under the existing Stage-1 policy.

## Evidence log

- 2026-10-07: PR #3 merged first, establishing the new corpus baseline.
- 2026-10-07: reconciled current main with PR #4 proposal; new identities are exactly five Funding and two Cash dates. Existing main identities are preserved.
- 2026-10-07: branch reconstruction reuses the existing PR #4 blobs for all proposed fixture files and the previously reviewed distribution-report regression test.
- 2026-10-07: first rebuilt CI used the pre-edit PR event body and failed only the Plan Integrity metadata check; PR body now contains Issue #8 and this plan path, so a fresh synchronize commit is required for a new event snapshot.

## Resume from here

Inspect the CI and Historical Backtest Smoke runs for the rebuilt PR #4 head. If all required checks pass, merge PR #4, verify main CI, close Issue #8, and archive this plan in a follow-up governance change.

## Completion

Final implementation commit: pending
CI run: pending
Historical smoke: pending
Remaining unassessed items: none if all gates pass
