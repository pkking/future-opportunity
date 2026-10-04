from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot


BPS = Decimal(10_000)
FUNDING_PERIODS_PER_DAY = Decimal(3)
DAYS_PER_YEAR = Decimal(365)


@dataclass(frozen=True, slots=True)
class FundingCarryAssumptions:
    horizon_days: int = 30
    deploy_ratio: Decimal = Decimal("0.90")
    spot_taker_fee_bps: Decimal = Decimal(10)
    perpetual_taker_fee_bps: Decimal = Decimal(5)

    def __post_init__(self) -> None:
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        if not Decimal(0) < self.deploy_ratio <= Decimal(1):
            raise ValueError("deploy_ratio must be within (0, 1]")


@dataclass(frozen=True, slots=True)
class FundingCarryEvaluation:
    venue: str
    base: str
    quote: str
    capital: Decimal
    deployed_notional: Decimal
    expected_funding_rate_per_period: Decimal
    positive_funding_ratio_7d: Decimal
    funding_volatility_30d: Decimal
    gross_return_horizon: Decimal
    assumed_round_trip_fee_return: Decimal
    expected_net_return_horizon: Decimal
    annualized_equivalent: Decimal
    return_character: str = "variable"


def _rates(snapshot: FundingCarryMarketSnapshot, count: int) -> list[Decimal]:
    values = [item.rate for item in snapshot.funding_history]
    return values[-count:] if len(values) > count else values


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


def evaluate_funding_carry(
    snapshot: FundingCarryMarketSnapshot,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
) -> FundingCarryEvaluation:
    if capital <= 0:
        raise ValueError("capital must be positive")

    rates_1d = _rates(snapshot, 3)
    rates_7d = _rates(snapshot, 21)
    rates_30d = _rates(snapshot, 90)

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

    periods = Decimal(assumptions.horizon_days) * FUNDING_PERIODS_PER_DAY
    gross_return = expected_rate * periods

    one_way_fee = (
        assumptions.spot_taker_fee_bps + assumptions.perpetual_taker_fee_bps
    ) / BPS
    round_trip_fee = one_way_fee * Decimal(2)
    net_return = gross_return - round_trip_fee

    annualized = net_return * DAYS_PER_YEAR / Decimal(assumptions.horizon_days)

    return FundingCarryEvaluation(
        venue=snapshot.venue,
        base=snapshot.base,
        quote=snapshot.quote,
        capital=capital,
        deployed_notional=capital * assumptions.deploy_ratio,
        expected_funding_rate_per_period=expected_rate,
        positive_funding_ratio_7d=positive_ratio_7d,
        funding_volatility_30d=_volatility(rates_30d),
        gross_return_horizon=gross_return,
        assumed_round_trip_fee_return=round_trip_fee,
        expected_net_return_horizon=net_return,
        annualized_equivalent=annualized,
    )
