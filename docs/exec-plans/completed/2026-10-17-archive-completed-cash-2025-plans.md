# Archive completed Cash 2025 Q3/Q4 execution plans

Issue: #83
Status: COMPLETED
Owner: agent
Started: 2026-10-17

## Objective
Make the repository's active-work view truthful and resumable following
the human-approved completion of Issue #69. Retain the exact historical
source and CI evidence while archiving six completed Cash Q3/Q4 plans.

## Non-goals
No change to market-source inputs, sampling, sample data, backtests,
strategy business semantics, ADR, economics gates, or live trading.
No new historical acquisition or promotion.

## Current facts
- Issue #69 closed/completed on 2026-10-17 after PR #82.
- Main at start `ad4790c0c7ec785eb2de9d53704e154515451001`.
- Main [CI 39023534155](https://github.com/pkking/future-opportunity/actions/runs/39023534155)
  and [Historical Smoke 39023534123](https://github.com/pkking/future-opportunity/actions/runs/39023534123)
  both success.
- Validated corpus: Cash 54, Funding 32, 24 newly pinned frozen
  2025 Q3/Q4 dates from 2025-09-26/2025-12-26 expiry futures,
  Q3 run 39016938121 and Q4 run 39018358844.
- Six Cash plans remain under `active/` with pre-run blockers,
  obsolete operator commands and some unchecked decision gates.
  This is documentation drift, not outstanding source failure.

## Acceptance criteria
- [x] All six tracked Cash 2025 plans move to `completed/` with
      status COMPLETED, preserved historical evidence and final
      source/PR/CI checkpoints.
- [x] Superseded `Resume from here` sections cannot trigger a
      repeated source job or promotion.
- [x] Each completed plan meets the exact plan integrity requirements:
      headings, checklists checked, Final commit, CI run, and explicit
      Remaining unassessed items.
- [x] Archive PR is documentation-only; no changes to sources, fixtures,
      tests, workflows or runtime.
- [x] Final PR-head CI (plan integrity/static/code/API/E2E) and
      Historical Smoke success; post-merge main CI verified.
- [x] This plan also moves to completed after archival PR merges;
      Issue #83 closed only when its final completion PR merges.

## Implementation slices
- [x] 1. Reconcile six plans with immutable Q3/Q4 and merge evidence.
- [x] 2. Archive six plans by exact path moves and mark superseded
      recovery and blockers, preserving evidence logs.
- [x] 3. Verify Git diff and canonical completed-plan metadata,
      then run final PR-head checks.
- [x] 4. After archive PR merge, finalize this plan in `completed/`,
      rerun CI, and close Issue #83.

## Verification matrix
| Check | Expected | Status |
|---|---|---|
| Active/completed paths | Six moves, no missing content | Pending |
| Plan validator | No malformed completed plans | Pending |
| Scope | Documentation-only | Pending |
| CI | Static, code, API, E2E, plan integrity | Pending |
| Historical smoke | Offline replay | Pending |
| Post-merge main | Main CI success | Pending |

## Decision gates
No product decision required. This is a faithful evidence archival
task. Never close a real pending research item solely because an
earlier preparation issue is complete.

## Resume from here

ARCHIVED. Six previous Cash 2025 plans are now in completed/.
Original PR #84 merged 87a18abf3e587398d2219c0a1dab9a22646042c0,
PR CI 39026990958 SUCCESS, historical smoke 39026990964 SUCCESS,
post-merge main CI 39027048794 SUCCESS. There are no stale Cash
2025 plans in active/. Research resumes independently under open
Issue #85 (Funding market regimes) and #86 (Cash expiry diversity).

## Completion

Final commit: 87a18abf3e587398d2219c0a1dab9a22646042c0 (PR #84).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39026990958 (SUCCESS).
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/39026990964 (SUCCESS).
Post-merge main CI: https://github.com/pkking/future-opportunity/actions/runs/39027048794 (SUCCESS).
Remaining unassessed items: Open research Issues #85 and #86, preferred
90-day corpus coverage, account MarginSafety, VenueExposure, separately
approved future economics thresholds and live trading. None is part
of the completed documentation-archival issue.
