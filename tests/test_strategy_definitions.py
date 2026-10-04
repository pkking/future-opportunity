from future_opportunity.domain.opportunity.model import ReturnCharacter
from future_opportunity.domain.strategy.definition import (
    CASH_AND_CARRY,
    FUNDING_CARRY,
    strategy_definition,
)


def test_strategy_definitions_preserve_business_semantics() -> None:
    assert FUNDING_CARRY.return_character is ReturnCharacter.VARIABLE
    assert FUNDING_CARRY.return_sources == ("funding",)

    assert CASH_AND_CARRY.return_character is ReturnCharacter.CONVERGENT
    assert CASH_AND_CARRY.return_sources == ("basis_convergence",)

    assert strategy_definition("funding-carry") is FUNDING_CARRY
