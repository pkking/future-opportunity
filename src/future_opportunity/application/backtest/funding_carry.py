from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.funding_carry import (
    DiscoverFundingCarry,
)
from future_opportunity.application.manage.close_funding_carry import (
    CloseFundingCarry,
)
from future_opportunity.application.simulate.errors import OpportunityNotQualified
from future_opportunity.application.simulate.funding_carry import (
    SimulateFundingCarry,
)
from future_opportunity.backtest.funding_evidence import (
    bound_short_funding_cash_flow,
    sum_funding_cash_flow_bounds,
)
from future_opportunity.backtest.model import (
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
)
from future_opportunity.domain.deployment.model import LiquidityPolicy
from future_opportunity.domain.market.snapshot import FundingCarryMarketSnapshot
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


@dataclass(frozen=True, slots=True)
class HistoricalFundingCarryCase:
    case_id: str
    entry: FundingCarryMarketSnapshot
    exit: FundingCarryMarketSnapshot
    funding: tuple[HistoricalFundingObservation, ...]
    mark_prices: tuple[HistoricalMarkPriceCandle, ...]
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")
        if self.exit.observed_at <= self.entry.observed_at:
            raise ValueError("funding case exit must be after entry")
        if self.entry.perpetual_instrument_id != self.exit.perpetual_instrument_id:
            raise ValueError("funding case perpetual instrument must remain stable")
        if self.entry.spot_instrument_id != self.exit.spot_instrument_id:
            raise ValueError("funding case spot instrument must remain stable")


