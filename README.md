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

## Agent-first development

All non-trivial repository development is governed by [AGENTS.md](AGENTS.md).

The agent workflow is intentionally plan-first and interruption-safe:

```text
Inspect
  -> execution plan
  -> implement small slices
  -> targeted verification
  -> CI: static + code + API + E2E
  -> machine-readable evidence
  -> completed plan
```

Work in progress lives under `docs/exec-plans/active/`. Strategy E2E targets
are versioned in `tests/e2e/strategy-targets.json`; CI uploads the actual-vs-
target evidence artifact on every E2E run, including failures.

See:

- [Agent repository contract](AGENTS.md)
- [Agent workflow](docs/agents/workflow.md)
- [Testing and evidence contract](docs/agents/testing.md)
- [Execution-plan template](docs/exec-plans/TEMPLATE.md)

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

### 1. Zero-configuration exploration

This mode uses in-memory repositories. It is appropriate for learning and one-shot analysis; state disappears when the command exits.

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

### 2. Persistent paper workflow

Use PostgreSQL when you want subsequent commands to inspect, refresh, close, and compare the same Position.

```bash
docker compose up -d postgres

export DATABASE_URL='postgresql://future_opportunity:future_opportunity@localhost:5432/future_opportunity'

uv run arb db-migrate

# This simulation is now persisted.
uv run arb simulate funding-carry \
  --venue binance \
  --base BTC \
  --capital 1000

uv run arb positions
uv run arb position-show <position-id>
uv run arb position-refresh <position-id>
uv run arb position-close <position-id>

uv run arb opportunity-show <opportunity-id>
uv run arb opportunity-history <opportunity-id>
```

When `DATABASE_URL` is set, CLI `discover` and `simulate` automatically use PostgreSQL. Without it they remain dependency-free, in-memory commands.

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

## Liquidity-bounded deployment

V0 treats requested capital and executable market liquidity as different facts.
The policy is defined by [ADR-0005](docs/adr/0005-liquidity-bounded-deployment.md).

Default behavior is **strict**:

```text
requested target notional > safe capacity at max impact
=> Opportunity is not qualified
=> paper execution is rejected
```

The system never silently reduces the user's capital intent.

Explicit partial deployment is available when the caller accepts unused capital:

```bash
uv run arb discover funding-carry \
  --venue binance \
  --base BTC \
  --capital 10000 \
  --liquidity-policy partial \
  --max-impact-bps 10
```

A partial StrategyPlan freezes:

```text
requested capital
requested spot notional
safe capacity
actual spot / hedge notional
reserve
futures margin
unused capital
max impact
```

Returns continue to use requested total capital as the denominator. Idle capital
therefore lowers return-on-capital instead of disappearing from the economics.

The Web workbench exposes the same explicit Strict/Partial choice. Partial is
never selected automatically.

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

GET  /v1/opportunities/<opportunity-id>
GET  /v1/opportunities/<opportunity-id>/observations

GET  /v1/positions
POST /v1/positions/<position-id>/refresh
POST /v1/positions/<position-id>/close
GET  /v1/history
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

The API and CLI use in-memory repositories by default so exploratory usage remains dependency-free.

For persistent Opportunity and Position history:

```bash
docker compose up -d postgres

export DATABASE_URL='postgresql://future_opportunity:future_opportunity@localhost:5432/future_opportunity'

uv sync --all-extras --dev
uv run arb db-migrate
uv run uvicorn future_opportunity.api:app --reload
```

`arb db-migrate` applies all pending SQL migrations in filename order, records their SHA-256 checksums, is idempotent on already-applied migrations, and rejects checksum drift.

When `DATABASE_URL` is present, API requests plus CLI `discover` / `simulate` use PostgreSQL. Without it, the same business use cases run against in-memory repositories.

## Manage paper positions

The Web/API management lifecycle is:

```text
HEDGED
  -> refresh
ACTIVE / DEGRADED
  -> close
CLOSED
```

Refresh uses current public order books and the **capital/fee policies frozen in the original StrategyPlan**. It never silently reuses today's defaults.

API:

```text
GET  /v1/positions
GET  /v1/positions/{id}
POST /v1/positions/{id}/refresh
POST /v1/positions/{id}/close
GET  /v1/history
```

Persistent CLI management requires `DATABASE_URL`:

```bash
uv run arb positions
uv run arb position-show <position-id>
uv run arb position-refresh <position-id>
uv run arb position-close <position-id>
```

A paper close creates a separate immutable `CLOSE` execution with exit fills. The closed Position itself has no remaining legs and zero delta; open/close fills remain the historical evidence.

### Expected vs Current / Realized

Every StrategyPlan freezes:

- expected return character
- expected horizon
- expected net return / PnL
- expected costs
- capital policy
- execution fee policy

History compares this entry-time expectation with the current assessed return.

For Funding Carry, public market data does not prove exact accrued funding cash flow for the simulated position. Until explicit settlement evidence is available, the `funding` return component is marked **unassessed** rather than assumed to be zero. A closed Funding Carry paper position is therefore reported as `realized_partial`.

Cash-and-Carry can be marked `realized` when the close evidence is complete. If the dated future has already delivered, OKX public delivery history supplies the settlement price; the future close is recorded as `FillSource.SETTLEMENT`, while the spot leg is sold against the current order book. Any spot move after delivery is attributed to residual directional PnL rather than basis convergence.

See [ADR-0003](docs/adr/0003-unassessed-return-components.md) and [ADR-0004](docs/adr/0004-public-delivery-settlement.md).

## Historical backtest evidence

The repository keeps deterministic reference E2E and real historical replay as
two separate evidence layers.

Pinned historical smoke fixtures live under:

```text
tests/fixtures/historical/
```

The committed fixtures are **compact derivatives** of larger official OKX
archives. Raw exchange archives remain outside git. Each manifest records:

- official source endpoint / filename;
- raw SHA-256;
- parent canonical SHA-256;
- preparation workflow run + artifact ID + artifact ZIP SHA-256;
- instrument metadata provenance;
- sample timestamps and staleness bounds;
- the frozen 10,000 USDT scenario and the exact base quantity preserved;
- the compact-depth derivation rule.

The compact order books retain at least 120% of the frozen scenario's required
base quantity on both sides. They are therefore suitable for deterministic
replay of that frozen scenario, but are **not** presented as full-book
market-capacity datasets.

Current pinned real-market evidence includes:

- OKX BTC-USDT Funding Carry: 2026-09-01 and 2026-09-02;
- OKX BTC-USDT / BTC-USDT-260626 Cash-and-Carry: 2026-06-01 and
  2026-06-02.

Both current historical cases are legitimate negative examples under the
existing default cost assumptions: the product workflow rejects them because
expected net return is not positive. This is evidence that qualification works;
it is not a reason to lower the deterministic reference targets.

Run the offline historical smoke directly:

```bash
uv run python scripts/run_pinned_historical_smoke.py
uv run pytest tests/e2e/test_historical_backtest_acceptance.py -v
```

CI workflow `Historical Backtest Smoke` uploads machine-readable historical
evidence even on failure.

Historical acceptance follows
[ADR-0007](docs/adr/0007-progressive-historical-acceptance-policy.md).

V0 uses a **provenance-and-semantics gate**:

- fixture checksums and source provenance must verify;
- replay must be deterministic and offline;
- compact-fixture derivation and quantity normalization must remain valid;
- pinned real-market cases must reproduce their expected business qualification
  semantics;
- historical returns are reported but do not determine pass/fail.

This means a real historical **negative** opportunity can correctly pass the
historical gate when the production workflow rejects it for the expected reason.
The deterministic reference targets in `tests/e2e/strategy-targets.json`
remain unchanged and continue to gate the synthetic/reference strategy E2E.

The active policy is versioned in
`tests/e2e/historical-target-policy.json`. The transition to a distribution-
based historical return gate becomes eligible only after at least **30 distinct
pinned entry-market days per strategy**; **90 days per strategy** is preferred
before freezing stable thresholds. Activation still requires a separate ADR and
human approval. Distribution thresholds must not be copied automatically from
the deterministic reference targets.

### Adding historical market days

Historical acquisition is resumable and separated from CI gating.

Funding Carry can prepare up to 31 UTC market days per batch:

```text
Actions -> Prepare Funding Historical Batch
start_date = YYYY-MM-DD
end_date   = YYYY-MM-DD
```

Each date is an independent matrix job with `fail-fast=false`. Successful jobs
produce:

```text
full provenance artifact
+
commit-ready compact fixture artifact
```

Cash-and-Carry uses two steps:

```text
Actions -> Discover Cash Historical Batch
  -> official historical FUTURES archive identity / expiry evidence

Actions -> Prepare Cash Historical Batch
  -> explicit entry/exit/future/expiry case
  -> full provenance + commit-ready compact fixture
```

A prepared artifact does **not** count toward Stage-2 readiness. A day counts
only after its compact fixture is committed under
`tests/fixtures/historical/`, added to `corpus-index.json`, and accepted by
the offline corpus validator and Historical Backtest Smoke.

Readiness is computed from distinct `entry_market_date` values in the validated
versioned corpus, separately for each required strategy:

```text
minimum_ready
  = every required strategy has >= 30 distinct pinned entry-market days

preferred_ready
  = every required strategy has >= 90 distinct pinned entry-market days
```

Duplicate strategy/date entries fail closed.

## Architecture

The system follows a domain-centric Ports & Adapters design.

See:

- [System Design Baseline v0.1](docs/design-baseline-v0.1.md)
- [ADR-0001: Conservative Isolated Capital Model](docs/adr/0001-isolated-capital-model.md)
- [ADR-0002: Explicit Unassessed Risk State](docs/adr/0002-unassessed-risk-state.md)
- [ADR-0003: Explicit Unassessed Return Components](docs/adr/0003-unassessed-return-components.md)
- [ADR-0004: Public Delivery Settlement as Execution Evidence](docs/adr/0004-public-delivery-settlement.md)
- [ADR-0005: Liquidity-Bounded Deployment Policy](docs/adr/0005-liquidity-bounded-deployment.md)
- [ADR-0006: Historical Backtest Dataset Provenance](docs/adr/0006-historical-backtest-dataset-provenance.md)
- [ADR-0007: Progressive Historical Acceptance Policy](docs/adr/0007-progressive-historical-acceptance-policy.md)

Changes to frozen domain boundaries, return semantics, capital semantics, or the paper/live safety boundary require an ADR.
