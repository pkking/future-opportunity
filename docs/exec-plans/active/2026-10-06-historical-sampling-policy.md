# 2026-10-06-historical-sampling-policy: Reproducible unbiased market-day sampling for Stage-2 evidence

Status: COMPLETED
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Define and implement a deterministic, auditable market-day sampling policy for
historical corpus growth so the future 30/90-day evidence base is not selected
after observing strategy outcomes.

The sampling layer chooses **dates only**. It does not inspect profitability,
qualification, spreads, funding rates, realized returns, or strategy outcomes.

Target flow:

```text
explicit study window + strategy + sample size + committed seed/policy
  -> deterministic candidate calendar
  -> deterministic sampled market dates
  -> explicit exclusions only for source-data availability/contract validity
  -> acquisition planning
  -> normal prepare / promote / review path
```

## Why this is required

The current corpus contains only a small manually selected set of market days.
Those fixtures are valid regression evidence, but they cannot establish a
market-wide opportunity arrival rate or an unbiased return distribution.

ADR-0007 requires 30 distinct days per strategy before Stage-2 design becomes
eligible. Counting 30 hand-picked dates would satisfy the number but not the
statistical intent.

## Non-goals

- No Stage-2 threshold design or activation.
- No automatic promotion or merge.
- No selection based on strategy return/profitability.
- No weighting based on future-known market conditions.
- No changing existing pinned fixtures.
- No claiming 30 sampled days are sufficient for final inference by themselves.

## Governing decisions

- AGENTS.md
- ADR-0006 historical dataset provenance
- ADR-0007 progressive historical acceptance policy
- historical corpus/report/acquisition contracts
- current Stage-1 economics remain reporting_only

## Initial sampling policy

Use a **pre-registered systematic sample with a committed hash-derived offset**
over an explicit inclusive UTC calendar window.

For each strategy study:

1. Operator supplies:
   - strategy;
   - inclusive start/end market dates;
   - requested sample size;
   - stable sampling-policy version;
   - explicit seed string.
2. Build the complete inclusive UTC calendar-day population before looking at
   strategy outcomes.
3. If requested sample size >= population size, select the full population.
4. Otherwise partition the population into requested_sample_size ordered strata
   using integer boundaries.
5. Derive one deterministic offset per stratum from SHA-256 of:
   `policy_version|strategy|seed|population_start|population_end|stratum_index`.
6. Select one calendar day inside each stratum from that offset.
7. Sort selected dates chronologically.
8. Data-source unavailability may exclude a selected date, but the exclusion
   remains explicit. Do not replace it with a profitable neighboring date.
9. A later replacement/resampling policy, if desired, requires a new policy
   version so the original draw remains reproducible.

Rationale:

- avoids hand-picking dates;
- spreads evidence across the whole study window;
- deterministic and reproducible;
- does not depend on returns or market-state labels;
- easier to audit than ad-hoc random sampling;
- preserves explicit missing-data evidence instead of silently cherry-picking.

## Constraints and invariants

- Sampling inputs are versioned evidence.
- Same inputs always produce identical dates.
- Strategy is part of the hash domain separator.
- Sampling never reads market data or backtest outputs.
- Requested sample size must be positive.
- Date range must be valid ISO UTC calendar dates.
- Duplicate sampled dates are impossible.
- Sampled dates are chronological in output.
- Output records full population size, policy version, seed, hashes/strata, and
  selected dates.
- Existing pinned corpus dates do not alter the draw. Overlap is reported later
  by acquisition/corpus planning rather than changing the sample.
- Missing source data is an exclusion, not a reason to mutate the draw.
- Stage-2 remains ineligible until validated pinned counts meet ADR-0007 and a
  separate ADR is approved.

## Acceptance criteria

- [x] Add versioned sampling request/result model.
- [x] Implement deterministic systematic-stratified sampler.
- [x] Same request is byte-for-byte deterministic.
- [x] Different strategy or seed changes hash domain.
- [x] Full-population request returns every day exactly once.
- [x] Invalid dates/sample counts fail closed.
- [x] Tests prove sampler never depends on market/profitability inputs.
- [x] CLI emits machine-readable sampling evidence.
- [x] Add read-only workflow_dispatch sampling workflow.
- [x] Workflow permissions remain contents:read only.
- [x] Workflow uploads sample request/result evidence only.
- [x] Add acquisition-composition bridge from a reviewed sample artifact for
      Funding dates without silently replacing unavailable dates.
