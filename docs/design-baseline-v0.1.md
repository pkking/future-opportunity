# System Design Baseline v0.1

Status: **Baseline**  
Date: 2026-10-03  
Scope: **V0 / Paper Trading**

## Product definition

future-opportunity is a market-neutral arbitrage workbench for:

```text
Discover -> Understand -> Plan -> Execute -> Maintain Invariants -> Attribute Returns -> Learn
```

V0 consumes real market data but **must never submit real exchange orders**.

## Core domain language

```text
MarketObservation
      |
      v
Opportunity
      |
      v
StrategyDefinition
      |
      v
StrategyPlan
      |
      v
Execution -> Order -> Fill
      |
      v
Position
   /      \
Return    Risk
```

### Architecture invariants

1. Users consume Opportunities, not raw exchange data.
2. StrategyDefinition is distinct from StrategyPlan.
3. Position represents the complete arbitrage combination, not one venue leg.
4. Position is derived from Fill.
5. Every StrategyPlan references the OpportunityObservation used to create it.
6. Returns must be attributable.
7. Risks must be explainable through invariants.
8. Domain code must not depend on exchange SDKs, HTTP frameworks, or persistence frameworks.
9. Paper and live execution use the same domain objects.
10. V0 cannot submit real exchange orders.
11. Professional domain concepts are preserved; Quickstarts reduce onboarding cost.
12. Future automated execution must be recoverable and idempotent.

## V0 scope

- Venues: Binance, OKX
- Assets: BTC, ETH
- Strategies: Funding Carry, Cash-and-Carry
- Real market data
- Opportunity lifecycle and history
- StrategyPlan
- Paper execution against real order books
- Position lifecycle
- Explainable Risk Invariants
- Return Attribution
- Expected vs Realized analysis
- REST API, CLI, basic Web UI

Explicitly deferred:

- Live trading
- Full automation
- Cross-venue execution
- Bybit
- ML funding prediction
- Portfolio optimization
- Multi-user/RBAC
- Temporal

## Architecture

Domain-centric Ports & Adapters.

```text
Exchange APIs
     |
     v
Exchange Adapters
     |
     v
Canonical Market Model
     |
     v
Domain
     |
     v
Application
   /  |  \
 API CLI Web
```

Persistence uses PostgreSQL with transactional current state, append-only domain events, and a transactional outbox. Full Event Sourcing is not part of V0.

CCXT may be used inside exchange adapters, but CCXT types must not enter the domain layer.

## Return semantics

Returns are either:

- **Variable** — e.g. Funding Carry.
- **Convergent** — e.g. Cash-and-Carry basis convergence toward expiry.

Annualized return is a comparison metric, not a promised yield.

## Risk semantics

The Risk Engine evaluates explicit invariants rather than an opaque score.

Initial invariants:

- DeltaNeutrality
- MarginSafety
- CarryPositive
- ExitLiquidity
- LegIntegrity
- VenueExposure

## Development sequence

Implement vertical slices rather than horizontal infrastructure layers.

First vertical slice:

```text
Binance BTC
 -> Spot + Perpetual market data
 -> FundingCarryDetector
 -> Opportunity
 -> OpportunityObservation
 -> StrategyPlan
 -> PaperExecution
 -> Position
 -> Funding Settlement
 -> ReturnAttribution
 -> RiskInvariant
 -> Close
 -> Expected vs Realized
```

Then extend to ETH, OKX, and Cash-and-Carry.

## Change policy

Changes to domain boundaries, opportunity semantics, strategy/plan separation, position source of truth, return model, risk invariant model, paper/live safety boundary, persistence architecture, execution architecture, or external framework dependencies require an ADR.
