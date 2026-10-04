from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable

import pytest

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import DiscoverCashAndCarry
from future_opportunity.application.discover.funding_carry import DiscoverFundingCarry
from future_opportunity.application.manage.close_cash_and_carry import CloseCashAndCarry
from future_opportunity.application.manage.close_funding_carry import CloseFundingCarry
from future_opportunity.application.simulate.cash_and_carry import SimulateCashAndCarry
from future_opportunity.application.simulate.funding_carry import SimulateFundingCarry
from future_opportunity.domain.execution.model import FillSource
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    DeliverySettlement,
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.position.model import PositionState
from future_opportunity.domain.strategy.cash_and_carry import CashAndCarryAssumptions
from future_opportunity.domain.strategy.funding_carry import FundingCarryAssumptions


ROOT = Path(__file__).parent
TARGETS_PATH = ROOT / "strategy-targets.json"
FIXTURES_PATH = ROOT / "fixtures" / "reference-scenarios.json"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


TARGETS = _load_json(TARGETS_PATH)["scenarios"]
FIXTURES_DOCUMENT = _load_json(FIXTURES_PATH)
FIXTURES = {
    key: value
    for key, value in FIXTURES_DOCUMENT.items()
    if key not in {"schema_version", "fixture_id"}
}
FIXTURE_HASH = hashlib.sha256(FIXTURES_PATH.read_bytes()).hexdigest()


def _book(values: dict[str, str], observed_at: datetime) -> OrderBook:
    return OrderBook(
        bids=(
            OrderBookLevel(
                price=Decimal(values["bid"]),
                quantity=Decimal(values["quantity"]),
            ),
        ),
        asks=(
            OrderBookLevel(
                price=Decimal(values["ask"]),
                quantity=Decimal(values["quantity"]),
            ),
        ),
        observed_at=observed_at,
    )


def _risk_states(report: object) -> dict[str, str]:
    return {
        invariant.name: invariant.state.value
        for invariant in report.invariants
    }


def _target_risk_states(target: dict[str, object]) -> dict[str, str]:
    raw = target["required_risk_states"]
    assert isinstance(raw, dict)
    return {str(key): str(value) for key, value in raw.items()}


class FundingReplay:
    def __init__(self, fixture: dict[str, object]) -> None:
        self.fixture = fixture

    async def snapshot(
        self,
        base: str,
        quote: str = "USDT",
    ) -> FundingCarryMarketSnapshot:
        observed_at = datetime.fromisoformat(str(self.fixture["observed_at"]))
        rate = Decimal(str(self.fixture["funding_rate"]))
        interval = int(self.fixture["funding_interval_hours"])
        points = int(self.fixture["funding_history_points"])
        spot = self.fixture["spot"]
        perpetual = self.fixture["perpetual"]
        assert isinstance(spot, dict)
        assert isinstance(perpetual, dict)

        return FundingCarryMarketSnapshot(
            venue="fixture",
            base=base,
            quote=quote,
            spot_instrument_id="fixture:BTC-USDT:spot",
            perpetual_instrument_id="fixture:BTC-USDT:perpetual",
            spot_book=_book(spot, observed_at),
            perpetual_book=_book(perpetual, observed_at),
            mark_price=(
                Decimal(str(perpetual["bid"]))
                + Decimal(str(perpetual["ask"]))
            )
            / Decimal(2),
            last_funding_rate=rate,
            next_funding_time=observed_at + timedelta(hours=interval),
            funding_history=tuple(
                FundingObservation(
                    rate=rate,
                    funding_time=observed_at - timedelta(hours=interval * index),
                )
                for index in range(points)
            ),
            observed_at=observed_at,
        )


class CashDeliveryReplay:
    def __init__(self, fixture: dict[str, object]) -> None:
        self.fixture = fixture
        self.delivered = False

    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        if self.delivered:
            return ()

        observed_at = datetime.fromisoformat(str(self.fixture["observed_at"]))
        delivery_at = datetime.fromisoformat(str(self.fixture["delivery_at"]))
        spot = self.fixture["spot_entry"]
        future = self.fixture["future_entry"]
        assert isinstance(spot, dict)
        assert isinstance(future, dict)

        return (
            CashAndCarryMarketSnapshot(
                venue="fixture",
                base=base,
                quote=quote,
                spot_instrument_id="fixture:BTC-USDT:spot",
                future_instrument_id="fixture:BTC-USDT-FUTURE:future",
                spot_book=_book(spot, observed_at),
                future_book=_book(future, observed_at),
                expiry=delivery_at,
                observed_at=observed_at,
            ),
        )

    async def spot_book(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[str, OrderBook]:
        del base, quote
        close = self.fixture["spot_close"]
        assert isinstance(close, dict)
        observed_at = datetime.fromisoformat(str(self.fixture["delivery_at"]))
        return "fixture:BTC-USDT:spot", _book(close, observed_at)

    async def delivery_settlement(
        self,
        future_instrument_id: str,
        base: str,
        quote: str = "USDT",
    ) -> DeliverySettlement | None:
        del base, quote
        return DeliverySettlement(
            venue="fixture",
            future_instrument_id=future_instrument_id,
            settlement_price=Decimal(str(self.fixture["delivery_price"])),
            settled_at=datetime.fromisoformat(str(self.fixture["delivery_at"])),
        )


@pytest.mark.asyncio
async def test_funding_carry_reference_target(
    evidence_recorder: Callable[[dict[str, object]], None],
) -> None:
    scenario_id = "funding-carry-reference-v1"
    target = TARGETS[scenario_id]
    fixture = FIXTURES[scenario_id]
    assert isinstance(target, dict)
    assert isinstance(fixture, dict)

    capital = Decimal(str(target["capital"]))
    market = FundingReplay(fixture)
    simulations = MemorySimulationRepository()
    simulated = await SimulateFundingCarry(
        DiscoverFundingCarry(market, MemoryOpportunityRepository()),
        simulations,
    ).execute(
        base=str(fixture["base"]),
        capital=capital,
        assumptions=FundingCarryAssumptions(),
    )
    closed = await CloseFundingCarry(market, simulations).execute(
        simulated.execution.position.id
    )

    expected = simulated.plan.expected_economics
    assert expected is not None
    actual_risk = _risk_states(simulated.risk)
    target_risk = _target_risk_states(target)
    expected_return = expected.expected_net_return
    delta_pct = abs(simulated.execution.position.delta_pct)

    passed = (
        simulated.discovered.qualification.qualified
        and expected_return >= Decimal(str(target["min_expected_net_return"]))
        and delta_pct <= Decimal(str(target["max_abs_delta_pct"]))
        and all(actual_risk.get(name) == state for name, state in target_risk.items())
        and closed.position.state is PositionState.CLOSED
        and closed.current_return.complete is bool(target["close_return_complete"])
        and list(closed.current_return.unassessed_components)
        == list(target["required_unassessed_return_components"])
    )

    evidence_recorder(
        {
            "scenario_id": scenario_id,
            "strategy": simulated.plan.strategy.name,
            "strategy_version": simulated.plan.strategy.version,
            "fixture_id": FIXTURES_DOCUMENT["fixture_id"],
            "fixture_sha256": FIXTURE_HASH,
            "target": target,
            "actual": {
                "expected_net_return": str(expected_return),
                "annualized_equivalent": str(expected.annualized_equivalent),
                "initial_delta_pct": str(delta_pct),
                "current_assessed_net_pnl": str(closed.current_return.net_pnl),
            },
            "qualified": simulated.discovered.qualification.qualified,
            "position_state": closed.position.state.value,
            "risk_invariants": actual_risk,
            "return_complete": closed.current_return.complete,
            "unassessed_components": list(
                closed.current_return.unassessed_components
            ),
            "passed": passed,
        }
    )

    assert passed


@pytest.mark.asyncio
async def test_cash_and_carry_delivery_reference_target(
    evidence_recorder: Callable[[dict[str, object]], None],
) -> None:
    scenario_id = "cash-and-carry-delivery-reference-v1"
    target = TARGETS[scenario_id]
    fixture = FIXTURES[scenario_id]
    assert isinstance(target, dict)
    assert isinstance(fixture, dict)

    capital = Decimal(str(target["capital"]))
    market = CashDeliveryReplay(fixture)
    simulations = MemorySimulationRepository()
    simulated = await SimulateCashAndCarry(
        DiscoverCashAndCarry(market, MemoryOpportunityRepository()),
        simulations,
    ).execute(
        base=str(fixture["base"]),
        future_instrument_id="fixture:BTC-USDT-FUTURE:future",
        capital=capital,
        assumptions=CashAndCarryAssumptions(),
    )

    initial_delta = abs(simulated.execution.position.delta_pct)
    initial_risk = _risk_states(simulated.risk)
    market.delivered = True
    closed = await CloseCashAndCarry(market, simulations).execute(
        simulated.execution.position.id
    )
    realized_return = closed.current_return.net_pnl / capital
    close_sources = sorted(
        fill.source.value
        for execution in closed.management_executions
        for fill in execution.fills
    )
    target_sources = sorted(str(item) for item in target["required_close_fill_sources"])
    target_risk = _target_risk_states(target)

    passed = (
        simulated.discovered.qualification.qualified
        and realized_return >= Decimal(str(target["min_realized_net_return"]))
        and initial_delta <= Decimal(str(target["max_abs_delta_pct"]))
        and all(initial_risk.get(name) == state for name, state in target_risk.items())
        and closed.position.state is PositionState.CLOSED
        and closed.current_return.complete is bool(target["close_return_complete"])
        and close_sources == target_sources
        and FillSource.SETTLEMENT.value in close_sources
    )

    evidence_recorder(
        {
            "scenario_id": scenario_id,
            "strategy": simulated.plan.strategy.name,
            "strategy_version": simulated.plan.strategy.version,
            "fixture_id": FIXTURES_DOCUMENT["fixture_id"],
            "fixture_sha256": FIXTURE_HASH,
            "target": target,
            "actual": {
                "realized_net_return": str(realized_return),
                "realized_net_pnl": str(closed.current_return.net_pnl),
                "basis_convergence": str(
                    closed.current_return.basis_convergence
                ),
                "residual_directional_pnl": str(
                    closed.current_return.residual_directional_pnl
                ),
                "initial_delta_pct": str(initial_delta),
                "close_fill_sources": close_sources,
            },
            "qualified": simulated.discovered.qualification.qualified,
            "position_state": closed.position.state.value,
            "risk_invariants": initial_risk,
            "return_complete": closed.current_return.complete,
            "unassessed_components": list(
                closed.current_return.unassessed_components
            ),
            "passed": passed,
        }
    )

    assert passed
