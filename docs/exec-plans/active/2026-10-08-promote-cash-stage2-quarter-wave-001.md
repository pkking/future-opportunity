# 2026-10-08-promote-cash-stage2-quarter-wave-001

Issue: #51
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Review and merge the exact frozen Cash Stage-2 25-day historical campaign into the pinned corpus while maintaining reproducible source, selection, contract and CI evidence.

## Authorized evidence and scope

- Planner: run 37745788337, artifact historical-campaign-planner-37745788337, artifact ID 11536165590, SHA256 8b19457239ad9979be44db3bbc333bbb1107a64899678298f4764e44307b4a94.
- Promoted planned-wave dispatch: run 37746589796, campaign cash-stage2-quarter-review-001-wave-001.
- Promotion evidence: artifact historical-campaign-evidence-37746589796, ID 11535639577, SHA256 a0cb9eb8264ac459993341d9810e3ac9fa0ef1953820d5f3cf8836fe746d3305.
- Exact source runs: Q1 37731060921 (12 cases BTC-USDT-260327); Q2 37730401199 (13 cases BTC-USDT-260626).
- Promotion review branch: historical-corpus-campaign/cash-stage2-quarter-review-001-wave-001-37746589796-1.
- Frozen 25 dates: docs/historical-acquisition-plans/cash-stage2-30day-wave-001.json.
- All 25 incoming dates are unique and match the frozen selection exactly.
- This is a historical evidence update, not an economics-gate policy activation.

## Acceptance criteria

- [x] Promotion dispatch matches exact successful Planner run, artifact and wave.
- [x] Planner verifies 25 unique incoming compact fixtures, 0 pinned duplicates.
- [x] Preparation provenance remains tied to frozen availability-even-rank-v1 selection.
- [x] Q1 and Q2 entry/exit contracts follow the accepted quarterly strategy.
- [x] Promotion stages historical fixtures atomically and offline tests pass.
- [x] Staged corpus has 30 distinct Cash days and preserves 32 Funding days.
- [ ] PR with Issue #51 and canonical active execution plan passes all five required checks.
- [ ] Historical Backtest Smoke passes on PR review head.
- [ ] Plan is archived, the PR is updated to completed path, and active plan removed.
- [ ] Final archival head passes all required checks and Historical Backtest Smoke.
- [ ] Squash merge succeeds using exact verified head SHA.
- [ ] Main corpus verifies exactly Cash=30, Funding=32 with correct unique dates.
- [ ] Issue #51 is closed only after main verification.

## Implementation slices

- [x] 1. Confirm explicit promotion provenance and staged campaign evidence.
- [x] 2. Verify staged corpus index, 25 exact dates and source provenance.
- [ ] 3. Open governed review PR linked to Issue #51.
- [ ] 4. Validate all PR review-head CI and Smoke checks.
- [ ] 5. Archive execution plan and re-validate final head.
- [ ] 6. Squash merge, verify main corpus and close Issue #51.

## Verification matrix

| Gate | Expected / observed |
|---|---|
| Source Q1 | 37731060921, 12 compact cases |
| Source Q2 | 37730401199, 13 compact cases |
| Planner | 37745788337 success |
| Promotion | 37746589796 success |
| Staged new unique Cash dates | 25/25 exact pre-registered match |
| Staged Funding distinct dates | 32 unchanged |
| Staged Cash distinct dates | 30 |
| Source artifact/parent SHA | verified by promotion |
| Offline staged replay | success |
| PR five required CI checks | pending |
| PR Historical Backtest Smoke | pending |
| Final-head checks | pending |
| Main corpus after merge | pending |

## Guardrails

- Do not change frozen dates, source run/artifact identities, future contracts, or economic thresholds.
- Do not activate a Cash Stage-2 economics gate just because the minimum 30-day evidence count is met.
- Preserve selection-provenance and parent artifact digests for every promoted fixture.
- Keep Issue #51 open through the final merge.

## Resume from here

Open the governed PR using the current branch and canonical Issue/Plan body lines. After all review-head CI and Historical Smoke succeed, archive this plan into docs/exec-plans/completed, update PR Plan reference and delete active plan. Re-run final-head checks, merge using expected head SHA, verify main counts/dates and close Issue #51.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: PR review, final-head checks, merge, main verification
