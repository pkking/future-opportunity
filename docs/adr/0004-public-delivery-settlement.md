# ADR-0004: Public Delivery Settlement as Execution Evidence

- Status: Accepted
- Date: 2026-10-04

## Context

Cash-and-Carry has a convergent return horizon at dated-future expiry.

Before this decision, paper close required both the spot and dated future to have live order books. That works for an early close but fails for the strategy's natural lifecycle: OKX removes a delivered futures instrument from live trading, while its public delivery history exposes the final delivery price.

Representing delivery as an ordinary market fill would be inaccurate:

- there is no live order book fill at delivery,
- delivery has no market slippage,
- settlement/delivery fees are distinct execution costs,
- after the future delivers, the spot leg remains directionally exposed until it is sold.

## Decision

V0 models public futures delivery as immutable execution evidence:

```text
FillSource.SETTLEMENT
```

For an OKX Cash-and-Carry position:

### Before expiry

```text
SELL spot through current order book
BUY  future through current order book
```

Both close legs are simulated market fills.

### After expiry

```text
Future leg:
  close price = public OKX delivery price
  source      = SETTLEMENT
  slippage    = 0
  fee         = frozen derivative exit/settlement fee assumption

Spot leg:
  SELL through the current real order book
  source      = SIMULATED
```

The return attribution is decomposed as:

```text
basis_convergence
  = quantity * (future_entry_reference - spot_entry_reference)

residual_directional_pnl
  = quantity * (spot_close_reference - delivery_price)
```

The second term makes the exposure after delivery explicit. It must not be reported as arbitrage basis return.

## Evidence source

OKX exposes public delivery/exercise history for dated futures, including instrument ID, delivery price, and delivery timestamp.

The adapter normalizes this venue response into the domain-level `DeliverySettlement` evidence object.

## Consequences

- Cash-and-Carry can complete its natural expiry lifecycle without a live future order book.
- Settlement evidence is auditable alongside normal paper fills.
- Post-delivery spot exposure is visible as residual directional PnL.
- Database fill-source constraints include `settlement`.
- If public delivery evidence is unavailable, V0 refuses to invent a settlement price.
- Any authenticated account-specific settlement cash-flow model remains future work.
