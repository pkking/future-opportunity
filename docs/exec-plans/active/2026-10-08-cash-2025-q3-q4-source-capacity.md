# 2026-10-08-cash-2025-q3-q4-source-capacity

Issue: #59
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Determine whether the newly identified 2025 Q3/Q4 Cash expiry cohorts have reproducible archive capacity, exact pre-expiry FUTURES exit members, and SPOT entry/exit catalog identities. Do not equate catalog identity with complete order-book market replay evidence.

## Input evidence

- Main SHA 9f4b18812e243c79139e2dde1def09f3dd9f295c.
- Prior fixed-entry source probe 37753604956; archive artifact 11538678600, SHA256 85083f599a9e85caaf2fbc22e67962c88f1b811bbe34327aed828e01a5dca1d4.
- Q3 target future BTC-USDT-250926; exit snapshot 2025-09-25T00:15:00+00:00.
- Q4 target future BTC-USDT-251226; exit snapshot 2025-12-25T00:15:00+00:00.
- Fixed entry source probes: 2025-09-12, 2025-09-19, 2025-12-12, 2025-12-19.

## Invariants

- Catalog presence is not proof of orderbook data completeness at 00:15, liquidity or returns.
- Fixed dates and expiry IDs cannot change after outcome observation.
- Every spot catalog source must uniquely identify module4 SPOT BTC-USDT.
- Exact futures exit member must be recorded as verified/unavailable/error; no silent fallback.
- Do not sample/pin/acquire/promote or change policy in this issue.

## Acceptance criteria

- [ ] Read-only capacity probe covers 2025 Q3 and Q4 bounded official futures archive calendar windows with missing/error explicit.
- [ ] SPOT entry and exit six fixed dates have official catalog identities or explicit errors.
- [ ] Exact FUTURES exit identity checked for both maturity exit dates.
- [ ] A single machine-readable artifact records source identity statuses and remaining blockers.
- [ ] Tests cover missing, duplicate, wrong future, and source error.
- [ ] All five required CI and Historical Smoke green at review/final heads.
- [ ] Plan archived, PR merged, main confirmed, Issue closed.

## Implementation slices

- [x] 1. Create Issue/branch/plan after verifying first-source evidence.
- [ ] 2. Implement bounded futures daily capacity query by quarter.
- [ ] 3. Verify spot catalog at fixed entry/exit dates and exact futures exit member.
- [ ] 4. Add workflow/artifact and pure tests.
- [ ] 5. Verify source report, document outcomes and blockers.
- [ ] 6. Governed PR, review CI/Smoke, plan archive, final CI/Smoke, merge.

## Verification matrix

| Gate | Expected |
|---|---|
| Q3 chain source | capacity unassessed before probe |
| Q4 chain source | capacity unassessed before probe |
| Q3/Q4 entry member identity | prior 4/4 verified |
| Exit FUTURES source | unassessed |
| Entry/exit SPOT catalog | unassessed |
| Acquisition | disabled |
| Economics | disabled |
| Main Cash/Funding | 30/32 unchanged |
| Required CI and Smoke | pending |

## Resume from here

Implement a separate source-report workflow without promoting any historical case. Existing 2025 fixed entry identities remain valid. Any incompleteness (including API download caps) must be recorded and never silently replaced. Use live source outputs to identify actual blockers for a later acquisition-wave issue.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: probing, tests, evidence inspection, governance merge
