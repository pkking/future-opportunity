# 2026-10-07-cash-futures-source-coverage: Diagnose OKX Cash archive coverage

Issue: #26
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Turn the repeated Wave 002/003 Cash exclusions into a source-coverage diagnosis before any evidence-quality or source-fallback decision.

The diagnostic compares the current OKX module-4 daily FUTURES BTC-USDT catalog query with official 50-level order-book module 6 using exactly the same market dates.

## Current facts

- Main pinned Cash dates are 2026-06-01, 06-02, 06-03, 06-04 and 06-08.
- Wave 002 + Wave 003 sampled 28 Cash dates; every discovery report returned candidate_count=0 / no_unique_future_chain_archive under module 4.
- Existing script `scripts/probe_okx_historical_archive.py` already probes OKX historical catalog modules and has bounded schema sampling.
- Existing workflow `.github/workflows/historical-data-probe.yml` uploads probe evidence on script changes.
- OKX current public historical-data documentation lists order-book historical data among supported downloadable datasets; the repository already models modules 4 and 6 as order-book archive sources.
- This task is diagnostic only: module 6 is not automatically accepted as equivalent evidence.

## Constraints

- Use official OKX catalog only.
- No full archive download for the 33-date coverage matrix.
- Query module 4 and module 6 with the same FUTURES/BTC-USDT/daily/date inputs.
- Preserve Wave 002/003 dates exactly; no outcome-based selection.
- Include positive controls from the current pinned Cash corpus.
- Distinguish zero, unique and ambiguous candidate counts.
- Do not alter Cash preparation/discovery behavior in this task.

## Acceptance criteria

- [x] Coverage input dates are deterministic: 5 pinned controls + 28 Wave 002/003 samples.
- [x] Module 4 and module 6 receive identical date/family/aggregation queries.
- [x] Evidence records exact query parameters and catalog candidate metadata without downloading full archives.
- [x] Summary reports zero/unique/ambiguous counts by module and positive-control pass rate.
- [x] Unit tests lock date matrix and summary semantics.
- [x] Historical Data Schema Probe uploads the coverage evidence.
- [x] Result states whether an evidence-source decision is required.

## Implementation slices

- [x] 1. Close completed Wave 002/003 decision and open Issue #26.
- [x] 2. Create this main-based implementation branch and plan.
- [x] 3. Extend existing historical probe with deterministic Cash coverage matrix and summary.
- [x] 4. Add focused tests.
- [x] 5. Historical Data Schema Probe run 37600956057 uploaded artifact 11473295390; module 4 and module 6 both show 5/5 positive controls with unique candidates and 0/28 Wave 002/003 dates with candidates.
- [x] 6. Run full PR gates, archive plan, merge if green, and record the evidence-source decision gate. Import bug fixed by moving pure coverage semantics into the package; latest CI is green.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | `tests/test_okx_cash_futures_coverage.py` in PR CI run 37602170963 | passed |
| Static | PR run 37601046367 | passed |
| Probe | rerun 37602098045 artifact 11472873651 / sha256:c6ff90e759b2d391b042ea131ecdb24bffe4e171bb163f64abb42c6e3a9062fe; both modules 5 controls unique / 28 wave dates absent | passed for coverage evidence |
| CI | PR run 37602170963 on commit 22457c19d5410af2023b045e17b0f74b9277e6ea | passed |
| Historical smoke | run 37602171089 | passed |

## Decision gates

No evidence-source decision is required from this diagnostic. The positive controls prove both module 4 and module 6 queries are functioning, while all 28 Wave 002/003 dates have zero candidates in both modules. Therefore switching from module 4 to module 6 would not recover the missing Cash evidence and would only change fidelity semantics without benefit.

The next decision should concern **how to obtain dated-futures historical evidence outside these two OKX catalog modules**, not whether to use module 6 as a fallback.

## Resume from here

Coverage evidence and implementation are reconciled. PR #27 is ready for completion-plan archival and merge. After #27 merges, close Issue #26 and open the next issue to evaluate alternate official historical evidence paths for dated futures while preserving the pre-registered dates and evidence-quality contract.

## Completion

Final commit: 22457c19d5410af2023b045e17b0f74b9277e6ea
CI run: https://github.com/pkking/future-opportunity/actions/runs/37602170963
E2E artifact: strategy-e2e-evidence artifact 11472784063 / sha256:2020cebb0f7eb4dbb797f5340d4bd4a4f752c43735375fcb3662189d5959a7c3
Probe run: 37602098045
Probe artifact: 11472873651 / sha256:c6ff90e759b2d391b042ea131ecdb24bffe4e171bb163f64abb42c6e3a9062fe
Historical smoke: https://github.com/pkking/future-opportunity/actions/runs/37602171089
Remaining unassessed items: alternate official dated-futures historical evidence paths outside OKX modules 4/6; Cash readiness remains 5 pinned days
