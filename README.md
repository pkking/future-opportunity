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

## V0 scope

Strategies:

- Funding Carry: long spot + short perpetual
- Cash-and-Carry: long spot + short dated future

Venues/assets:

- Binance
- OKX
- BTC
- ETH

Current implementation supports the Funding Carry vertical slice on Binance and OKX for BTC/ETH.

## Quickstart

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras --dev

uv run arb quickstart funding-carry
uv run arb discover BTC --capital 1000
uv run arb simulate BTC --capital 1000
```

`discover` reads public spot/perpetual market data through a Venue adapter and produces an Opportunity-level funding-carry evaluation. OKX swap contract sizes are normalized from contract count into base-asset quantity before entering the domain model.

`simulate` walks the real order book to create simulated fills and a delta-neutral paper Position.

Fee values are explicit assumptions. The defaults are examples for simulation and are **not** a claim about the fee tier of any Binance account:

```bash
uv run arb discover BTC \
  --capital 10000 \
  --spot-fee-bps 10 \
  --perpetual-fee-bps 5
```

## API

```bash
uv run uvicorn future_opportunity.api:app --reload
```

Then use:

```text
GET  /healthz
GET  /v1/opportunities/funding-carry/BTC
POST /v1/simulations/funding-carry/BTC
```

## Architecture

The system follows a domain-centric Ports & Adapters design. Exchange naming and API semantics are isolated behind adapters.

See `docs/design-baseline-v0.1.md` for the frozen V0 design baseline.

## Development policy

Changes to the frozen domain boundaries or paper/live safety boundary require an ADR.


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

When `DATABASE_URL` is present, the API uses the PostgreSQL Repository adapter. Without it, the same application use case runs against the in-memory adapter.
