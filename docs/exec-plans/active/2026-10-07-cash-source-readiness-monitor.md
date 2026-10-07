# 2026-10-07-cash-source-readiness-monitor: Monitor exact pre-registered Cash source availability

Issue: #33
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Add a read-only GitHub-native monitor for the exact 28 Wave 002/003 Cash dates so the repository can detect when canonical OKX module-4 L2 FUTURES-chain archives become available without resampling or changing study semantics.

## Current facts

- Issue #31/PR #32 measured a clean publication frontier through 2026-06-26 across modules 1/2/4/5/6.
- The current Cash preparation path uses module 4 / 400-level L2.
- Wave 002/003 selected 28 exact Cash dates and excluded them only because source archives were unavailable at execution time.
- Reusing the same dates after source publication preserves the approved pre-registration better than selecting replacement dates.
- Dispatching any retry remains a separate execution decision.

## Constraints and invariants

- Reuse canonical Wave 002/003 date constants from `cash_source_coverage.py`; do not duplicate a new date list.
- Canonical readiness source is module 4, FUTURES, BTC-USDT family, daily aggregation.
- Query chunks must be <=10 days.
- Workflow permissions remain `contents: read`.
- Scheduled monitor may publish artifacts/job summary only; no Issues/PR/corpus/acquisition writes.
- Network failures are evidence states, not reasons to mutate the sample.
- `all_ready` becomes true only when every one of the exact 28 dates has a unique module-4 catalog candidate.

## Acceptance criteria

- [x] Issue and immutable readiness contract are versioned before implementation.
- [ ] Exact 28 canonical dates are reused without replacement.
- [ ] Pure readiness summary handles none/partial/all-ready cases.
- [ ] Catalog query chunking is bounded to <=10 days.
- [ ] Scheduled + manual non-gating workflow emits machine-readable evidence.
- [ ] Workflow permissions are read-only.
- [ ] Job summary reports required/ready/missing/all_ready.
- [ ] Offline tests cover summary and date contract.
- [ ] Full PR CI and Historical Smoke pass.
- [ ] No automatic acquisition or study-design mutation exists.

## Implementation slices

- [x] 1. Open Issue #33 and create this branch/plan.
- [ ] 2. Add pure readiness model and tests.
- [ ] 3. Add catalog probe script using exact canonical dates.
- [ ] 4. Add scheduled/manual read-only workflow.
- [ ] 5. Run one baseline probe and record current readiness.
- [ ] 6. Archive/merge implementation; stop at execution decision if/when all_ready becomes true.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | readiness helper tests | pending |
| Static/API/E2E | PR Ruleset | pending |
| Historical smoke | PR workflow | pending |
| Baseline readiness | non-gating Actions artifact | pending |

## Decision gates

No decision is required to add or run the monitor.

A separate explicit execution decision is required if/when `all_ready=true`: preferred action is retrying acquisition for the exact pre-registered Wave 002/003 Cash dates, not resampling.

## Evidence log

- 2026-10-07: Issue #33 opened after Issue #31 measured module-4 publication frontier at 2026-06-26.
- 2026-10-07: branch `agent/cash-source-readiness-monitor` created from main 1208f1a39e9e8a9564aa731c043e3c7df5458752.

## Deviations and discoveries

None yet.

## Resume from here

Implement a pure readiness summary over the canonical 28 dates, then a module-4 catalog probe and daily scheduled workflow with read-only permissions.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: future source publication and exact-wave retry execution decision
