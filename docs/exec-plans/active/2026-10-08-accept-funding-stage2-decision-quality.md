# 2026-10-08-accept-funding-stage2-decision-quality

Issue: #43
Status: READY_FOR_REVIEW
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Record human acceptance of ADR-0008 and make the approved Funding Stage-2 decision-quality semantics machine-verifiable without activating a numerical economics gate.

## Acceptance criteria

- [x] ADR-0008 is Accepted with explicit approval date and boundary.
- [x] Policy configuration records Funding Stage-2 decision-quality as enabled and economics gating as disabled.
- [x] Funding Stage-2 readiness evaluates evidence completeness rather than requiring positive returns.
- [x] Pinned-case qualification rate remains reporting evidence, not market-wide arrival rate.
- [x] Rejected cases remain in qualification-rate denominator.
- [x] Rejected cases never become realized-return zeroes.
- [x] Realized-return economics gating reports unavailable when qualified evidence is insufficient.
- [x] Cash remains below Stage-2 minimum and is not enabled.
- [x] Distribution report exposes Stage-2 decision-quality status and reasons.
- [x] Tests prove current Funding=32 is decision-quality ready despite 0 qualified cases.
- [ ] Full CI and Historical Backtest Smoke pass.

## Implementation slices

- [x] 1. Create governed Issue/branch/plan.
- [x] 2. Accept ADR-0008 and version approved policy parameters.
- [x] 3. Implement pure Stage-2 readiness evaluation.
- [x] 4. Expose readiness in historical distribution evidence.
- [x] 5. Add policy/report unit tests.
- [ ] 6. Run CI/Smoke, archive plan, merge, close Issue.

## Verification matrix

| Gate | Expected |
|---|---|
| Funding pinned days | 32 |
| Funding pre-registered ratio | >=0.80 |
| Funding expected-return assessment | 100% |
| Funding qualified cases | may be 0 |
| Funding Stage-2 decision-quality | ready/pass |
| Funding economics gate | disabled/unavailable |
| Cash Stage-2 | not enabled / below minimum |
| Active historical gate | provenance_and_semantics remains unchanged |
| Required CI | all green |
| Historical Smoke | green |

## Resume from here

Implement the accepted policy as observability/readiness only. Do not add a numerical return threshold. Open a PR linked to Issue #43 and merge only after final-head CI/Smoke succeeds.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: PR CI/Smoke and final merge verification