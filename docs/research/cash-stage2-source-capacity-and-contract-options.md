# Cash Stage-2 source-capacity and contract-discovery evidence

Status: evidence complete; acquisition contract policy intentionally undecided.

## Capacity evidence

Canonical source:

- OKX public historical catalog
- module: `4`
- instrument type: `FUTURES`
- instrument family: `BTC-USDT`
- date aggregation: `daily`

Capacity workflow:

- run: `37714282539`
- artifact: `cash-stage2-source-capacity`
- artifact id: `11522419694`
- digest: `sha256:48c202548ebeb98a4531c6a11cdd4ced61305f32754ba689fb45225a6a4a2da1`

Observed interval: 2026-01-01 through 2026-06-26.

Results:

- scanned days: 177
- unique-ready archive days: 177
- missing days: 0
- ambiguous archive days: 0
- query-error days: 0
- current pinned Cash days: 5
- unique-ready unpinned days: 172
- additional days required for ADR-0007 minimum: 25
- source capacity sufficient: yes

The previous Cash bottleneck was therefore not historical archive capacity. It
was caused by watching July-September dates beyond the current publication
frontier and by a discovery implementation that assumed one expiry-future member
per daily chain archive.

## Frozen 25-day pre-registration

The exact selection is versioned in:

`docs/historical-acquisition-plans/cash-stage2-30day-wave-001.json`

Selection depends only on source availability and already-pinned dates. No
economics were inspected before the dates were frozen.

Selected dates:

- 2026-01-04
- 2026-01-11
- 2026-01-18
- 2026-01-25
- 2026-01-31
- 2026-02-07
- 2026-02-14
- 2026-02-21
- 2026-02-28
- 2026-03-07
- 2026-03-14
- 2026-03-21
- 2026-03-28
- 2026-04-03
- 2026-04-10
- 2026-04-17
- 2026-04-24
- 2026-05-01
- 2026-05-08
- 2026-05-15
- 2026-05-22
- 2026-05-28
- 2026-06-09
- 2026-06-16
- 2026-06-23

## Contract discovery

Successful corrected discovery workflow:

- run: `37714773301`
- frozen selection control: `cash-stage2-selection-control`
- 25/25 selected dates completed successfully
- 0 failed discovery jobs

The discovery fix preserves all expiry-future members when a historical chain
archive contains multiple contracts. It does not choose a contract or holding
period.

Contract coverage across the 25 selected days:

| Future ID | Selected dates where present |
|---|---:|
| BTC-USDT-260109 | 1 |
| BTC-USDT-260116 | 2 |
| BTC-USDT-260123 | 2 |
| BTC-USDT-260130 | 4 |
| BTC-USDT-260227 | 8 |
| BTC-USDT-260327 | 12 |
| BTC-USDT-260626 | 25 |

Status distribution:

- `multiple_future_contracts`: 12 dates
- `future_discovered`: 13 dates

The transition occurs after 2026-03-21: 2026-03-28 and all later selected dates
contain only `BTC-USDT-260626` in the chain archive.

The public delivery-history endpoint did not return settlement evidence for
these historical candidate contracts during this probe. This remains
`unassessed`; the archive identity itself is source-verifiable and the
BTCUSDT expiry-futures product specification is backed by the official product
rule already used by the repository.

## Decision boundary

Existing Cash acquisition planning intentionally requires the operator to supply
an explicit `future_id`, `expiry_at`, and `exit_at`; discovery must not silently
choose them.

Two technically valid next policies are now visible:

### A. Fixed June contract

Use `BTC-USDT-260626` for all 25 days, with explicit expiry
`2026-06-26T08:00:00+00:00` and the existing pre-expiry exit convention.

Advantages:

- one acquisition template;
- the contract is present on all 25 frozen dates;
- directly reuses the future already represented in current pinned Cash
  fixtures.

Tradeoff:

- holding horizon varies substantially from January to June, so early cases
  represent much longer capital lock-up than current June cases.

### B. Quarter-aligned contracts

Use `BTC-USDT-260327` for the 12 selected dates from 2026-01-04 through
2026-03-21, and `BTC-USDT-260626` for the 13 selected dates from 2026-03-28
through 2026-06-23.

Advantages:

- keeps each entry in its current quarter;
- produces more comparable time-to-expiry / capital-lock-up semantics;
- still uses only contracts explicitly present in the frozen archive evidence;
- only two explicit acquisition templates are required.

Tradeoff:

- requires two acquisition waves/templates instead of one.

No economics were used to derive either option.
