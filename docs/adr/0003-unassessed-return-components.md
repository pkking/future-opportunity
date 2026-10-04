# ADR-0003: Explicit Unassessed Return Components

- Status: Accepted
- Date: 2026-10-04

## Context

The V0 design requires explainable return attribution.

For some paper-managed positions, public market data can support only part of the current return calculation. In particular, a Funding Carry position may be mark-to-market against current spot/perpetual books while the exact accrued funding cash flow is not provable from the current public snapshot alone.

Treating an unknown component as zero would understate or overstate return while falsely presenting the result as complete.

## Decision

`ReturnAttribution` carries an explicit `unassessed_components` collection.

```text
net_pnl = sum(assessed components only)
complete = unassessed_components is empty
```

An unassessed component means required evidence is not available. It is not equivalent to zero.

Examples:

```text
Funding Carry current valuation:
  basis_convergence / market PnL  assessed
  entry / exit execution costs    assessed
  accrued funding                 UNASSESSED unless settlement evidence exists
```

```text
Cash-and-Carry mark-to-market:
  basis convergence               assessed
  execution costs                 assessed
```

## Consequences

- History/API/UI must expose whether return evidence is complete.
- Consumers must not call an incomplete current return "realized return".
- Future paper funding-settlement evidence can remove `funding` from the unassessed set.
- Future authenticated venue/account adapters can use actual settlement ledger evidence.
- Persistence must store unassessed return components.
