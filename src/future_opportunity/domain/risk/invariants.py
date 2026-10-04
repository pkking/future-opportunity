from __future__ import annotations

from decimal import Decimal

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
