# 2026-10-08-promote-cash-stage2-quarter-wave-001

Issue: #51
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Provide governed, reproducible evidence for the 25-day Cash Stage-2 historical corpus promotion and validate the staged fixture state before final-head merge.

## Frozen source evidence

- Planner run 37745788337, successful; artifact historical-campaign-planner-37745788337, ID 11536165590, SHA256 8b19457239ad9979be44db3bbc333bbb1107a64899678298f4764e44307b4a94.
- Promotion run 37746589796, successful; artifact historical-campaign-evidence-37746589796, ID 11535639577, SHA256 a0cb9eb8264ac459993341d9810e3ac9fa0ef1953820d5f3cf8836fe746d3305.
- Campaign cash-stage2-quarter-review-001-wave-001; source Q1 37731060921 (12 cases / BTC-USDT-260327) and Q2 37730401199 (13 cases / BTC-USDT-260626).
- Selection frozen in docs/historical-acquisition-plans/cash-stage2-30day-wave-001.json.
- Review PR #52; source branch historical-corpus-campaign/cash-stage2-quarter-review-001-wave-001-37746589796-1.
- Promotion task Issue #51 remains open until PR merge and main verification.

## Acceptance criteria

- [x] Promotion uses the exact previously validated Planner run/artifact/wave.
- [x] All 25 source compact fixtures and parent artifact digests verified by promotion.
- [x] Exactly 25 new Cash dates added, matching the frozen selection without omissions.
- [x] Q1 and Q2 quarter-aligned contract semantics and provenance preserved.
- [x] Offline staged tests and Historical Smoke succeed.
- [x] Staged corpus has 30 distinct Cash days and retains 32 Funding days.
- [x] PR #52 exists with canonical Issue and execution Plan references.
- [x] Review head CI has five successful required jobs.
- [x] Review head Historical Backtest Smoke succeeds.
- [x] Execution plan archived as completed for final-head validation.
- [x] Main merge is explicitly gated on fresh final archival-head CI and Smoke.

## Implementation slices

- [x] 1. Check exact promotion source provenance and evidence.
- [x] 2. Verify staging index and 25 exact frozen Cash dates.
- [x] 3. Open PR #52 with Issue #51 and active plan.
- [x] 4. Verify review-head CI 5/5 and Historical Smoke.
- [x] 5. Archive this plan and require final-head revalidation.
- [x] 6. Document post-merge count and issue closure verification requirements.

## Verification matrix

| Gate | Evidence/result |
|---|---|
| Source Q1 | 37731060921: 12 cash cases |
| Source Q2 | 37730401199: 13 cash cases |
| Planner | 37745788337 success |
| Promotion | 37746589796 success |
| New frozen Cash dates | 25/25 exact match |
| Staged Funding days | 32 |
| Staged Cash days | 30 |
| Offline promotion verification | success |
| Review-head CI | 37746849098; 5/5 successful |
| Review-head Historical Smoke | 37746849107 successful |
| Final archival-head CI/Smoke | required before merge |
| Main branch verified count | required after merge |

## Guardrails

- This plan does not approve economic-return thresholds or automatically activate Cash Stage-2.
- Do not alter any previously frozen sample dates or the historical source artifact references.
- Keep issue #51 OPEN through successful merge and post-merge corpus verification.

## Resume from here

PR #52 has passed review-head CI and Historical Backtest Smoke. Update PR Plan to docs/exec-plans/completed/2026-10-08-promote-cash-stage2-quarter-wave-001.md and delete its active plan. Require all five required checks and separate Historical Smoke on the final archival head. Squash merge using exact expected head SHA. Verify main corpus-index has 30 distinct Cash dates and 32 distinct Funding dates; ensure the added 25 dates match frozen selection; only then close Issue #51.

## Completion

Final commit: 69073ee21fce2b174520775a2755f3844033f1bc
CI run: 37746849098 (all five required checks successful)
Historical Smoke: 37746849107 successful
Remaining unassessed items: final archival-head checks, merge, post-merge verification and issue closure
