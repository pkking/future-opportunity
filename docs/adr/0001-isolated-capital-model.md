# ADR-0001: Conservative Isolated Capital Model

- Status: Accepted
- Date: 2026-10-04

## Context

Funding Carry and Cash-and-Carry are delta-neutral only if both legs can remain open.

A previous implementation treated a 10,000 USDT account with a 10% reserve as capable of holding roughly 9,000 USDT of spot and 9,000 USDT of futures notional while also describing the futures leg as low leverage. That assumption is only valid under specific unified/portfolio-margin collateral rules and therefore is not venue-independent.

For a portable strategy model, futures margin must be accounted for explicitly.

## Decision

V0 uses a conservative isolated-capital model.

For total capital `C`, reserve ratio `R`, and futures leverage `L`:

```text
usable capital = C * (1 - R)

hedged notional N satisfies:

N + N / L <= usable capital

therefore:

N = usable capital / (1 + 1/L)
```

The first term is the spot purchase. The second term is futures margin.

Default V0 assumptions:

```text
reserve ratio    = 10%
futures leverage = 1.0x
max leverage     = 1.2x
```

For 10,000 USDT:

```text
reserve          = 1,000
spot notional    = 4,500
futures notional = 4,500
futures margin   = 4,500
```

Funding and execution returns are reported against **total capital**, not only the futures notional.

## Alternatives

### Assume unified/portfolio margin

Rejected as the V0 default because collateral eligibility, haircuts, liquidation rules, and capital efficiency are venue/account specific.

### Ignore futures margin

Rejected because it materially overstates deployable notional and expected return on capital.

## Consequences

- V0 reported return on capital is deliberately conservative.
- Funding Carry remains independent from exchange-specific margin systems.
- A future Unified/Portfolio Margin capability should be modeled as a separate `CapitalAllocator`/margin adapter.
- Strategy economics must expose reserve amount, hedged notional, and futures margin.
- Any future change to this default capital model requires a new ADR.
