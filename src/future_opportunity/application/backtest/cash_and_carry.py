from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
    MemorySimulationRepository,
)
from future_opportunity.application.discover.cash_and_carry import (
    DiscoverCashAndCarry,
)
from future_opportunity.application.manage.close_cash_and_carry import (
    CloseCashAndCarry,
)
from future_opportunity.application.simulate.cash_and_carry import (
    SimulateCashAndCarry,
)
from future_opportunity.application.simulate.errors import OpportunityNotQualified
from future_opportunity.domain.deployment.model import LiquidityPolicy
from future_opportunity.domain.market.snapshot import (
    CashAndCarryMarketSnapshot,
    DeliverySettlement,
    OrderBook,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)


@dataclass(frozen=True, slots=True)
class HistoricalCashAndCarryCase:
    case_id: str
    entry: CashAndCarryMarketSnapshot
    settlement: DeliverySettlement
    spot_close_instrument_id: str
    spot_close_book: OrderBook
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")
        if self.settlement.future_instrument_id != self.entry.future_instrument_id:
            raise ValueError("settlement instrument must match entry future")
        if self.spot_close_instrument_id != self.entry.spot_instrument_id:
            raise ValueError("spot close instrument must match entry spot")
        if self.settlement.settled_at < self.entry.observed_at:
            raise ValueError("settlement must not precede entry")
        if self.spot_close_book.observed_at < self.settlement.settled_at:
            raise ValueError("spot close book must not precede delivery settlement")


@dataclass(frozen=True, slots=True)
class CashAndCarryBacktestCaseResult:
    case_id: str
    observed_at: str
    expiry: str
    qualified: bool
    qualification_reasons: tuple[str, ...]
    expected_net_return: Decimal
    realized_net_return: Decimal | None
    initial_delta_pct: Decimal | None
    return_complete: bool | None
    basis_convergence: Decimal | None
    residual_directional_pnl: Decimal | None
    deployment_policy: str | None
    partial_deployment: bool | None
    risk_states: tuple[tuple[str, str], ...]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CashAndCarryBacktestReport:
    strategy: str
    sample_count: int
    qualified_count: int
    qualification_rate: Decimal
    closed_count: int
    complete_return_count: int
    mean_realized_net_return: Decimal | None
    median_realized_net_return: Decimal | None
    minimum_realized_net_return: Decimal | None
    maximum_realized_net_return: Decimal | None
    cases: tuple[CashAndCarryBacktestCaseResult, ...]


@dataclass(slots=True)
class _HistoricalCaseMarketData:
    case: HistoricalCashAndCarryCase
    delivered: bool = False

    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        if base != self.case.entry.base or quote != self.case.entry.quote:
            return ()
        return () if self.delivered else (self.case.entry,)

    async def spot_book(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[str, OrderBook]:
        if base != self.case.entry.base or quote != self.case.entry.quote:
            raise ValueError("historical case spot pair mismatch")
        return self.case.spot_close_instrument_id, self.case.spot_close_book

    async def delivery_settlement(
        self,
        future_instrument_id: str,
        base: str,
        quote: str = "USDT",
    ) -> DeliverySettlement | None:
        if base != self.case.entry.base or quote != self.case.entry.quote:
            return None
        if future_instrument_id != self.case.entry.future_instrument_id:
            return None
        return self.case.settlement


async def run_cash_and_carry_backtest(
    cases: tuple[HistoricalCashAndCarryCase, ...],
    *,
    capital: Decimal,
    assumptions: CashAndCarryAssumptions,
    liquidity_policy: LiquidityPolicy = LiquidityPolicy.STRICT,
    max_impact_bps: Decimal = Decimal(10),
) -> CashAndCarryBacktestReport:
    if not cases:
        raise ValueError("historical backtest requires at least one case")
    if capital <= 0:
        raise ValueError("capital must be positive")

    results: list[CashAndCarryBacktestCaseResult] = []
    realized_returns: list[Decimal] = []

    for case in cases:
        market = _HistoricalCaseMarketData(case)
        opportunities = MemoryOpportunityRepository()
        simulations = MemorySimulationRepository()
        discovery = DiscoverCashAndCarry(market, opportunities)

        try:
            simulated = await SimulateCashAndCarry(
                discovery,
                simulations,
            ).execute(
                base=case.entry.base,
                future_instrument_id=case.entry.future_instrument_id,
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
            candidate = next(
                item
                for item in discovered
                if item.snapshot.future_instrument_id
                == case.entry.future_instrument_id
            )
            results.append(
                CashAndCarryBacktestCaseResult(
                    case_id=case.case_id,
                    observed_at=case.entry.observed_at.isoformat(),
                    expiry=case.entry.expiry.isoformat(),
                    qualified=False,
                    qualification_reasons=candidate.qualification.reasons,
                    expected_net_return=(
                        candidate.evaluation.expected_net_return_to_expiry
                    ),
                    realized_net_return=None,
                    initial_delta_pct=None,
                    return_complete=None,
                    basis_convergence=None,
                    residual_directional_pnl=None,
                    deployment_policy=candidate.deployment.policy.value,
                    partial_deployment=(
                        candidate.deployment.partial_deployment
                    ),
                    risk_states=(),
                    evidence_ids=case.evidence_ids,
                )
            )
            continue

        market.delivered = True
        closed = await CloseCashAndCarry(
            market,
            simulations,
        ).execute(simulated.execution.position.id)

        expected = simulated.plan.expected_economics
        if expected is None:
            raise RuntimeError("historical simulation has no expected economics")

        realized_return = closed.current_return.net_pnl / capital
        realized_returns.append(realized_return)
        deployment = simulated.plan.deployment
        results.append(
            CashAndCarryBacktestCaseResult(
                case_id=case.case_id,
                observed_at=case.entry.observed_at.isoformat(),
                expiry=case.entry.expiry.isoformat(),
                qualified=True,
                qualification_reasons=(),
                expected_net_return=expected.expected_net_return,
                realized_net_return=realized_return,
                initial_delta_pct=abs(
                    simulated.execution.position.delta_pct
                ),
                return_complete=closed.current_return.complete,
                basis_convergence=closed.current_return.basis_convergence,
                residual_directional_pnl=(
                    closed.current_return.residual_directional_pnl
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
                        (
                            invariant.name,
                            invariant.state.value,
                        )
                        for invariant in simulated.risk.invariants
                    )
                ),
                evidence_ids=case.evidence_ids,
            )
        )

    qualified_count = sum(1 for item in results if item.qualified)
    complete_return_count = sum(
        1 for item in results if item.return_complete is True
    )
    return CashAndCarryBacktestReport(
        strategy="cash-and-carry",
        sample_count=len(results),
        qualified_count=qualified_count,
        qualification_rate=Decimal(qualified_count) / Decimal(len(results)),
        closed_count=len(realized_returns),
        complete_return_count=complete_return_count,
        mean_realized_net_return=(
            sum(realized_returns, Decimal(0)) / Decimal(len(realized_returns))
            if realized_returns
            else None
        ),
        median_realized_net_return=(
            median(realized_returns) if realized_returns else None
        ),
        minimum_realized_net_return=(
            min(realized_returns) if realized_returns else None
        ),
        maximum_realized_net_return=(
            max(realized_returns) if realized_returns else None
        ),
        cases=tuple(results),
    )
