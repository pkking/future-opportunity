# ADR-0007: Progressive Historical Acceptance Policy

- Status: Accepted
- Date: 2026-10-05

## Context

The repository now has two different kinds of strategy evidence:

1. deterministic reference scenarios, designed to prove that a strategy can meet
   explicit return/risk targets under a controlled market state;
2. pinned real historical market replay, designed to prove that the same product
   workflow behaves correctly on auditable external market evidence.

The first real historical datasets are legitimate negative examples. Funding
Carry on 2026-09-01 and Cash-and-Carry on 2026-06-01 are correctly rejected by
the production qualification workflow under the existing default cost model.

Requiring every historical period to meet the deterministic reference return
threshold would confuse two different questions:

```text
Reference E2E:
Can the strategy implementation satisfy the intended business target
when a qualifying opportunity exists?

Historical replay:
Did the scanner/strategy correctly interpret what actually happened
in this market period?
```

Historical data is not yet broad enough to define statistically meaningful
return-distribution thresholds.

## Decision

Historical acceptance evolves in two stages.

### Stage 1 — V0 provenance-and-semantics gate

The active historical policy is versioned in:

```text
tests/e2e/historical-target-policy.json
```

Historical CI MUST gate:

- fixture checksum and source provenance validity;
- deterministic offline replay;
- instrument/quantity normalization evidence;
- frozen compact-fixture derivation semantics;
- the production qualification result for pinned historical cases;
- machine-readable evidence generation.

Historical CI MUST NOT fail merely because a real historical period does not
reach the deterministic reference return threshold.

The deterministic reference targets remain unchanged and continue to gate their
own reference E2E scenarios.

Reference targets may be displayed beside historical actuals for context, but
their use in historical evidence is explicitly `reporting_only`.

A historical negative opportunity is a passing historical test when the
production workflow rejects it for the expected business reason.

### Stage 2 — historical distribution gate

The repository becomes eligible to propose a distribution-based historical gate
after accumulating at least:

```text
30 distinct market days per strategy
```

Ninety distinct market days per strategy is the preferred evidence base before
freezing stable distribution thresholds.

Reaching 30 or 90 days does **not** automatically activate Stage 2.

Stage 2 requires a separate ADR and human approval defining:

- the aggregation window;
- opportunity qualification-rate semantics;
- which return statistic is gated (for example P25/P50/P90 or lower bound);
- treatment of zero-opportunity periods;
- risk/capacity/evidence-completeness requirements;
- acceptable sample-size and coverage rules;
- exact thresholds.

Those thresholds MUST be derived as a product decision from accumulated
historical evidence and strategy objectives. They MUST NOT be copied
automatically from deterministic reference targets and MUST NOT be relaxed only
to make observed history pass.

## Consequences

- Real negative markets remain useful regression evidence.
- Reference E2E continues to protect the intended strategy capability target.
- Historical CI immediately becomes a meaningful hard gate without pretending
  that two pinned days define a return distribution.
- The transition to statistical acceptance has an explicit evidence threshold
  and cannot happen silently.
- Future agents can determine the active historical policy from repository facts
  without relying on conversation history.
