# Funding historical corpus promotion Wave 003

Issue: #39
Status: READY_FOR_REVIEW

## Objective

Review and merge the exact Funding historical corpus campaign `preregistered-review-003-wave-001` produced by workflow_dispatch run 37710381194 without changing source selection or evidence semantics.

## Acceptance criteria

- [x] The dispatched planner handoff resolves the exact Wave 003 campaign.
- [x] All 12 Funding compact artifacts are digest-verified and staged atomically.
- [x] Offline corpus validation and historical smoke inside the promotion workflow succeed.
- [x] Staging projects 32 distinct pinned Funding days and 5 Cash-and-Carry days.
- [ ] Review PR final head passes all repository required checks.
- [ ] Review PR final head passes Historical Backtest Smoke.
- [ ] Review PR is merged.
- [ ] Main verifies 32 distinct pinned Funding days after merge.
- [ ] ADR-0007 Stage-2 eligibility is evaluated from the merged main state.

## Implementation slices

- [x] Execute exact Wave 003 promotion via `Promote Planned Historical Wave`.
- [x] Create the review branch from workflow evidence.
- [x] Attach Issue/Plan governance metadata before opening the PR.
- [ ] Verify the final review head and merge.
- [ ] Verify post-merge pinned corpus count and Stage-2 eligibility.

## Verification matrix

| Evidence | Expected |
| --- | --- |
| Promotion workflow run | 37710381194 succeeds |
| Campaign | `preregistered-review-003-wave-001` |
| Promotion evidence artifact | 11521527455, sha256:b756bfba10c9028a89c691907dc33c5a71731398dc85c074fee0499d12c07793 |
| Funding days after staging | 32 |
| Cash days after staging | 5 |
| Required CI | all final-head checks successful |
| Historical Backtest Smoke | successful |
| Post-merge corpus | Funding=32 distinct pinned days |
| ADR-0007 | Funding meets >=30-day Stage-2 target-design eligibility threshold |

## Resume from here

Open the review PR from branch `historical-corpus-campaign/preregistered-review-003-wave-001-37710381194-1` with Issue #39 and this plan in the PR body. Do not merge until every required check and Historical Backtest Smoke is green on the final head. Then archive this plan as completed, validate the archival head, merge, verify Funding=32 on main, evaluate ADR-0007 Stage-2 eligibility, and close Issue #39.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: final-head CI, merge, post-merge Funding=32 verification, and ADR-0007 eligibility evaluation
