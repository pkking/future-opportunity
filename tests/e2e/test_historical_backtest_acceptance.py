from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.application.backtest.cash_and_carry import (
    run_cash_and_carry_backtest,
)
from future_opportunity.application.backtest.funding_carry import (
    run_funding_carry_backtest,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.fixture import (
    build_funding_case,
    load_funding_history_fixture,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


CASH_FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "historical"
    / "okx-btc-cash-and-carry-2026-06-v1-target-compact"
)


@pytest.mark.asyncio
async def test_pinned_real_cash_history_replays_offline_without_semantic_drift() -> None:
    case = load_cash_and_carry_close_fixture(CASH_FIXTURE)

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



FUNDING_FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "historical"
    / "okx-btc-usdt-funding-carry-2026-09-01-v1-target-compact"
)


@pytest.mark.asyncio
async def test_pinned_real_funding_history_replays_offline_without_semantic_drift() -> None:
    fixture = load_funding_history_fixture(FUNDING_FIXTURE)
    assert fixture.dataset_id == (
        "okx-btc-usdt-funding-carry-2026-09-01-v1-target-compact"
    )
    assert fixture.alignment.requested_samples == 96
    assert fixture.alignment.emitted_samples == 2

    case = build_funding_case(
        fixture,
        entry_index=0,
        exit_index=1,
    )
    report = await run_funding_carry_backtest(
        (case,),
        capital=Decimal("10000"),
        assumptions=FundingCarryAssumptions(horizon_days=1),
    )

    assert report.sample_count == 1
    assert report.qualified_count == 0
    assert report.qualification_rate == Decimal(0)

    result = report.cases[0]
    assert result.case_id.startswith(
        "okx-btc-usdt-funding-carry-2026-09-01-v1-target-compact:"
    )
    assert result.qualified is False
    assert result.qualification_reasons == (
        "expected_net_return_not_positive",
    )
    assert result.expected_net_return == Decimal(
        "-0.001309413091319054999999999910"
    )
    assert result.realized_return_lower is None
    assert result.realized_return_upper is None
    assert result.evidence_ids[0] == fixture.dataset_id