@dataclass(frozen=True, slots=True)
class FundingCarryBacktestCaseResult:
    case_id: str
    entry_at: str
    exit_at: str
    qualified: bool
    qualification_reasons: tuple[str, ...]
    expected_net_return: Decimal
    assessed_ex_funding_pnl: Decimal | None
    funding_cash_flow_lower: Decimal | None
    funding_cash_flow_upper: Decimal | None
    realized_return_lower: Decimal | None
    realized_return_upper: Decimal | None
    funding_event_count: int
    funding_interval_evidence_complete: bool
    initial_delta_pct: Decimal | None
    deployment_policy: str | None
    partial_deployment: bool | None
    risk_states: tuple[tuple[str, str], ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FundingCarryBacktestReport:
    strategy: str
    sample_count: int
    qualified_count: int
    qualification_rate: Decimal
    interval_evidence_complete_count: int
    mean_realized_return_lower: Decimal | None
    mean_realized_return_upper: Decimal | None
    median_realized_return_lower: Decimal | None
    minimum_realized_return_lower: Decimal | None
    maximum_realized_return_upper: Decimal | None
    cases: tuple[FundingCarryBacktestCaseResult, ...]


@dataclass(slots=True)
class _HistoricalFundingMarketData:
    case: HistoricalFundingCarryCase
    at_exit: bool = False

    async def snapshot(
        self,
        base: str,
        quote: str = "USDT",
    ) -> FundingCarryMarketSnapshot:
        selected = self.case.exit if self.at_exit else self.case.entry
        if base != selected.base or quote != selected.quote:
            raise ValueError("historical funding case pair mismatch")
        return selected


async def run_funding_carry_backtest(
    cases: tuple[HistoricalFundingCarryCase, ...],
    *,
    capital: Decimal,
    assumptions: FundingCarryAssumptions,
    liquidity_policy: LiquidityPolicy = LiquidityPolicy.STRICT,
    max_impact_bps: Decimal = Decimal(10),
) -> FundingCarryBacktestReport:
    if not cases:
        raise ValueError("historical backtest requires at least one case")
    if capital <= 0:
        raise ValueError("capital must be positive")

    results: list[FundingCarryBacktestCaseResult] = []
    lower_returns: list[Decimal] = []
    upper_returns: list[Decimal] = []

    for case in cases:
        market = _HistoricalFundingMarketData(case)
        opportunities = MemoryOpportunityRepository()
        simulations = MemorySimulationRepository()
        discovery = DiscoverFundingCarry(market, opportunities)

        try:
            simulated = await SimulateFundingCarry(
                discovery,
                simulations,
            ).execute(
                base=case.entry.base,
                capital=capital,
                assumptions=assumptions,
                liquidity_policy=liquidity_policy,
                max_impact_bps=max_impact_bps,
            )
        except OpportunityNotQualified:
            discovered = await discovery.execute(
                case.entry.base,
                capital,
                assumptions,
                liquidity_policy=liquidity_policy,
                max_impact_bps=max_impact_bps,
            )
            expected = discovered.evaluation.expected_net_return_horizon
            results.append(
                FundingCarryBacktestCaseResult(
                    case_id=case.case_id,
                    entry_at=case.entry.observed_at.isoformat(),
                    exit_at=case.exit.observed_at.isoformat(),
                    qualified=False,
                    qualification_reasons=discovered.qualification.reasons,
                    expected_net_return=expected,
                    assessed_ex_funding_pnl=None,
                    funding_cash_flow_lower=None,
                    funding_cash_flow_upper=None,
                    realized_return_lower=None,
                    realized_return_upper=None,
                    funding_event_count=0,
                    funding_interval_evidence_complete=False,
                    initial_delta_pct=None,
                    deployment_policy=discovered.deployment.policy.value,
                    partial_deployment=discovered.deployment.partial_deployment,
                    risk_states=(),
                    evidence_ids=case.evidence_ids,
                )
            )
            continue

        expected = simulated.plan.expected_economics
        if expected is None:
            raise RuntimeError("historical simulation has no expected economics")

        perp_leg = next(
            leg
            for leg in simulated.execution.position.legs
            if leg.instrument_id == case.entry.perpetual_instrument_id
        )
        base_quantity = abs(perp_leg.quantity)

        candle_by_minute = {
            item.started_at: item
            for item in case.mark_prices
        }
        relevant_funding = tuple(
            item
            for item in case.funding
            if case.entry.observed_at < item.funding_time <= case.exit.observed_at
        )
        bounds = []
        missing_mark = False
        for observation in relevant_funding:
            candle = candle_by_minute.get(
                observation.funding_time.replace(second=0, microsecond=0)
            )
            if candle is None:
                missing_mark = True
                continue
            bounds.append(
                bound_short_funding_cash_flow(
                    observation,
                    candle,
                    base_quantity=base_quantity,
                )
            )

        market.at_exit = True
        closed = await CloseFundingCarry(
            market,
            simulations,
        ).execute(simulated.execution.position.id)
        assessed_ex_funding = closed.current_return.net_pnl

        interval_complete = (
            not missing_mark
            and len(bounds) == len(relevant_funding)
            and bool(relevant_funding)
        )
        funding_lower: Decimal | None = None
        funding_upper: Decimal | None = None
        realized_lower: Decimal | None = None
        realized_upper: Decimal | None = None
        if interval_complete:
            funding_lower, funding_upper = sum_funding_cash_flow_bounds(
                tuple(bounds)
            )
            realized_lower = (assessed_ex_funding + funding_lower) / capital
            realized_upper = (assessed_ex_funding + funding_upper) / capital
            lower_returns.append(realized_lower)
            upper_returns.append(realized_upper)

        deployment = simulated.plan.deployment
        results.append(
            FundingCarryBacktestCaseResult(
                case_id=case.case_id,
                entry_at=case.entry.observed_at.isoformat(),
                exit_at=case.exit.observed_at.isoformat(),
                qualified=True,
                qualification_reasons=(),
                expected_net_return=expected.expected_net_return,
                assessed_ex_funding_pnl=assessed_ex_funding,
                funding_cash_flow_lower=funding_lower,
                funding_cash_flow_upper=funding_upper,
                realized_return_lower=realized_lower,
                realized_return_upper=realized_upper,
                funding_event_count=len(relevant_funding),
                funding_interval_evidence_complete=interval_complete,
                initial_delta_pct=abs(
                    simulated.execution.position.delta_pct
                ),
                deployment_policy=(
                    deployment.policy.value if deployment is not None else None
                ),
                partial_deployment=(
                    deployment.partial_deployment
                    if deployment is not None
                    else None
                ),
                risk_states=tuple(
                    sorted(
                        (invariant.name, invariant.state.value)
                        for invariant in simulated.risk.invariants
                    )
                ),
                evidence_ids=case.evidence_ids,
            )
        )

    qualified_count = sum(1 for item in results if item.qualified)
    complete_count = sum(
        1
        for item in results
        if item.funding_interval_evidence_complete
    )
    return FundingCarryBacktestReport(
        strategy="funding-carry",
        sample_count=len(results),
        qualified_count=qualified_count,
        qualification_rate=Decimal(qualified_count) / Decimal(len(results)),
        interval_evidence_complete_count=complete_count,
        mean_realized_return_lower=(
            sum(lower_returns, Decimal(0)) / Decimal(len(lower_returns))
            if lower_returns
            else None
        ),
        mean_realized_return_upper=(
            sum(upper_returns, Decimal(0)) / Decimal(len(upper_returns))
            if upper_returns
            else None
        ),
        median_realized_return_lower=(
            median(lower_returns) if lower_returns else None
        ),
        minimum_realized_return_lower=(
            min(lower_returns) if lower_returns else None
        ),
        maximum_realized_return_upper=(
            max(upper_returns) if upper_returns else None
        ),
        cases=tuple(results),
    )
