# future-opportunity

A professional, explainable market-neutral arbitrage workbench.

The product models the business lifecycle directly:

```text
Opportunity
  -> StrategyDefinition
  -> StrategyPlan
  -> Execution
  -> Position
  -> Return + Risk
```

## Safety boundary

V0 is intentionally **paper-trading only**.

It reads real public market data, but the repository contains no live-order API path and requires no exchange API key.

## V0 implementation status

Implemented vertical slices:

- Funding Carry: long spot + short perpetual
  - Binance BTC / ETH
  - OKX BTC / ETH
- Cash-and-Carry: long spot + short dated future
  - OKX USDT-settled linear futures
  - BTC / ETH

Both strategies share the same Opportunity, StrategyPlan, Position, Capital Allocation, Risk, and Paper Fill domain objects.

## Quickstart

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras --dev

# Funding Carry
uv run arb quickstart funding-carry
uv run arb discover funding-carry --venue binance --base BTC --capital 1000
uv run arb simulate funding-carry --venue binance --base BTC --capital 1000

# Cash-and-Carry
uv run arb quickstart cash-and-carry
uv run arb discover cash-and-carry --venue okx --base BTC --capital 1000
```

Cash-and-Carry discovery can return multiple dated futures. Each expiry is a distinct Opportunity. Simulation therefore requires an explicit future instrument:

```bash
uv run arb simulate cash-and-carry \
  --venue okx \
  --base BTC \
  --capital 1000 \
  --future-instrument-id 'okx:BTC-USDT-XXXXXX:future'
```

The simulator uses the **same market snapshot and OpportunityObservation** that generated the StrategyPlan. It does not invent a new observation ID or silently select another expiry.

## Business semantics

### Funding Carry

```text
BUY  Spot
SELL Perpetual
```

Return character: **Variable**

Primary return source: funding payments.

The estimator derives the recent funding cadence from exchange history rather than assuming that every venue always settles at an eight-hour interval.

### Cash-and-Carry

```text
BUY  Spot
SELL Dated Future
```

Return character: **Convergent**

Primary return source: positive futures basis converging toward spot at expiry.

The system reports both:

- expected net return **to expiry**
- annualized equivalent for comparison

The annualized value is not presented as a promised yield.

## Capital model

V0 uses the conservative isolated-capital model defined by [ADR-0001](docs/adr/0001-isolated-capital-model.md).

Capital is explicitly split into:

```text
Reserve
+
Spot purchase
+
Futures margin
```

For a dated future with basis, the futures quote-notional may differ from the spot quote-notional even when base-asset quantity is exactly hedged. The capital allocator accounts for this ratio.

Defaults:

```text
Reserve ratio     10%
Futures leverage   1x
Maximum leverage 1.2x
```

This intentionally avoids assuming exchange-specific unified/portfolio-margin collateral behavior.

## Costs

Fee values are **explicit assumptions**. Defaults are examples for paper simulation and are not claims about the fee tier of a specific exchange account.

Funding example:

```bash
uv run arb discover funding-carry \
  --venue binance \
  --base BTC \
  --capital 10000 \
  --spot-fee-bps 10 \
  --derivative-fee-bps 5 \
  --reserve-ratio 0.10 \
  --futures-leverage 1
```

Cash-and-Carry additionally exposes `--exit-buffer-bps` for uncertain expiry/exit friction.

Paper execution walks the real order book instead of filling at the mid price.

## API

```bash
uv run uvicorn future_opportunity.api:app --reload
```

Examples:

```text
GET  /healthz

GET  /v1/opportunities/binance/funding-carry/BTC
POST /v1/simulations/binance/funding-carry/BTC

GET  /v1/opportunities/okx/cash-and-carry/BTC
POST /v1/simulations/okx/cash-and-carry/BTC?future_instrument_id=<id>
```

## Exchange anti-corruption layer

Exchange-specific instrument naming and quantity units do not enter the domain model.

For example, OKX derivative order-book `sz` is contract count. The OKX adapter uses public instrument metadata such as `ctVal` / `ctValCcy` to normalize derivative liquidity into base-asset quantity before passing it to strategy code.

## Opportunity lifecycle

A continuously valid market condition reuses the same active Opportunity aggregate and appends immutable OpportunityObservations.

```text
DISCOVERED -> QUALIFIED -> EXPIRED
```

If the opportunity disappears and later reappears, a new Opportunity lifecycle begins.

## Optional PostgreSQL persistence

The API uses an in-memory Opportunity repository by default, which keeps Quickstart dependency-free.

For persistent Opportunity lifecycle history:

```bash
docker compose up -d postgres

export DATABASE_URL='postgresql://future_opportunity:future_opportunity@localhost:5432/future_opportunity'

psql "$DATABASE_URL" -f migrations/0001_v0_core.sql

uv sync --all-extras --dev
uv run uvicorn future_opportunity.api:app --reload
```

When `DATABASE_URL` is present, the API uses the PostgreSQL Repository adapter. Without it, the same application use cases run against the in-memory adapter.

## Architecture

The system follows a domain-centric Ports & Adapters design.

See:

- [System Design Baseline v0.1](docs/design-baseline-v0.1.md)
- [ADR-0001: Conservative Isolated Capital Model](docs/adr/0001-isolated-capital-model.md)

Changes to frozen domain boundaries, return semantics, capital semantics, or the paper/live safety boundary require an ADR.
