# ADR-0002: Explicit Unassessed Risk State

- Status: Accepted
- Date: 2026-10-04

## Context

The V0 design requires explainable risk invariants including MarginSafety and VenueExposure.

Some invariants cannot be evaluated correctly from public market data alone:

- MarginSafety depends on account mode, collateral, maintenance-margin tiers, haircuts, and venue-specific liquidation rules.
- VenueExposure depends on portfolio-wide capital and positions, not one isolated Position.

Marking these invariants as SATISFIED without evidence would create false assurance.

## Decision

Add an explicit `UNASSESSED` invariant state.

V0 invariant states are:

```text
SATISFIED
WARNING
VIOLATED
UNASSESSED
```

`UNASSESSED` means required evidence is unavailable. It is not equivalent to low risk and must not be rendered as green in future UI.

V0 evaluates directly where evidence exists:

- DeltaNeutrality
- LegIntegrity
- CarryPositive
- ExitLiquidity

V0 reports as UNASSESSED where account/portfolio evidence is absent:

- MarginSafety
- VenueExposure

## Consequences

- Risk output is honest about evidence coverage.
- Future authenticated account adapters can replace UNASSESSED MarginSafety with a real evaluation.
- Future Portfolio Context can replace UNASSESSED VenueExposure.
- Database risk state constraints must include `unassessed`.
