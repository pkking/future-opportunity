# 2026-10-07-cash-futures-source-coverage: Diagnose OKX Cash archive coverage

Issue: #26
Status: IMPLEMENTING
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

- [ ] Coverage input dates are deterministic: 5 pinned controls + 28 Wave 002/003 samples.
- [ ] Module 4 and module 6 receive identical date/family/aggregation queries.
- [ ] Evidence records exact query parameters and catalog candidate metadata without downloading full archives.
- [ ] Summary reports zero/unique/ambiguous counts by module and positive-control pass rate.
- [ ] Unit tests lock date matrix and summary semantics.
- [ ] Historical Data Schema Probe uploads the coverage evidence.
- [ ] Result states whether an evidence-source decision is required.

## Implementation slices

- [x] 1. Close completed Wave 002/003 decision and open Issue #26.
- [x] 2. Create this main-based implementation branch and plan.
- [ ] 3. Extend existing historical probe with deterministic Cash coverage matrix and summary.
- [ ] 4. Add focused tests.
- [ ] 5. Trigger Historical Data Schema Probe through the script change and inspect artifact evidence.
- [ ] 6. Run full PR gates, archive plan, merge if green, and record the evidence-source decision gate.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | focused coverage helper tests | pending |
| Static | ruff + architecture contract | pending |
| Probe | Historical Data Schema Probe artifact | pending |
| CI | repository CI | pending |
| Historical smoke | pinned historical replay | pending |

## Decision gates

No decision is needed to run the diagnostic. Stop for operator review only if the evidence shows a viable alternate official source/module whose fidelity differs from the current module-4 400-level evidence, because accepting that source would change historical evidence semantics.

## Resume from here

Implement the matrix inside the existing historical probe, keeping the network query/read-only boundary unchanged. Add unit tests for date construction and zero/unique/ambiguous summary classification. Push the script change so the existing probe workflow emits evidence, then inspect module-4 vs module-6 coverage before proposing any fallback.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: module-4/module-6 coverage evidence and any resulting evidence-source decision
