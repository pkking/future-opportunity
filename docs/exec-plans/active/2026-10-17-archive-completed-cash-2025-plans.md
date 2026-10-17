# Archive completed Cash 2025 Q3/Q4 execution plans

Issue: #83
Status: IMPLEMENTING
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
- [ ] All six tracked Cash 2025 plans move to `completed/` with
      status COMPLETED, preserved historical evidence and final
      source/PR/CI checkpoints.
- [ ] Superseded `Resume from here` sections cannot trigger a
      repeated source job or promotion.
- [ ] Each completed plan meets the exact plan integrity requirements:
      headings, checklists checked, Final commit, CI run, and explicit
      Remaining unassessed items.
- [ ] Archive PR is documentation-only; no changes to sources, fixtures,
      tests, workflows or runtime.
- [ ] Final PR-head CI (plan integrity/static/code/API/E2E) and
      Historical Smoke success; post-merge main CI verified.
- [ ] This plan also moves to completed after archival PR merges;
      Issue #83 closed only when its final completion PR merges.

## Implementation slices
- [ ] 1. Reconcile six plans with immutable Q3/Q4 and merge evidence.
- [ ] 2. Archive six plans by exact path moves and mark superseded
      recovery and blockers, preserving evidence logs.
- [ ] 3. Verify Git diff and canonical completed-plan metadata,
      then run final PR-head checks.
- [ ] 4. After archive PR merge, finalize this plan in `completed/`,
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
Read Issue #83, current main, and this plan. Archive exactly the six
previously identified completed Cash Q3/Q4 plans. All original source
logs are historical; status and recovery must reflect final
promotion PR #82, merged `ad4790c0`, post-merge CI and
the closed status of Issue #69. Do not change `AGENTS.md` or
strategy gates.

## Completion
Pending archive and follow-up plan completion PR.