- [x] README/testing docs define pre-registration and exclusion semantics.
- [x] Final CI + workflow self-test green.
- [x] Archive after verification.

## Implementation slices

- [x] 1. Sampling domain model and deterministic algorithm.
- [x] 2. Unit/property-style boundary tests.
- [x] 3. Sampling CLI + evidence schema.
- [x] 4. Read-only Actions workflow and self-test.
- [x] 5. Reviewed-sample -> Funding acquisition composition bridge.
- [x] 6. Documentation and final verification.
- [x] 7. Archive.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | passed 37483945384 |
| Code | deterministic sampling + boundaries | passed 37483945384 |
| API | no regression | passed 37483945384 |
| Reference E2E | unchanged | passed 37483945384 |
| Workflow | request -> sample evidence | passed 37482498880; artifact 11421537670 |
| Safety boundary | no market/backtest/profitability dependency or mutation | workflow contract + pure sampler signature tests passed |

## Decision gates

None for the sampling mechanism itself.

A future change that stratifies using market outcomes/volatility/regimes, or
changes replacement rules after seeing results, requires an explicit policy
decision/ADR because it changes statistical interpretation.

## Evidence log

- 2026-10-06: ADR-0007 requires >=30 distinct pinned market days per strategy
  before Stage-2 target design is eligible.
- 2026-10-06: historical corpus report explicitly leaves market-wide
  opportunity arrival rate unassessed because the current sampled corpus cannot
  establish it.
- 2026-10-06: committed corpus currently contains 2 Funding Carry and 2
  Cash-and-Carry days; open/unmerged candidates do not count.

## Deviations and discoveries

None.

## Resume from here

Completed. Future Stage-2-oriented corpus growth should start from a reviewed,
pre-registered sampling artifact. Missing source data remains an explicit
exclusion; the draw is not mutated after outcomes are observed.

## Completion

Final implementation/documentation commit: 5a6b055a8770d4d2d37add2c23c8f677d16642df
CI run: 37483945384 passed all required gates
Sampling workflow evidence: run 37482498880; artifact 11421537670; SHA-256 bdaab43d0be70a2fc8b43059d39f5341a2405bf9a0aff00306b90e92e24b8fa2
Sampled acquisition bridge evidence: composer run 37483512784; artifact 11422581630; SHA-256 05ba4d4c322ee86343cd3d01fb676d55e9d3c5c3b6acf8780c0267e5bc9a9b38
Remaining unassessed items: market-wide opportunity arrival remains unassessed until a sufficiently broad pre-registered corpus is pinned; Stage-2 thresholds remain a separate ADR/human decision

## Evidence log

- 2026-10-06: sampler v1 implemented as deterministic systematic strata with
  SHA-256-derived within-stratum offsets. Golden request
  Funding/2026-01-01..2026-01-31/n=5/seed=stage2-baseline-v1 selects
  2026-01-01, 2026-01-08, 2026-01-13, 2026-01-22 and 2026-01-29.
- 2026-10-06: tests lock byte-for-byte determinism, strategy/seed hash-domain
  separation, full-population behavior, invalid inputs, non-overlapping strata
  and the sampler's absence of market/profitability inputs.
- 2026-10-06: sampling evidence parser recomputes the full draw from the embedded
  request and rejects selected-date/hash/schema tampering.
- 2026-10-06: read-only workflow run 37482498880 passed and uploaded artifact
  11421537670 with digest
  bdaab43d0be70a2fc8b43059d39f5341a2405bf9a0aff00306b90e92e24b8fa2.
- 2026-10-06: acquisition Funding schema now accepts either a contiguous
  start/end range or explicit chronological market_dates, never both. Existing
  range workflows remain compatible.
- 2026-10-06: acquisition composer independently verifies the exact sampling
  run/artifact and deterministically replays the sample before converting a
  funding-carry sample to explicit market_dates. Self-test run 37483512784
  produced the five sampled Funding dates plus the reviewed 2026-06-03 Cash
  case without filling date gaps; artifact 11422581630.
- 2026-10-06: composer push defaults were scoped to push events so optional
  manual workflow_dispatch inputs no longer inherit self-test Funding/Cash data.
- 2026-10-06: README/testing contracts now define pre-registration,
  no-replacement exclusions, explicit-date acquisition, and the continued
  separation between composition and explicit acquisition dispatch.
- 2026-10-06: final CI run 37483945384 passed Static, Code-level, API contract
  and E2E strategy acceptance gates.
