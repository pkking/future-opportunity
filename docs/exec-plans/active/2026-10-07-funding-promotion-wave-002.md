# Funding historical corpus promotion Wave 002

Issue: #38
Status: READY_FOR_REVIEW

## Objective

Review and merge the exact Funding historical corpus campaign `preregistered-review-002-wave-001` produced by workflow_dispatch run 37615149834 without changing source selection or evidence semantics.

## Acceptance criteria

- [x] The dispatched planner handoff resolves the exact Wave 002 campaign.
- [x] All 12 Funding compact artifacts are digest-verified and staged atomically.
- [x] Offline corpus validation and historical smoke inside the promotion workflow succeed.
- [ ] PR #37 final head passes all repository required checks.
- [ ] PR #37 final head passes Historical Backtest Smoke.
- [ ] PR #37 is merged.
- [ ] Main verifies 20 distinct pinned Funding days after merge.

## Implementation slices

- [x] Execute exact Wave 002 promotion via `Promote Planned Historical Wave`.
- [x] Create the review branch and PR from workflow evidence.
- [x] Attach PR governance metadata required by agent plan integrity.
- [ ] Verify the final review head and merge.
- [ ] Verify the post-merge pinned corpus count.

## Verification matrix

| Evidence | Expected |
| --- | --- |
| Promotion workflow run | 37615149834 succeeds |
| Campaign | `preregistered-review-002-wave-001` |
| Funding days after staging | 20 |
| Cash days after staging | 5 |
| PR | #37 |
| Required CI | all final-head checks successful |
| Historical Backtest Smoke | successful |
| Post-merge corpus | Funding=20 distinct pinned days |

## Resume from here

PR #37 is open from branch `historical-corpus-campaign/preregistered-review-002-wave-001-37615149834-1`. Re-run/observe CI after this plan metadata commit. Do not merge until every required check and Historical Backtest Smoke is green on the final head. Then merge, verify Funding pinned count is 20 on main, archive this plan as completed, and close Issue #38.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: final-head CI, merge, and post-merge pinned count
