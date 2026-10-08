# 2026-10-08-cash-stage2-decision-evidence

Issue: #53
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Analyze the 30 pinned Cash-and-Carry days for Stage-2 decision-quality using the existing actuals and provenance framework. Make evidence sufficiency and contract/holding-horizon heterogeneity observable without changing approval scope or economics gates.

## Evidence baseline

- Main merge of Cash 30 days: a5124f804a603731a55125563959e1c6811a10d8.
- Main Historical Backtest Smoke run: 37747210353.
- Evidence artifact 11536670411, digest sha256:762ef5d6f7f10fc4ccc37e75cf722012af65ad91c383fb260e97c33aca033950.
- Cash: 30 pinned, 27 pre-registered, expected assessed 30/30, qualified 8, realized 8/8 complete, 22 rejected.
- Q1 March expiry: 12 cases, 5 qualified, horizon 5–81 days.
- Q2 June expiry: 18 cases, 3 qualified, horizon 2–89 days.
- Funding: 32 pinned, 0 qualified; existing Stage-2 decision-quality enabled for Funding only.
- Existing economics gate remains disabled / historical mode provenance_and_semantics.

## Invariants

- Human approval of ADR-0008 for Funding is not implicitly approval for Cash.
- No changes to stage2_decision_quality.enabled_strategies, active historical gate, numerical threshold or canonical historical corpus fixtures.
- Zero qualified cases must not produce an invented zero-realized distribution or a positive economics gate.
- Rejection reason counts can overlap and must not be summed as unique case counts.
- Report by observed expiry cohorts and explicit holding periods; no annualized or market-wide profitability claims.
- Cohorts sharing a contract expiry are not presumed independent trials.

## Acceptance criteria

- [x] Readiness exposes evidence conditions separately from Stage-2 enablement for any strategy.
- [x] Cash per-expiry report contains count, qualification, reasons and expected/conditional realized-return distributions.
- [x] Holding horizon is computed from real entry and exit timestamps, with all and qualified cohorts separately assessed.
- [x] Empty-qualified and incomplete-realized return cases remain explicit without fabricated zeros.
- [x] Cash stays not Stage-2 enabled; numerical economics gate remains disabled.
- [x] Report explicitly states non-independence, non-annualization and non-market-wide scope.
- [x] Tests cover new readiness and report invariants.
- [x] Version evidence research with exact main smoke artifact attribution and next approval boundary.
- [x] Review head passed five required checks and Historical Smoke; fresh final-head verification is mandatory before merge.
- [x] Execution plan archived with PR #54 and Issue #53 traceability; merger must separately verify main before issue closure.

## Implementation slices

- [x] 1. Inspect source artifacts and record actual Cash distributions and horizon/expiry cohorts.
- [x] 2. Create governed Issue #53 and implementation branch.
- [x] 3. Add separate evidence-eligible status and expiry/holding-period cohort report.
- [x] 4. Add reproducible tests, document limitations and recommendations.
- [x] 5. Open PR #54 with Issue #53 and verify review-head CI and Smoke.
- [x] 6. Archive plan and require final-head CI/Smoke; merge, main verification and issue closure occur only after those checks.

## Verification matrix

| Check | Baseline / expected |
|---|---|
| Cash pinned | 30 |
| Cash pre-registered | 27 / 30 |
| Cash qualified | 8 / 30 |
| Cash assessed realized (conditional) | 8 / 8 |
| Q1 expiry cohort | 12 pinned / 5 qualified |
| Q2 expiry cohort | 18 pinned / 3 qualified |
| Funding pinned / qualified | 32 / 0 |
| Enabled Stage-2 strategies | Funding only |
| Economics gate | disabled |
| Human choice before Cash activation | required |
| Required CI | review head run 37748696193: 5/5 success |
| Historical Smoke | review head run 37748696345: success |

## Resume from here

PR #54 has passed all five required checks (37748696193) and Historical Backtest Smoke (37748696345). Update the PR to reference this completed plan, delete the active plan, and re-run the final-head checks. Squash-merge only after final CI/Smoke are fully green. Verify main reporting retains Cash disabled, Funding-only Stage-2 enabled, Cash 30 pinned, Funding 32 pinned, and the new maturity evidence. Close Issue #53 only after main verification.

## Completion

Final commit: bc079d239199ffababe4e59e395d625ce09977f8
CI run: 37748696193 (5/5 success); Historical Smoke 37748696345 (success)
Remaining unassessed items: final archival-head checks, PR merge, main verification; Cash ADR-0009 requires separate human approval
