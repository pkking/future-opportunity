# future-opportunity

A market-neutral arbitrage workbench for discovering, analyzing, simulating, and eventually executing explainable crypto arbitrage strategies.

## V0 scope

V0 is intentionally **paper-trading only**. It uses real market data, but must never submit real exchange orders.

Initial strategies:

- Funding Carry: long spot + short perpetual
- Cash-and-Carry: long spot + short dated future

Initial venues/assets:

- Binance
- OKX
- BTC
- ETH

## Architecture

The system follows a domain-centric Ports & Adapters design. Core domain concepts are:

`Opportunity -> StrategyDefinition -> StrategyPlan -> Execution -> Position -> Return + Risk`

See `docs/design-baseline-v0.1.md` for the frozen V0 design baseline.

## Development status

Repository bootstrap in progress.
