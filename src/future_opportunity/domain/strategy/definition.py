from __future__ import annotations

from dataclasses import dataclass

from future_opportunity.domain.market.model import InstrumentType
from future_opportunity.domain.opportunity.model import ReturnCharacter


@dataclass(frozen=True, slots=True)
class StrategyLegDefinition:
    instrument_type: InstrumentType
    side: str


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    name: str
    version: str
    description: str
    return_character: ReturnCharacter
    legs: tuple[StrategyLegDefinition, ...]
    return_sources: tuple[str, ...]
    invariants: tuple[str, ...]


COMMON_INVARIANTS = (
    "DeltaNeutrality",
    "MarginSafety",
    "CarryPositive",
    "ExitLiquidity",
    "LegIntegrity",
    "VenueExposure",
)


FUNDING_CARRY = StrategyDefinition(
    name="funding-carry",
    version="1.0.0",
    description=(
        "Long spot and short perpetual to capture positive funding "
        "while neutralizing directional exposure."
    ),
    return_character=ReturnCharacter.VARIABLE,
    legs=(
        StrategyLegDefinition(InstrumentType.SPOT, "buy"),
        StrategyLegDefinition(InstrumentType.PERPETUAL, "sell"),
    ),
    return_sources=("funding",),
    invariants=COMMON_INVARIANTS,
)


CASH_AND_CARRY = StrategyDefinition(
    name="cash-and-carry",
    version="1.0.0",
    description=(
        "Long spot and short a dated future trading above spot, "
        "capturing basis convergence toward expiry."
    ),
    return_character=ReturnCharacter.CONVERGENT,
    legs=(
        StrategyLegDefinition(InstrumentType.SPOT, "buy"),
        StrategyLegDefinition(InstrumentType.FUTURE, "sell"),
    ),
    return_sources=("basis_convergence",),
    invariants=COMMON_INVARIANTS,
)


STRATEGIES = {
    FUNDING_CARRY.name: FUNDING_CARRY,
    CASH_AND_CARRY.name: CASH_AND_CARRY,
}


def strategy_definition(name: str) -> StrategyDefinition:
    try:
        return STRATEGIES[name]
    except KeyError as error:
        raise ValueError(f"unsupported strategy: {name}") from error
