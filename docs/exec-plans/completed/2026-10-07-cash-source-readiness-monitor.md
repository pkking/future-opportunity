# 2026-10-07-cash-source-readiness-monitor: Monitor exact pre-registered Cash source availability

Issue: #33
Status: COMPLETED
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
- [x] Exact 28 canonical dates are reused without replacement.
- [x] Pure readiness summary handles none/partial/all-ready cases.
- [x] Catalog query chunking is bounded to <=10 days.
- [x] Scheduled + manual non-gating workflow emits machine-readable evidence.
- [x] Workflow permissions are read-only.
- [x] Job summary reports required/ready/missing/all_ready.
- [x] Offline tests cover summary and date contract.
- [x] Full PR CI and Historical Smoke pass.
- [x] No automatic acquisition or study-design mutation exists.

## Implementation slices

- [x] 1. Open Issue #33 and create this branch/plan.
- [x] 2. Add pure readiness model and tests.
- [x] 3. Add catalog probe script using exact canonical dates.
- [x] 4. Add scheduled/manual read-only workflow.
- [x] 5. Baseline run 37605404316 succeeded: ready=0, missing=28, ambiguous=0, query_error=0, all_ready=false.
- [x] 6. Archive/merge implementation; stop at execution decision if/when all_ready becomes true.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | `tests/test_cash_source_readiness.py` in CI 37609468354 | passed |
| Static/API/E2E | PR CI 37609468354 | passed |
| Historical smoke | 37609468358 | passed |
| Baseline readiness | run 37605404316 artifact 11474303342 / sha256:c042c3783902bfa37dd17d9332df2e15530452aa210aac57b1bace097b025920 | passed |

## Decision gates

No decision is required to add or run the monitor.

A separate explicit execution decision is required if/when `all_ready=true`: preferred action is retrying acquisition for the exact pre-registered Wave 002/003 Cash dates, not resampling.

## Evidence log

- 2026-10-07: Issue #33 opened after Issue #31 measured module-4 publication frontier at 2026-06-26.
- 2026-10-07: branch `agent/cash-source-readiness-monitor` created from main 1208f1a39e9e8a9564aa731c043e3c7df5458752.
- 2026-10-07: baseline readiness run 37605404316 succeeded with `required_count=28`, `ready_count=0`, `missing_count=28`, `ambiguous_count=0`, `query_error_count=0`, `all_ready=false`.
- 2026-10-07: artifact 11474303342 digest `sha256:c042c3783902bfa37dd17d9332df2e15530452aa210aac57b1bace097b025920`.

## Deviations and discoveries

None yet.

## Resume from here

Implementation and baseline evidence are reconciled. Move this plan to `completed/`, update PR #34 metadata, rerun final Ruleset checks, merge, and close Issue #33 only after merge. The scheduled monitor should continue read-only while all_ready=false.

## Completion

Final commit: 084cc916b237bbcc922f7735a1201ec7714f7f32
CI run: https://github.com/pkking/future-opportunity/actions/runs/37609468354
E2E artifact: strategy E2E evidence from CI run 37609468354
Historical smoke: https://github.com/pkking/future-opportunity/actions/runs/37609468358
Baseline readiness run: https://github.com/pkking/future-opportunity/actions/runs/37605404316
Baseline artifact: 11474303342 / sha256:c042c3783902bfa37dd17d9332df2e15530452aa210aac57b1bace097b025920
Remaining unassessed items: future source publication and exact-wave retry execution decision when all_ready=true
