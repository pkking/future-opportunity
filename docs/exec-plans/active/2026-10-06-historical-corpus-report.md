# 2026-10-06-historical-corpus-report: Stage-1 corpus-wide historical distribution reporting

Status: VERIFYING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Produce a deterministic, offline, machine-readable distribution report for
*every indexed historical market-day case* in both supported strategies.

The report must distinguish a pinned entry-day case rate from a market-wide
opportunity arrival rate, and must preserve missing/unassessed realized return
as null rather than zero.

## Non-goals

- No activation of Stage-2 distribution acceptance.
- No historical return-based CI gating or automatic target inference.
- No live exchange calls or authenticated trading.
- No modification/merge of open corpus promotion PR #3.
- No unindexed or guessed external historical observations.

## Governing evidence

- AGENTS.md; docs/agents/workflow.md; docs/agents/testing.md.
- ADR-0006: historical provenance; ADR-0007: progressive acceptance.
- tests/e2e/historical-target-policy.json.
- tests/fixtures/historical/corpus-index.json, validated by load_historical_corpus.
- Completed corpus-campaign execution plan; main still has 2+2 pinned days,
  PR #3 (unmerged) proposes one further day per strategy.

## Invariants

1. Report covers *all and only* indexed, validated, pinned corpus fixtures.
2. One frozen historical case per pinned entry-market day; do not report this
   case qualification ratio as a market-wide opportunity frequency.
3. Use current Discover -> Simulate -> Close historical application workflow,
   no parallel strategy math.
4. Return distributions are strategy-specific; unqualified cases never contribute
   zero-valued realized returns.
5. Every metric includes its eligible denominator and evidence coverage.
6. All Decimal results serialize as exact strings; quantiles use a documented
   deterministic rank/interpolation rule.
7. Historical economics are `reporting_only`; existing Stage-1 gates remain
   unchanged.
8. Failed corpus validation/replay yields error evidence uploaded by CI.
9. The 30/90-day counts come only from the validated corpus index and remain
   advisory, never auto-activate Stage 2.

## Acceptance criteria

- [x] Add corpus-wide historical replay/report application and deterministic
      per-strategy summary statistics.
- [x] Provenance and per-case qualification/risk/unassessed evidence retained.
- [x] Correct null return distribution when no realized cases are assessed.
- [x] Properly distinguish entry-case qualification rate from market-wide rate.
- [x] Stable percentile definitions and tests including zero/one/multiple samples.
- [x] Unit + offline corpus integration tests cover both strategies.
- [x] CLI emits JSON evidence and error evidence on failure.
- [x] Historical Smoke uploads corpus distribution actuals without gating return.
- [x] README/testing contract documents meaning, limitations and reproduction.
- [x] Final Static, Code, API, E2E and historical-smoke CI green.

## Implementation slices

- [x] 1. Model reporting semantics and deterministic quantiles.
- [x] 2. Replay all indexed Funding/Cash fixtures through production workflow.
- [x] 3. Write machine-readable reporting CLI and offline tests.
- [x] 4. Integrate as additional reporting artifact into Historical Smoke.
- [x] 5. Document, validate final CI and archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/safety | passed CI 37440505065 |
| Code | report/quantiles/corpus integration tests | passed CI 37440505065 |
| API | no regression | passed CI 37440505065 |
| E2E | frozen strategy targets unchanged | passed CI 37440505065 |
| Historical smoke | full validated corpus report artifact, reporting_only | passed 37440355869; artifact 11400672797 |

## Decision gates

None. Future Stage-2 thresholds and activation explicitly require human
approval under ADR-0007.

## Evidence log

- 2026-10-06: prior corpus campaign completed; main CI 37439106863 green.
- 2026-10-06: PR #3 open, PR CI 37435522881 and Historical Smoke
  37435522957 green. No automatic merge.
- 2026-10-06: corpus report replays all indexed cases through existing Funding
  Carry/Cash-and-Carry product workflows, preserving case/provenance evidence,
  exact Decimal expected-return distributions, bounded or complete realized-
  return distributions and explicit nulls for unavailable outcomes.
- 2026-10-06: tests lock percentile interpolation and fail-closed behavior for
  missing realized data. Report distinguishes pinned-case qualification from
  market-wide opportunity arrival; latter remains null/unassessed.
- 2026-10-06: Historical Smoke run 37440355869 succeeded and uploaded artifact
  11400672797. Log confirms reporting_only and case counts Funding=2, Cash=2.
  README/testing contract documents the sample-selection limitations.
- 2026-10-06: main CI 37440505065 passed Static, Code, API and E2E gates.


## Resume from here

All features and test evidence are complete. After the final plan-only CI
is green, mark COMPLETED and archive. Future evidence accumulation happens
through reviewed corpus campaigns; no automatic Stage-2 threshold activation.

## Completion

Final implementation/documentation commit: b8822769122a4eb7bcd63abb911a512719f41d25
CI: 37440505065 (success)
Historical report artifact: 11400672797 from Historical Smoke run 37440355869
Remaining unassessed items: market-wide opportunity arrival rate (sampled corpus cannot establish it), exact funding mark/returns, Stage-2 statistical thresholds
