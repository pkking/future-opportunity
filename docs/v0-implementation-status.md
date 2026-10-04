# V0 Implementation Status

Status: **Implemented baseline with explicit evidence limitations**  
Date: 2026-10-04

This document maps the frozen V0.1 design baseline to the current repository implementation.

## End-to-end lifecycle

```text
Real public market data
  -> Opportunity discovery
  -> OpportunityObservation
  -> StrategyPlan with frozen economics/policies
  -> real-order-book Paper Execution
  -> Position
  -> Return Attribution + Risk Invariants
  -> Refresh / Manage
  -> auditable Paper Close
  -> Expected vs Current / Realized History
```

## Baseline coverage

| Baseline capability | Status | Evidence |
|---|---|---|
| Binance market data | Implemented | Funding Carry adapter |
| OKX market data | Implemented | Funding Carry + dated futures adapters |
| BTC / ETH | Implemented | Venue-independent base asset input |
| Funding Carry | Implemented | Discover / simulate / refresh / close |
| Cash-and-Carry | Implemented | Discover / simulate / refresh / live close / expiry delivery close |
| Opportunity lifecycle | Implemented | Active lifecycle + immutable observations |
| StrategyDefinition | Implemented | Versioned strategy catalog |
| StrategyPlan | Implemented | Observation reference + frozen economics/capital/fees/liquidity deployment |
| Paper execution | Implemented | Real order-book walk, liquidity-impact bound, immutable fills, public delivery settlement evidence |
| Position lifecycle | Implemented | HEDGED / ACTIVE / DEGRADED / CLOSED |
| Return attribution | Implemented | Evidence-aware components |
| Risk invariants | Implemented | Explainable invariant reports |
| Expected vs Realized | Implemented | History view; incomplete evidence is explicit |
| PostgreSQL persistence | Implemented | Integration-tested migrations/repositories |
| Domain events / outbox | Implemented | Transactional DB writes for Opportunity/Position lifecycle |
| CLI | Implemented | Discover / simulate / persistent manage commands |
| REST API | Implemented | Discovery / simulation / position management / history |
| Basic Web UI | Implemented | Discover / Analyze / Positions / History |
| Live trading | Not in V0 | Explicit safety boundary |

## Liquidity deployment boundary

ADR-0005 makes liquidity capacity part of Opportunity qualification.

```text
STRICT (default):
  oversized capital intent -> unqualified -> no execution

PARTIAL (explicit):
  actual notional = safe capacity
  unused capital  = explicit
  return denominator = requested total capital
```

The frozen deployment travels with StrategyPlan and is reused by simulation,
refresh, close, persistence, API, CLI, and Web.

## Deliberately unassessed evidence

### Funding cash flow

Funding Carry cannot claim an exact paper funding cash flow from the current public snapshot alone. Until settlement-grade evidence exists, the `funding` component remains unassessed.

A closed Funding Carry paper position can therefore be:

```text
CLOSED + realized_partial
```

rather than falsely reported as a complete realized return.

See ADR-0003 and ADR-0004.

### MarginSafety

Public market data does not establish account margin mode, collateral, maintenance tiers, or liquidation state.

Status: `UNASSESSED`.

### VenueExposure

A single Position does not establish portfolio-wide venue exposure.

Status: `UNASSESSED`.

See ADR-0002.

## Transactional outbox boundary

V0 atomically writes domain events and matching outbox rows in the same PostgreSQL transaction as the associated aggregate change.

V0 has no asynchronous event consumer, so an outbox delivery dispatcher is intentionally not required yet. It should be added together with the first real consumer, preserving the existing outbox contract.

## V0 safety invariant

There is no live-order endpoint, API-key requirement, or authenticated trading adapter in V0.

```text
real market data
+
paper fills
+
paper position lifecycle
!=
real exchange orders
```

Any future live execution capability requires a new architecture decision and must preserve recoverability/idempotency.
