# ADR-0006: Historical Backtest Dataset Provenance

- Status: Accepted
- Date: 2026-10-05

## Context

The existing strategy E2E suite is deterministic and observable, but its replay
fixtures are synthetic reference scenarios. Historical backtest evidence needs
real market history without making CI depend on live network availability.

A historical dataset is useful only if another agent can prove exactly where it
came from, how derivative quantities were normalized, which assumptions were
applied, and whether the normalized dataset is byte-for-byte reproducible.

## Decision

### Initial source

The initial unified history source is OKX public historical market data:

```text
GET /api/v5/public/market-data-history
```

The official contract supports:

- SPOT, FUTURES, SWAP, OPTION instruments;
- funding-rate archives;
- 400-level order-book archives;
- 5000-level order-book archives where available;
- daily/monthly file catalog results with direct download URLs.

Binance public archives remain a possible secondary source, but are not the
initial unified source because equivalent historical L2 evidence for both spot
and derivatives is not established by the current repository evidence.

### CI boundary

CI MUST NOT fetch historical market data from an exchange.

Historical acceptance tests consume only pinned canonical replay datasets that
are already present in the repository or in a content-addressed artifact whose
checksum is pinned by the repository.

Acquisition is an explicit preparation step outside the gating replay.

### Provenance manifest

Every historical dataset MUST include a manifest containing at least:

```text
dataset schema version
dataset id
venue
source endpoint and query parameters
source module / instrument type
source date aggregation and timezone semantics
source filename
source download URL
declared source size
raw SHA-256
instrument metadata snapshot
normalizer version
normalized SHA-256
canonical sample count / time range
```

### Instrument metadata

Derivative book size is contract count, not base-asset quantity.

For each historical derivative instrument, the manifest MUST pin the metadata
used for normalization:

```text
instId
instFamily
instType
ctVal
ctMult
ctValCcy
settleCcy
listTime
expTime
```

Missing metadata is evidence failure. The importer MUST NOT infer contract value
from symbol naming.

### Timezone semantics

Historical catalog dates follow the source contract:

- order-book modules use UTC dates;
- funding/trade/candle modules use UTC+8 dates where specified by OKX.

The source timezone rule MUST be recorded in the manifest rather than silently
normalized without provenance.

### Raw schema

A raw archive parser may be added only after the raw archive schema has been
verified against an official sample file.

Unknown headers, unsupported schema variants, or missing required fields fail
closed. They must not be interpreted by guessing a third-party format.

### Supplemental evidence

Funding Carry may use official historical mark-price candles as supplemental
market evidence.

Cash-and-Carry may use official public delivery/settlement evidence.

Whether a modeled funding cash flow is sufficient to satisfy a historical
strategy return target is a separate acceptance-semantic decision and is not
decided by this ADR.

### Backtest engine

The repository will reuse the existing canonical market model, StrategyPlan,
paper execution, ReturnAttribution, Risk invariants, and liquidity policy.

A specialized HFT backtesting framework is not introduced at this stage.
External projects such as hftbacktest may inform replay/reconstruction methods,
but their queue/latency engine is not required for the current taker execution
model.

## Consequences

- Historical backtests are reproducible without exchange network access in CI.
- Dataset provenance is independently auditable.
- Quantity normalization cannot silently drift when exchange contract metadata
  changes.
- The canonical replay format remains venue-independent.
- Raw source formats stay confined to acquisition/normalization adapters.
- Missing historical evidence remains explicit instead of being synthesized.


## Verified source-schema evidence

The raw module-4 order-book schema was verified through a non-gating GitHub
Actions probe against the official OKX catalog and CDN.

Evidence:

```text
workflow run: 37218442680
artifact: okx-historical-schema-probe
artifact id: 11309790145
probe date: 2026-10-01 UTC
```

Observed archive contract:

```text
catalog filename: *-L2orderbook-400lv-YYYY-MM-DD.tar.gz
HTTP content-type: application/gzip
archive member: *.data
member encoding: UTF-8 JSON Lines
```

Observed event shape:

```json
{
  "instId": "...",
  "action": "snapshot | update",
  "ts": "...",
  "asks": [["price", "size", "orderCount"]],
  "bids": [["price", "size", "orderCount"]]
}
```

A snapshot replaces the complete replay state. Updates mutate individual price
levels. An update size of zero removes that price level.

For SPOT, size is base-currency quantity. For derivatives, size is contract
count and MUST be normalized through the pinned contract metadata in the
dataset manifest.

Verified probe hashes:

```text
USDC-USDT SPOT:
25c59d54bc4797e6353e01f2fb1e0ec4a63b2e00986761821ce516359c3b6b9a

USDC-USDT-SWAP:
c21b083f6116cb9411d6738d85a2776db2db5fde579d0fd2d8cfbba2b5426835
```


## Verified funding archive evidence

The official module-3 funding archive was verified independently:

```text
workflow run: 37249021018
instrument: BTC-USDT-SWAP
archive: BTC-USDT-SWAP-fundingrates-2026-09.zip
raw SHA-256:
ce5a600e578678a73294a316592afea9cc2a7f0702bf15d56eb0c9ee68fa5a65
```

The archive contains one CSV member with the exact header:

```text
instrument_name,funding_rate,funding_time
```

Funding timestamps are milliseconds and sampled data shows the expected 8-hour
settlement cadence.

The archive does **not** contain mark price. A Funding Carry historical cash-flow
calculation therefore requires a separately pinned mark-price evidence source.
The importer must not infer settlement notional from the funding rate alone.
