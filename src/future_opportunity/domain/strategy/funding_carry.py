from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from future_opportunity.domain.capital.model import allocate_isolated_hedge
from future_opportunity.domain.market.liquidity import BPS, estimate_market_fill
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot


SECONDS_PER_DAY = Decimal(86_400)
DAYS_PER_YEAR = Decimal(365)


@dataclass(frozen=True, slots=True)
class FundingCarryAssumptions:
    horizon_days: int = 30
    reserve_ratio: Decimal = Decimal("0.10")
    futures_leverage: Decimal = Decimal(1)
    spot_taker_fee_bps: Decimal = Decimal(10)
    perpetual_taker_fee_bps: Decimal = Decimal(5)

    def __post_init__(self) -> None:
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        if not Decimal(0) <= self.reserve_ratio < Decimal(1):
            raise ValueError("reserve_ratio must be within [0, 1)")
        if self.futures_leverage <= 0:
            raise ValueError("futures_leverage must be positive")


@dataclass(frozen=True, slots=True)
class FundingCarryEvaluation:
    venue: str
    base: str
    quote: str
    capital: Decimal
    reserve_amount: Decimal
    deployed_notional: Decimal
    futures_margin: Decimal
    expected_funding_rate_per_period: Decimal
    funding_periods_per_day: Decimal
    positive_funding_ratio_7d: Decimal
    funding_volatility_30d: Decimal
    gross_return_horizon: Decimal
    assumed_round_trip_fee_return: Decimal
    estimated_round_trip_slippage_return: Decimal
    expected_net_return_horizon: Decimal
    annualized_equivalent: Decimal
    return_character: str = "variable"



def _rates_within(
    snapshot: FundingCarryMarketSnapshot,
    days: int,
) -> list[Decimal]:
    cutoff = snapshot.observed_at - timedelta(days=days)
    return [
        item.rate
        for item in snapshot.funding_history
        if item.funding_time >= cutoff
    ]


def _mean(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal(0)
    return sum(values, Decimal(0)) / Decimal(len(values))


def _volatility(values: list[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal(0)
    mean = _mean(values)
    variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / Decimal(
        len(values)
    )
    return variance.sqrt()


def _funding_periods_per_day(snapshot: FundingCarryMarketSnapshot) -> Decimal:
    times = sorted(item.funding_time for item in snapshot.funding_history)
    if len(times) < 2:
        return Decimal(3)

    intervals = [
        Decimal(str((right - left).total_seconds()))
        for left, right in zip(times[-22:-1], times[-21:], strict=False)
        if right > left
    ]
    if not intervals:
        return Decimal(3)

    intervals.sort()
    median_seconds = intervals[len(intervals) // 2]
    return SECONDS_PER_DAY / median_seconds


def evaluate_funding_carry(
    snapshot: FundingCarryMarketSnapshot,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
) -> FundingCarryEvaluation:
    rates_1d = _rates_within(snapshot, 1)
    rates_7d = _rates_within(snapshot, 7)
    rates_30d = _rates_within(snapshot, 30)

    expected_rate = (
        Decimal("0.5") * _mean(rates_1d)
        + Decimal("0.3") * _mean(rates_7d)
        + Decimal("0.2") * _mean(rates_30d)
    )
    positive_ratio_7d = (
        Decimal(sum(1 for value in rates_7d if value > 0)) / Decimal(len(rates_7d))
        if rates_7d
        else Decimal(0)
    )

    periods_per_day = _funding_periods_per_day(snapshot)
    periods = Decimal(assumptions.horizon_days) * periods_per_day
    allocation = allocate_isolated_hedge(
        capital,
        assumptions.reserve_ratio,
        assumptions.futures_leverage,
    )
    deployed_notional = allocation.hedged_notional
    notional_to_capital = deployed_notional / capital

    gross_return = expected_rate * periods * notional_to_capital

    one_way_fee_rate = (
        assumptions.spot_taker_fee_bps + assumptions.perpetual_taker_fee_bps
    ) / BPS
    round_trip_fee_return = one_way_fee_rate * Decimal(2) * notional_to_capital

    spot_quantity = deployed_notional / snapshot.spot_book.best_ask
    spot_impact = estimate_market_fill(
        snapshot.spot_book,
        "buy",
        spot_quantity,
    ).impact_bps
    perpetual_impact = estimate_market_fill(
        snapshot.perpetual_book,
        "sell",
        spot_quantity,
    ).impact_bps
    entry_slippage_rate = (spot_impact + perpetual_impact) / BPS
    round_trip_slippage_return = (
        entry_slippage_rate * Decimal(2) * notional_to_capital
    )

    net_return = (
        gross_return
        - round_trip_fee_return
        - round_trip_slippage_return
    )
    annualized = net_return * DAYS_PER_YEAR / Decimal(assumptions.horizon_days)

    return FundingCarryEvaluation(
        venue=snapshot.venue,
        base=snapshot.base,
        quote=snapshot.quote,
        capital=capital,
        reserve_amount=allocation.reserve_amount,
        deployed_notional=deployed_notional,
        futures_margin=allocation.futures_margin,
        expected_funding_rate_per_period=expected_rate,
        funding_periods_per_day=periods_per_day,
        positive_funding_ratio_7d=positive_ratio_7d,
        funding_volatility_30d=_volatility(rates_30d),
        gross_return_horizon=gross_return,
        assumed_round_trip_fee_return=round_trip_fee_return,
        estimated_round_trip_slippage_return=round_trip_slippage_return,
        expected_net_return_horizon=net_return,
        annualized_equivalent=annualized,
    )
