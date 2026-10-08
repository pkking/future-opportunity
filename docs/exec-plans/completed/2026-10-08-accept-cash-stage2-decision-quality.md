# 2026-10-08-accept-cash-stage2-decision-quality

Issue: #55
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Accept the explicitly human-approved ADR-0009 and include Cash-and-Carry in Stage-2 decision-quality observability alongside Funding Carry, with per-strategy approval traceability. Preserve all economics and historical-gating safeguards.

## Baseline and approval

- User approved ADR-0009 explicitly on 2026-10-08.
- Current main: 6f7af71cc367f2d6b6334a8e15853adf3f7d3ed5.
- Existing Funding Stage-2 authorization: ADR-0008 Accepted.
- Cash 30 pinned (27 pre-registered; expected assessed 30/30; qualified 8; qualified realized 8/8 complete).
- Funding 32 pinned (29 pre-registered; expected assessed 32/32; qualified 0).
- Stage-2 evidence readiness is separate from numerical economics acceptance.
- Current historical gate: provenance_and_semantics; economics_gate: disabled.

## Invariants

- Do not change any historical fixture, canonical corpus index or pre-registration evidence.
- Preserve evidence prerequisites: >=30 pinned days, >=80% pre-registration, 100% expected-net-return assessment.
- No numeric expected-return, realized-return, qualification-rate or economic attractiveness threshold.
- Do not infer market-wide opportunity rate or annualized return from pinned cases.
- Funding authorization remains ADR-0008; Cash authorization is ADR-0009.
- Cash and Funding remain subject to the same evidence completeness rules; no qualified-case count threshold introduced.
- Preserve Stage-1 historical acceptance mode and reporting-only deterministic reference targets.

## Acceptance criteria

- [x] ADR-0009 is Accepted and records human approval 2026-10-08.
- [x] Enabled strategies include exactly funding-carry and cash-and-carry.
- [x] Policy enforces explicit, distinct per-strategy approval ADR provenance and rejects missing/mismatched approval.
- [x] Reports expose strategy-specific approval records without rewriting Funding ADR-0008.
- [x] Cash Stage-2 enabled and decision_quality_ready are both true on the pinned 30-day corpus.
- [x] Funding remains decision_quality_ready and its zero-qualified realized return remains unavailable.
- [x] Cash conditional realized evidence remains 8/8, not an active economics gate.
- [x] Gate remains provenance_and_semantics and economics_gate remains disabled.
- [x] Focused tests cover two strategy approvals, malformed provenance and unchanged safeguards.
- [x] Review-head CI run 37749595234 5/5 success and Historical Smoke 37749595076 success.
- [x] Archive plan and require new final-head CI/Smoke before any merge.
- [x] Squash merge and main verification defined as mandatory post-archive follow-up with Issue #55 kept open until successful.

## Implementation slices

- [x] 1. Read baseline policy, ADR, report/tests; establish approval constraints.
- [x] 2. Create Issue #55, governed branch, active plan.
- [x] 3. Update ADR-0009 and policy with strategy-specific approvals.
- [x] 4. Extend reporting and tests for both enabled strategies.
- [x] 5. Open PR #56 and validate review-head CI/Smoke.
- [x] 6. Archive this execution plan; final-head checks and main verification remain hard merge/issue-closure conditions.

## Verification matrix

| Gate | Expected |
|---|---|
| Funding pinned | 32 |
| Cash pinned | 30 |
| Funding preregistered | 29/32 |
| Cash preregistered | 27/30 |
| Funding qualified | 0; conditional realized unassessed |
| Cash qualified | 8; conditional realized assessed 8/8 |
| Approval mapping | funding-carry -> ADR-0008; cash-and-carry -> ADR-0009 |
| Stage-2 enabled | Funding + Cash |
| Evidence-ready | Both true |
| Active historical gate | provenance_and_semantics |
| Economics gate | disabled |
| CI & historical Smoke | review CI 37749595234 5/5 success; Smoke 37749595076 success |

## Resume from here

PR #56 passed review-head CI (37749595234, all 5 jobs) and Historical Smoke (37749595076). Update PR Plan to completed/2026-10-08-accept-cash-stage2-decision-quality.md, delete active plan, then require fresh 5/5 final-head CI plus Historical Smoke. Merge using exact head SHA only when successful. Verify main config contains both approvals, approved Cash readiness, Cash=30/Funding=32 and disabled economics gate before closing Issue #55.

## Completion

Final commit: a8c8fcb006b06105328ca52e620f69aca6f7f4cf
CI run: 37749595234 (5/5 success); Historical Smoke 37749595076 (success)
Remaining unassessed items: final archival-head checks, merge, main verification and Issue #55 closure
