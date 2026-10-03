from decimal import Decimal

from future_opportunity.domain.returns.model import ReturnAttribution


def test_net_pnl_is_attributable() -> None:
    attribution = ReturnAttribution(
        funding=Decimal("100"),
        basis_convergence=Decimal("20"),
        trading_fees=Decimal("10"),
        slippage=Decimal("5"),
        rebalancing_cost=Decimal("2"),
        residual_directional_pnl=Decimal("-3"),
    )

    assert attribution.net_pnl == Decimal("100")
