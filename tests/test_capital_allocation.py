from decimal import Decimal

from future_opportunity.domain.capital.model import allocate_isolated_hedge


def test_isolated_allocation_accounts_for_spot_and_futures_margin() -> None:
    allocation = allocate_isolated_hedge(
        capital=Decimal(10_000),
        reserve_ratio=Decimal("0.10"),
        futures_leverage=Decimal(1),
    )

    assert allocation.reserve_amount == Decimal(1_000)
    assert allocation.spot_notional == Decimal(4_500)
    assert allocation.hedge_notional == Decimal(4_500)
    assert allocation.futures_margin == Decimal(4_500)
    assert (
        allocation.reserve_amount
        + allocation.spot_notional
        + allocation.futures_margin
        == allocation.total_capital
    )


def test_isolated_allocation_accounts_for_futures_basis() -> None:
    allocation = allocate_isolated_hedge(
        capital=Decimal(10_000),
        reserve_ratio=Decimal("0.10"),
        futures_leverage=Decimal(1),
        hedge_notional_ratio=Decimal("1.02"),
    )

    assert allocation.spot_notional == Decimal(9_000) / Decimal("2.02")
    assert allocation.hedge_notional == allocation.spot_notional * Decimal("1.02")
    assert (
        allocation.reserve_amount
        + allocation.spot_notional
        + allocation.futures_margin
        == allocation.total_capital
    )
