# ADR-0005: Liquidity-Bounded Deployment Policy

- Status: Accepted
- Date: 2026-10-05

## Context

A user's capital intent and the market's executable liquidity are different
facts.

Example:

```text
requested capital                 = 10,000 USDT
isolated-capital target notional = 4,500 USDT
safe visible capacity @ 10 bps   = 3,000 USDT
```

Silently deploying only 3,000 USDT would change the user's intent. Attempting
4,500 USDT would violate the accepted market-impact limit.

V0 already observes order-book capacity at bounded VWAP impact, but before this
decision that capacity was informational only.

## Decision

V0 introduces an explicit liquidity deployment policy.

```text
STRICT  (default)
PARTIAL (explicit opt-in)
```

Both policies require an explicit `max_impact_bps`, defaulting to 10 bps.

### STRICT

If the capital-derived target notional exceeds hedged visible capacity at the
configured impact limit:

```text
OpportunityQualification = false
reason = requested_notional_exceeds_liquidity_limit
simulation/execution = rejected
```

No silent resizing is allowed.

### PARTIAL

Partial deployment is allowed only when explicitly selected by the caller.

```text
actual spot notional = min(requested spot notional, safe visible capacity)
```

The StrategyPlan freezes the deployment assessment, including:

- policy;
- max impact;
- requested capital;
- requested spot notional;
- capacity spot notional;
- actual spot notional;
- actual hedge notional;
- reserve amount;
- futures margin;
- unused capital;
- whether deployment is partial.

Returns remain measured against **requested total capital**, so idle capital is
economically visible rather than disappearing from the denominator.

## Qualification semantics

Liquidity is a first-class qualification condition.

An Opportunity may remain observable and persisted even when STRICT deployment
is rejected. It must not execute while unqualified.

Under explicit PARTIAL policy, the Opportunity may qualify if the safe partial
deployment remains economically positive and has non-zero executable capacity.

## Execution semantics

Execution must use the exact deployment frozen in the StrategyPlan.

It must never recompute a larger target from capital at execution time.

The observed market impact of each entry leg must remain within the Plan's
`max_impact_bps` constraint.

## Consequences

- Default behavior preserves the user's capital intent.
- Partial deployment is visible and opt-in.
- Unused capital is explicit.
- Opportunity, Plan, execution, API, CLI, Web, and E2E all share one deployment
  model.
- Changing these semantics requires a new ADR.
