from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from future_opportunity.domain.deployment.model import DeploymentAssessment


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class StrategyRef:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class PlanLeg:
    id: str
    instrument_id: str
    side: str
    target_notional: Money


@dataclass(frozen=True, slots=True)
class CapitalPolicy:
    reserve_ratio: Decimal
    futures_leverage: Decimal


@dataclass(frozen=True, slots=True)
class ExecutionCostPolicy:
    spot_entry_fee_bps: Decimal
    derivative_entry_fee_bps: Decimal
    spot_exit_fee_bps: Decimal
    derivative_exit_fee_bps: Decimal
    exit_buffer_bps: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class ExpectedEconomics:
    return_character: str
    horizon_type: str
    horizon_days: Decimal
    expected_net_return: Decimal
    annualized_equivalent: Decimal
    expected_cost_return: Decimal
    expected_net_pnl: Decimal
    expected_cost_pnl: Decimal


@dataclass(frozen=True, slots=True)
class StrategyPlan:
    id: str
    strategy: StrategyRef
    opportunity_observation_id: str
    venue: str
    base: str
    quote: str
    capital: Money
    legs: tuple[PlanLeg, ...]
    max_delta_pct: Decimal
    max_leverage: Decimal
    execution_mode: str = "paper"
    capital_policy: CapitalPolicy | None = None
    execution_cost_policy: ExecutionCostPolicy | None = None
    deployment: DeploymentAssessment | None = None
    expected_economics: ExpectedEconomics | None = None
