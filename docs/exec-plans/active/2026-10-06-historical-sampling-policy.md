# 2026-10-06-historical-sampling-policy: Reproducible unbiased market-day sampling for Stage-2 evidence

Status: PLANNING
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

- [ ] Add versioned sampling request/result model.
- [ ] Implement deterministic systematic-stratified sampler.
- [ ] Same request is byte-for-byte deterministic.
- [ ] Different strategy or seed changes hash domain.
- [ ] Full-population request returns every day exactly once.
- [ ] Invalid dates/sample counts fail closed.
- [ ] Tests prove sampler never depends on market/profitability inputs.
- [ ] CLI emits machine-readable sampling evidence.
- [ ] Add read-only workflow_dispatch sampling workflow.
- [ ] Workflow permissions remain contents:read only.
- [ ] Workflow uploads sample request/result evidence only.
- [ ] Add acquisition-composition bridge from a reviewed sample artifact for
      Funding dates without silently replacing unavailable dates.
- [ ] README/testing docs define pre-registration and exclusion semantics.
- [ ] Final CI + workflow self-test green.
- [ ] Archive after verification.

## Implementation slices

- [ ] 1. Sampling domain model and deterministic algorithm.
- [ ] 2. Unit/property-style boundary tests.
- [ ] 3. Sampling CLI + evidence schema.
- [ ] 4. Read-only Actions workflow and self-test.
- [ ] 5. Reviewed-sample -> Funding acquisition composition bridge.
- [ ] 6. Documentation and final verification.
- [ ] 7. Archive.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | pending |
| Code | deterministic sampling + boundaries | pending |
| API | no regression | pending |
| Reference E2E | unchanged | pending |
| Workflow | request -> sample evidence | pending |
| Safety boundary | no market/backtest/profitability dependency or mutation | pending |

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

Implement the pure sampler with no market-data imports. Persist enough
per-stratum evidence to reconstruct every selected date from request facts
alone, then add deterministic tests before any workflow integration.

## Completion

Final implementation commit:
CI run:
Sampling workflow evidence:
Remaining unassessed items:
