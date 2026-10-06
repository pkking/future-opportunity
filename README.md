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

### Pre-registering historical market days

Dates intended to support future Stage-2 distribution design should be selected
**before** looking at strategy outcomes. Use the read-only sampler:

```text
Actions -> Sample Historical Market Days

strategy       = funding-carry | cash-and-carry
start_date     = inclusive UTC date
end_date       = inclusive UTC date
sample_size    = requested number of days
seed           = stable pre-registration seed
policy_version = systematic-stratified-sha256-v1
```

The v1 policy partitions the complete calendar population into ordered strata
and selects one day per stratum from a SHA-256-derived offset. The hash domain
includes policy version, strategy, seed, study-window boundaries and stratum
index. It never reads prices, funding rates, basis, volatility, qualification
or returns.

The evidence records the full request, population size, every stratum boundary,
hash input/digest, offset and selected date. Replaying the same request must
reproduce the entire artifact exactly.

If a selected date has no usable source data, record it as an explicit
exclusion. Do **not** replace it with a neighboring or profitable date after
observing results. Any future replacement policy needs a new version.

Verified golden self-test:

```text
run:      37482498880
artifact: historical-market-day-sample-37482498880
id:       11421537670

Funding Carry / 2026-01-01..2026-01-31 / n=5
=> 2026-01-01, 2026-01-08, 2026-01-13, 2026-01-22, 2026-01-29
```

Existing manually selected pinned fixtures remain valid Stage-1 regression
evidence. They must not be retroactively described as an unbiased market-wide
sample.

### Adding historical market days

For a reviewed multi-day preparation set, prefer the acquisition campaign:

```text
Actions -> Acquire Historical Campaign
```

Input is an explicit versioned JSON object:

```json
{
  "schema_version": 1,
  "acquisition_id": "stage1-acquisition-01",
  "planner_campaign_prefix": "stage1-review-01",
  "funding": {
    "start_date": "2026-09-04",
    "end_date": "2026-09-06"
  },
  "cash_cases": [
    {
      "entry_at": "2026-06-04T00:15:00+00:00",
      "exit_at": "2026-06-25T00:15:00+00:00",
      "future_id": "BTC-USDT-260626",
      "expiry_at": "2026-06-26T08:00:00+00:00"
    }
  ]
}
```

The acquisition manifest is bounded to **31 total items**. Funding accepts
either an inclusive UTC date range **or** an explicit chronological
`market_dates` list; the two forms are mutually exclusive. Pre-registered
samples use the explicit-date form so unsampled days are never filled in.
Cash remains explicit: the acquisition layer never infers a holding period or
expiry case from discovery output.

The workflow reuses the existing Funding/Cash preparation workflows. It has
`contents: read` only and does not change
`tests/fixtures/historical/`, push review branches, or create PRs.

After the entire acquisition run completes successfully, a
`workflow_run` trigger starts **Plan Historical Corpus Campaign** against that
exact completed run. The planner retrieves the normalized
`historical-acquisition-control` artifact, verifies every compact/parent
artifact pair, compares only against the committed corpus, and uploads
review-only campaign waves. A failed or partial acquisition is never planned.

Verified integration example:

```text
Acquire run 37475817137
  Funding 2026-09-04 + Cash 2026-06-03
    -> success

Planner workflow_run 37476495413
  baseline pinned: Funding 2 / Cash 2
  selected: 2
  projected if later reviewed+merged: Funding 3 / Cash 3
  wave: selftest-acquisition-review-wave-001.json
```

This projection is not pinned readiness and performs no promotion.

For lower-level or one-off preparation, the individual batch workflows remain
available.

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

Cash-and-Carry uses discovery plus an explicit case-planning step:

```text
Actions -> Discover Cash Historical Batch
  -> official historical FUTURES archive identity / expiry evidence

Actions -> Plan Cash Acquisition Cases
  discovery_run_id = exact successful discovery run
  future_id        = explicit BTC-USDT expiry future
  expiry_at        = explicit UTC expiry
  exit_at          = explicit UTC strategy exit
  entry_time_utc   = explicit UTC clock time
  -> acquisition-ready cash_cases[]
  -> excluded-date diagnostics

Actions -> Prepare Cash Historical Batch
  -> explicit entry/exit/future/expiry case
  -> full provenance + commit-ready compact fixture
```

The Cash case planner is read-only. It never chooses the future, expiry, exit
date, or holding period. It only verifies discovery evidence and expands the
operator's explicit template across matching market dates. A discovery date
with no unique future archive, a mismatched future ID, or an entry not before
the explicit exit is reported as excluded rather than silently rewritten.

Verified example: planner run `37477835622` consumed discovery run
`37434982233` and produced the explicit 2026-06-03 BTC-USDT-260626 case with
no exclusions. Evidence artifact: `11420145596`.

To combine reviewed sampling/case-plan evidence without copying JSON by hand,
use the read-only composer:

```text
Actions -> Compose Historical Acquisition Manifest

acquisition_id                       = explicit acquisition identifier
planner_campaign_prefix              = explicit future planner prefix

Funding, choose at most one:
  funding_start_date/end_date        = explicit inclusive UTC range
  funding_sample_run_id              = exact successful sampling run
  funding_sample_artifact_name       = exact sampling artifact

Optional Cash:
  cash_case_plan_run_id              = exact successful planner run
  cash_case_plan_artifact_name       = exact planner artifact
```

For a Funding sampling artifact, the composer independently verifies the exact
run/artifact and then **recomputes the deterministic draw from the embedded
request**. Any changed selected date, hash or stratum evidence fails closed.
Only a verified `funding-carry` sample is converted to explicit
`funding.market_dates`; gaps remain gaps.

For Cash, the composer revalidates the case-plan schema/evidence and strips
reporting-only fields such as `entry_market_date`. The final combined object
is passed back through the normal acquisition parser, reusing the 31-item and
UTC/future/expiry contracts.

It does **not** dispatch `Acquire Historical Campaign`. Acquisition remains a
separate explicit operator action after reviewing the composed manifest.

Verified sampled composer self-test:

```text
run:      37483512784
artifact: historical-acquisition-composer-37483512784
id:       11422581630

Funding sampled dates:
  2026-01-01, 2026-01-08, 2026-01-13, 2026-01-22, 2026-01-29
Cash:
  2026-06-03 / BTC-USDT-260626
```

A prepared artifact does **not** count toward Stage-2 readiness. A day counts
only after its compact fixture is committed under
`tests/fixtures/historical/`, added to `corpus-index.json`, and accepted by
the offline corpus validator and Historical Backtest Smoke.

### Promoting a prepared day

Promotion is explicit and review-based. Use:

```text
Actions -> Promote Historical Compact Artifact

source_run_id          = preparation workflow run ID
compact_artifact_name  = exact commit-ready compact artifact name
```

The promotion workflow:

```text
source run/artifact lookup
  -> verify compact artifact belongs to the exact run
  -> verify parent preparation artifact ID + SHA-256 from manifest
  -> validate commit_ready manifest + canonical checksums
  -> reject unexpected files/symlinks/identity collisions
  -> stage fixture + deterministic corpus-index update
  -> offline corpus + historical smoke verification
  -> create review branch
  -> create PR when repository policy permits
     OR emit machine-readable PR handoff
```

It never writes directly to `main` and never auto-merges. This repository
currently disables pull-request creation by `GITHUB_TOKEN`. In that case the
workflow keeps the validated branch and writes `pr-handoff.json`; a connected
GitHub integration or operator opens the PR from that exact branch without
changing corpus contents.

Re-running promotion for an already indexed fixture is a no-op only when the
manifest is structurally identical and all canonical evidence files are
byte-identical. JSON whitespace/key order is not treated as data drift.
Different canonical bytes, different provenance, or a duplicate strategy/date
with another dataset fail closed.

If a promotion run is interrupted, rerun it with the same source run and exact
compact artifact. If the fixture has already landed unchanged, the rerun is
idempotent. If a previous PR exists but is not merged, review that PR rather
than creating a second conflicting corpus fact.

A promotion PR—whether opened by the workflow or from its handoff—must pass the
normal repository CI plus `Historical Backtest Smoke` before merge.

### Promoting a corpus campaign

For corpus growth, prefer one explicit multi-day campaign over one PR per market
day:

```text
Actions -> Promote Historical Corpus Campaign
```

The input is a versioned JSON object containing exact preparation run/artifact
pairs:

```json
{
  "schema_version": 1,
  "campaign_id": "stage1-wave-03",
  "items": [
    {
      "source_workflow_run": "123456",
      "compact_artifact_name": "okx-btc-funding-compact-YYYY-MM-DD"
    },
    {
      "source_workflow_run": "123457",
      "compact_artifact_name": "okx-btc-cash-and-carry-compact-..."
    }
  ]
}
```

Campaigns are limited to 31 items. Each artifact and its parent preparation
artifact are verified independently against the Actions API and the compact
manifest. The local promotion is then atomic: if any later item fails
provenance, checksum, identity, or corpus validation, all fixtures newly staged
by that campaign are removed and `corpus-index.json` is restored.

A workflow code push uses a **pinned, already-present Funding+Cash pair** as a
safe no-op integration self-check. To promote new days, explicitly dispatch a
campaign with its actual preparation run IDs and compact artifact names; a code
push never implicitly selects unpinned market days.

The first real mixed campaign was validated by Actions run
[37435411557](https://github.com/pkking/future-opportunity/actions/runs/37435411557)
and proposed as [PR #3](https://github.com/pkking/future-opportunity/pull/3):
Funding 2026-09-03 and Cash 2026-06-03. Its PR-triggered CI and historical smoke
passed. These dates do **not** count as pinned on `main` until the PR is
reviewed and merged. PR #2 was closed without merge, superseded by the mixed
campaign; do not open a second PR with the same strategy/date facts.

Already-pinned identical items are allowed as no-ops. Input order does not
control corpus order. One effective campaign produces one review branch and one
PR or policy-safe PR handoff, reducing review overhead while preserving
per-market-day evidence.

### Reporting on the entire historical corpus

The Stage-1 statistics report replays **every indexed pinned entry-market
day** through the same Funding Carry and Cash-and-Carry application workflows:

```bash
uv run python scripts/report_historical_corpus_distribution.py
```

Output: `artifacts/historical-smoke/corpus-distribution.json`, also uploaded
by `Historical Backtest Smoke`. This is additional reporting evidence,
**not** a return-based acceptance gate.

The key business distinction is the **pinned-case qualification rate**:
the share of deliberately selected, frozen entry/exit cases that qualify.
It does **not** measure the market-wide arrival frequency of profitable
arbitrage opportunities. Every indexed market day contributes exactly one
frozen case in the current compact corpus.

For each strategy the report includes sample denominator, qualified/rejected
cases, rejection reasons, per-case expected net return distribution, and
realized-return distributions only where execution/return evidence is
assessed. Missing realized returns remain `null`, never zero. Funding Carry
retains separate lower/upper realized-return bounds; it does not invent an
exact funding settlement mark. Cash-and-Carry includes only qualified,
completely assessed closed cases in realized-return percentiles.

P25/P50/P90 use deterministic linear interpolation at sorted index
`(n - 1) * percentile`. These are **per-case horizon returns**, not
annualized or directly comparable between different holding periods. With
zero assessed returns, distributions have zero assessed count and null
statistics. Stage-2 thresholds remain disabled pending sufficient evidence
and a separate human-approved ADR.

### Planning future campaigns from prepared artifacts

For larger batches, use the **read-only** planning workflow:

```text
Actions -> Plan Historical Corpus Campaign

source_run_ids  = 37327493270,37434976457
campaign_prefix = stage1-reviewed-wave
```

The input is an explicit, comma-separated set of **successful** preparation
workflow run IDs (at most 20 runs). The planner checks the exact compact artifact
and parent preparation artifact IDs/digests against the GitHub Actions API,
revalidates compact manifest provenance and canonical checksums, then compares
strategy/date identities against the versioned `corpus-index.json`.

The resulting `historical-campaign-planner-<run-id>` Actions artifact contains:

- `inventory.json`: downloaded artifact identities and provenance inputs;
- `report.json`: excluded pinned days, selected candidate days, **actual pinned
  counts** and **projected counts if all proposals were merged**;
- `waves/*.json`: deterministic candidate campaigns containing no more than
  31 items each, suitable as explicit inputs to `Promote Historical Corpus
  Campaign`.

A planner run **never stages fixtures, creates a branch or PR, changes the
corpus, or activates Stage 2**. Its default push-trigger integration check uses
Funding 2026-09-02 (already pinned) and Funding 2026-09-04 (prepared but not
pinned). Self-check run
[37441177683](https://github.com/pkking/future-opportunity/actions/runs/37441177683)
verified one exclusion, one proposal, and a Funding forecast of 2 pinned to
3 if merged without changing current pinned counts.

The planner compares with `main` and does **not** automatically subtract
unmerged/open PR candidates. Review outstanding campaign PRs (currently
[PR #3](https://github.com/pkking/future-opportunity/pull/3)) before
dispatching a generated wave to avoid duplicate proposals. Actual promotion
revalidates all source identities and fails closed on corpus collisions.

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
