# Funding historical corpus promotion Wave 003

Issue: #39
Status: COMPLETED

## Objective

Review the exact Funding historical corpus campaign `preregistered-review-003-wave-001` produced by workflow_dispatch run 37710381194 and bring its review PR to a ruleset-clean merge-ready state without changing source selection or evidence semantics.

## Acceptance criteria

- [x] The dispatched planner handoff resolves the exact Wave 003 campaign.
- [x] All 12 Funding compact artifacts are digest-verified and staged atomically.
- [x] Offline corpus validation and historical smoke inside the promotion workflow succeed.
- [x] Staging projects 32 distinct pinned Funding days and 5 Cash-and-Carry days.
- [x] PR #40 review head passes all five repository required checks.
- [x] PR #40 review head passes Historical Backtest Smoke.
- [x] PR #40 is merge-ready under the repository ruleset.

## Implementation slices

- [x] Execute exact Wave 003 promotion via `Promote Planned Historical Wave`.
- [x] Create the review branch from workflow evidence.
- [x] Attach Issue/Plan governance metadata before opening the PR.
- [x] Verify the review head with repository CI and Historical Backtest Smoke.
- [x] Archive the execution evidence before merge.

## Verification matrix

| Evidence | Result |
| --- | --- |
| Promotion workflow run | 37710381194 |
| Campaign | `preregistered-review-003-wave-001` |
| Promotion evidence artifact | 11521527455, sha256:b756bfba10c9028a89c691907dc33c5a71731398dc85c074fee0499d12c07793 |
| Funding days after staging | 32 |
| Cash days after staging | 5 |
| PR | #40 |
| Required CI | run 37710505749: 5/5 successful |
| Historical Backtest Smoke | run 37710505751: successful |

## Resume from here

PR #40 is ready for final archival-head validation. Keep Issue #39 open until merge. After this completed plan becomes the canonical PR plan and the active plan is removed, require all checks on the final head to succeed, merge #40, verify main contains 32 distinct pinned Funding days, evaluate ADR-0007 Stage-2 target-design eligibility from merged main, then close Issue #39.

## Completion

Final commit: 5e7689f80304cdee73c65ece44423ec182fa332a
CI run: 37710505749 (all five required jobs successful); Historical Backtest Smoke 37710505751 successful
Remaining unassessed items: post-merge main verification of Funding=32 and ADR-0007 eligibility evaluation; tracked by Issue #39 lifecycle
