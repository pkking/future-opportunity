from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.application.backtest.cash_and_carry import (
    run_cash_and_carry_backtest,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)


FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "historical"
    / "okx-btc-cash-and-carry-2026-06-v1-target-compact"
)


@pytest.mark.asyncio
async def test_pinned_real_cash_history_replays_offline_without_semantic_drift() -> None:
    case = load_cash_and_carry_close_fixture(FIXTURE)

    report = await run_cash_and_carry_backtest(
        (case,),
        capital=Decimal("10000"),
        assumptions=CashAndCarryAssumptions(),
    )

    assert report.sample_count == 1
    assert report.qualified_count == 0
    assert report.qualification_rate == Decimal(0)

    result = report.cases[0]
    assert result.case_id == (
        "okx-btc-usdt-cash-and-carry-2026-06-v1-target-compact"
    )
    assert result.close_mode == "pre-expiry"
    assert result.qualified is False
    assert result.qualification_reasons == (
        "expected_net_return_not_positive",
    )
    assert result.expected_net_return == Decimal(
        "-0.0007469851510475881110930647630"
    )
    assert result.realized_net_return is None
    assert result.initial_delta_pct is None
    assert "future-metadata:official-product-spec" in result.evidence_ids
