# 2026-10-08-cash-2025-q3-q4-source-capacity

Issue: #59
Status: COMPLETED
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

- [x] Read-only capacity probe covers 2025 Q3 and Q4 bounded official futures archive calendar windows with missing/error explicit.
- [x] SPOT entry and exit six fixed dates have official catalog identities or explicit errors.
- [x] Exact FUTURES exit identity checked for both maturity exit dates.
- [x] A single machine-readable artifact records source identity statuses and remaining blockers.
- [x] Tests cover missing, duplicate, wrong future, and source error.
- [x] Review head CI 37755042891 5/5 success and Historical Smoke 37755042850 success; fresh final-head checks required before merge.
- [x] Completed plan archived with governance and exact final-head/main verification requirements, to be executed before issue closure.

## Implementation slices

- [x] 1. Create Issue/branch/plan after verifying first-source evidence.
- [x] 2. Implement bounded futures daily capacity query by quarter.
- [x] 3. Verify spot catalog at fixed entry/exit dates and exact futures exit member.
- [x] 4. Add workflow/artifact and pure tests.
- [x] 5. Verify source report, document outcomes and blockers.
- [x] 6. PR #60 review checks passed; archive plan and require final-head CI/Smoke before merge.

## Verification matrix

| Gate | Expected |
|---|---|
| Q3 chain source | 87/87 daily unique archive; 0 gaps/errors, live run 37754484440 |
| Q4 chain source | 90/90 daily unique archive; 0 gaps/errors, live run 37754484440 |
| Q3/Q4 entry member identity | prior 4/4 verified |
| Exit FUTURES source | Q3 and Q4 exact member identities verified |
| Entry/exit SPOT catalog | 6/6 unique catalog sources |
| Acquisition | disabled |
| Economics | disabled |
| Main Cash/Funding | 30/32 unchanged |
| Required CI and Smoke | CI 37755042891 5/5 success; Smoke 37755042850 success |

## Resume from here

PR #60 review head passed CI 37755042891 5/5 and Smoke 37755042850. Live workflow 37754484440 artifact 11539801691 establishes Q3 87/87 and Q4 90/90 unique FUTURES daily archives, SPOT fixed dates 6/6, FUTURES exits 2/2. Actual 00:15 snapshots are unassessed and acquisition_ready stays false. Update PR to completed plan, delete active plan, require new final-head CI/Smoke, merge by exact head SHA, verify main unchanged, close issue. A separate follow-up must freeze sample dates before ever assessing economics.

## Completion

Final commit: 823ae86d3aec38fbc413e87c335924efa6512af5
CI run: 37755042891 (5/5 success); Historical Smoke 37755042850 success
Remaining unassessed items: archival-head checks, merge, main verification; exact 00:15 L2 entry/exit samples for future pre-registered waves
