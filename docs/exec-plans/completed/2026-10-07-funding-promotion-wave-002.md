# Funding historical corpus promotion Wave 002

Issue: #38
Status: COMPLETED

## Objective

Review the exact Funding historical corpus campaign `preregistered-review-002-wave-001` produced by workflow_dispatch run 37615149834 and bring its review PR to a ruleset-clean merge-ready state without changing source selection or evidence semantics.

## Acceptance criteria

- [x] The dispatched planner handoff resolves the exact Wave 002 campaign.
- [x] All 12 Funding compact artifacts are digest-verified and staged atomically.
- [x] Offline corpus validation and historical smoke inside the promotion workflow succeed.
- [x] PR #37 final review head passes all five repository required checks.
- [x] PR #37 final review head passes Historical Backtest Smoke.
- [x] PR #37 is merge-ready under the repository ruleset.

## Implementation slices

- [x] Execute exact Wave 002 promotion via `Promote Planned Historical Wave`.
- [x] Create the review branch and PR from workflow evidence.
- [x] Attach Issue/Plan governance metadata required by agent plan integrity.
- [x] Verify the review head with repository CI and Historical Backtest Smoke.
- [x] Archive the execution evidence before merge.

## Verification matrix

| Evidence | Result |
| --- | --- |
| Promotion workflow run | 37615149834 |
| Campaign | `preregistered-review-002-wave-001` |
| Promotion evidence artifact | 11478628710, sha256:50c8f8656b41ab5350b4b8fde4c1ca96747463af211f160472948b79dc9c05bb |
| Funding days after staging | 20 |
| Cash days after staging | 5 |
| PR | #37 |
| Required CI | run 37615597447: 5/5 successful |
| Historical Backtest Smoke | run 37615597424: successful |

## Resume from here

PR #37 is ready for its final archival-head validation. Keep Issue #38 open until the PR merges. After this completed plan is the canonical PR plan and the active plan is removed, require all checks on that final head to succeed, merge #37, then verify main reports 20 distinct pinned Funding days. Only then close Issue #38 and proceed to Wave 003.

## Completion

Final commit: e4619815612704001cad8e5bf6743220df8784be
CI run: 37615597447 (all five required jobs successful); Historical Backtest Smoke 37615597424 successful
Remaining unassessed items: post-merge main-branch verification of Funding=20; tracked by Issue #38 lifecycle
