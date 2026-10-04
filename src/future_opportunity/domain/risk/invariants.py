from __future__ import annotations

from decimal import Decimal

from future_opportunity.domain.market.liquidity import max_visible_quantity_at_impact
from future_opportunity.domain.market.snapshot import OrderBook
from future_opportunity.domain.position.model import Position
from future_opportunity.domain.risk.model import InvariantResult, InvariantState


def evaluate_delta_neutrality(
    position: Position,
    max_delta_pct: Decimal,
) -> InvariantResult:
    absolute_delta = abs(position.delta_pct)
    state = (
        InvariantState.SATISFIED
        if absolute_delta <= max_delta_pct
        else InvariantState.VIOLATED
    )

    return InvariantResult(
        name="DeltaNeutrality",
        state=state,
        observed={"deltaPct": str(position.delta_pct)},
        limit={"maxDeltaPct": str(max_delta_pct)},
        explanation={"deltaNotional": str(position.delta_notional)},
    )


def evaluate_leg_integrity(
    position: Position,
    expected_instrument_ids: tuple[str, ...],
) -> InvariantResult:
    actual = tuple(leg.instrument_id for leg in position.legs)
    nonzero = all(leg.quantity != 0 for leg in position.legs)
    complete = set(actual) == set(expected_instrument_ids) and nonzero

    return InvariantResult(
        name="LegIntegrity",
        state=(
            InvariantState.SATISFIED
            if complete
            else InvariantState.VIOLATED
        ),
        observed={
            "instrumentIds": list(actual),
            "nonzero": nonzero,
        },
        limit={"expectedInstrumentIds": list(expected_instrument_ids)},
    )


def evaluate_carry_positive(expected_net_return: Decimal) -> InvariantResult:
    return InvariantResult(
        name="CarryPositive",
        state=(
            InvariantState.SATISFIED
            if expected_net_return > 0
            else InvariantState.VIOLATED
        ),
        observed={"expectedNetReturn": str(expected_net_return)},
        limit={"minimum": "0"},
    )


def evaluate_exit_liquidity(
    position: Position,
    books: dict[str, OrderBook],
    max_impact_bps: Decimal,
) -> InvariantResult:
    details: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    sufficient = True

    for leg in position.legs:
        book = books.get(leg.instrument_id)
        if book is None:
            missing.append(leg.instrument_id)
            continue

        exit_side = "sell" if leg.quantity > 0 else "buy"
        required = abs(leg.quantity)
        visible = max_visible_quantity_at_impact(
            book,
            exit_side,
            max_impact_bps,
        )
        if visible < required:
            sufficient = False

        details[leg.instrument_id] = {
            "exitSide": exit_side,
            "requiredQuantity": str(required),
            "visibleQuantity": str(visible),
        }

    if missing:
        return InvariantResult(
            name="ExitLiquidity",
            state=InvariantState.UNASSESSED,
            observed={"legs": details, "missingBooks": missing},
            limit={"maxImpactBps": str(max_impact_bps)},
            explanation={"reason": "missing_order_book_evidence"},
        )

    return InvariantResult(
        name="ExitLiquidity",
        state=(
            InvariantState.SATISFIED
            if sufficient
            else InvariantState.VIOLATED
        ),
        observed={"legs": details},
        limit={"maxImpactBps": str(max_impact_bps)},
    )


def margin_safety_unassessed() -> InvariantResult:
    return InvariantResult(
        name="MarginSafety",
        state=InvariantState.UNASSESSED,
        observed={},
        limit={},
        explanation={
            "reason": "requires_account_and_venue_specific_margin_evidence"
        },
    )


def venue_exposure_unassessed() -> InvariantResult:
    return InvariantResult(
        name="VenueExposure",
        state=InvariantState.UNASSESSED,
        observed={},
        limit={},
        explanation={"reason": "requires_portfolio_level_venue_exposure"},
    )
