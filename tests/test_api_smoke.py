from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

import future_opportunity.api as api_module
from future_opportunity.api import app
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)


def test_web_workbench_and_strategy_catalog_are_served() -> None:
    with TestClient(app) as client:
        index = client.get("/")
        strategies = client.get("/v1/strategies")

    assert index.status_code == 200
    assert "future-opportunity" in index.text
    assert "Discover Opportunities" in index.text

    assert strategies.status_code == 200
    names = [item["name"] for item in strategies.json()["results"]]
    assert names == ["funding-carry", "cash-and-carry"]


def test_v0_openapi_exposes_management_and_history_without_live_orders() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    paths = set(schema["paths"])
    required = {
        "/v1/strategies",
        "/v1/history",
        "/v1/positions",
        "/v1/positions/{position_id}",
        "/v1/positions/{position_id}/refresh",
        "/v1/positions/{position_id}/close",
        "/v1/opportunities/{opportunity_id}",
        "/v1/opportunities/{opportunity_id}/observations",
        "/v1/opportunities/{venue}/{strategy}/{base}",
        "/v1/simulations/{venue}/{strategy}/{base}",
    }
    assert required <= paths
    assert not any(
        token in path.lower()
        for path in paths
        for token in ("/orders", "/live-order", "/trade")
    )


class ThinFundingApiMarket:
    async def snapshot(
        self,
        base: str,
        quote: str = "USDT",
    ) -> FundingCarryMarketSnapshot:
        now = datetime.now(UTC)
        spot = OrderBook(
            bids=(OrderBookLevel(price=Decimal("99.9"), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            observed_at=now,
        )
        perpetual = OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal("100.1"), quantity=Decimal(10)),),
            observed_at=now,
        )
        return FundingCarryMarketSnapshot(
            venue="fixture",
            base=base,
            quote=quote,
            spot_instrument_id="fixture:spot",
            perpetual_instrument_id="fixture:perp",
            spot_book=spot,
            perpetual_book=perpetual,
            mark_price=Decimal("100.05"),
            last_funding_rate=Decimal("0.001"),
            next_funding_time=now + timedelta(hours=8),
            funding_history=tuple(
                FundingObservation(
                    rate=Decimal("0.001"),
                    funding_time=now - timedelta(hours=8 * index),
                )
                for index in range(90)
            ),
            observed_at=now,
        )


def test_api_requires_explicit_partial_policy_for_oversized_capital(
    monkeypatch,
) -> None:
    market = ThinFundingApiMarket()
    monkeypatch.setattr(
        api_module,
        "_funding_market_data_or_400",
        lambda venue: market,
    )

    common = (
        "?capital=10000&spot_fee_bps=0&derivative_fee_bps=0"
        "&max_impact_bps=10"
    )

    with TestClient(app) as client:
        discovered = client.get(
            "/v1/opportunities/binance/funding-carry/BTC" + common
        )
        strict = client.post(
            "/v1/simulations/binance/funding-carry/BTC" + common
        )
        partial = client.post(
            "/v1/simulations/binance/funding-carry/BTC"
            + common
            + "&liquidity_policy=partial"
        )

    assert discovered.status_code == 200
    result = discovered.json()["results"][0]
    assert result["qualification"]["qualified"] is False
    assert (
        "requested_notional_exceeds_liquidity_limit"
        in result["qualification"]["reasons"]
    )
    assert result["deployment"]["policy"] == "strict"
    assert Decimal(result["deployment"]["capacity_spot_notional"]) == Decimal(1_000)

    assert strict.status_code == 409
    assert "requested_notional_exceeds_liquidity_limit" in strict.json()["detail"]

    assert partial.status_code == 200
    deployment = partial.json()["deployment"]
    assert deployment["policy"] == "partial"
    assert deployment["partial_deployment"] is True
    assert Decimal(deployment["requested_spot_notional"]) == Decimal(4_500)
    assert Decimal(deployment["actual_spot_notional"]) == Decimal(1_000)
    assert Decimal(deployment["unused_capital"]) == Decimal(7_000)
