from __future__ import annotations

import asyncio
import json
import traceback
from decimal import Decimal
from pathlib import Path

from future_opportunity.application.backtest.cash_and_carry import (
    run_cash_and_carry_backtest,
)
from future_opportunity.application.backtest.funding_carry import (
    run_funding_carry_backtest,
)
from future_opportunity.backtest.cash_fixture import (
    load_cash_and_carry_close_fixture,
)
from future_opportunity.backtest.evidence import write_backtest_evidence
from future_opportunity.backtest.fixture import (
    build_funding_case,
    load_funding_history_fixture,
)
from future_opportunity.backtest.historical_policy import (
    collect_pinned_entry_market_days,
    distribution_transition_readiness,
    evaluate_historical_gate,
    load_historical_acceptance_policy,
)
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
)


ROOT = Path(__file__).parents[1]
FUNDING_FIXTURE = (
    ROOT
    / "tests/fixtures/historical"
    / "okx-btc-usdt-funding-carry-2026-09-01-v1-target-compact"
)
CASH_FIXTURE = (
    ROOT
    / "tests/fixtures/historical"
    / "okx-btc-cash-and-carry-2026-06-v1-target-compact"
)
TARGETS = ROOT / "tests/e2e/strategy-targets.json"
HISTORICAL_POLICY = ROOT / "tests/e2e/historical-target-policy.json"
HISTORICAL_FIXTURES = ROOT / "tests/fixtures/historical"
OUTPUT = ROOT / "artifacts/historical-smoke/evidence.json"


async def build_evidence() -> dict[str, object]:
    targets = json.loads(TARGETS.read_text())
    policy, raw_policy = load_historical_acceptance_policy(
        HISTORICAL_POLICY
    )

    funding_fixture = load_funding_history_fixture(FUNDING_FIXTURE)
    funding_case = build_funding_case(
        funding_fixture,
        entry_index=0,
        exit_index=1,
    )
    funding_report = await run_funding_carry_backtest(
        (funding_case,),
        capital=Decimal("10000"),
        assumptions=FundingCarryAssumptions(horizon_days=1),
    )

    cash_case = load_cash_and_carry_close_fixture(CASH_FIXTURE)
    cash_report = await run_cash_and_carry_backtest(
        (cash_case,),
        capital=Decimal("10000"),
        assumptions=CashAndCarryAssumptions(),
    )

    funding_actual = funding_report.cases[0]
    cash_actual = cash_report.cases[0]
    funding_reference = targets["scenarios"]["funding-carry-reference-v1"]
    cash_reference = targets["scenarios"][
        "cash-and-carry-delivery-reference-v1"
    ]

    semantics = raw_policy["pinned_smoke_semantics"]
    funding_expected = semantics["funding_carry"]
    cash_expected = semantics["cash_and_carry"]

    checks = {
        "funding_fixture_checksum_and_provenance_valid": True,
        "cash_fixture_checksum_and_provenance_valid": True,
        "funding_replay_semantics_stable": (
            funding_actual.qualified
            is funding_expected["qualified"]
            and list(funding_actual.qualification_reasons)
            == funding_expected["qualification_reasons"]
        ),
        "cash_replay_semantics_stable": (
            cash_actual.qualified
            is cash_expected["qualified"]
            and list(cash_actual.qualification_reasons)
            == cash_expected["qualification_reasons"]
        ),
    }
    gate_passed, evaluated_checks = evaluate_historical_gate(
        policy,
        checks,
    )
    pinned_days = collect_pinned_entry_market_days(
        HISTORICAL_FIXTURES,
        required_strategies=policy.required_strategies,
    )
    readiness = distribution_transition_readiness(
        policy,
        pinned_days,
    )

    return {
        "schema_version": 1,
        "evidence_type": "pinned_historical_smoke",
        "policy_id": policy.policy_id,
        "historical_gate_semantics": policy.mode,
        "gate": {
            "passed": gate_passed,
            "required_checks": evaluated_checks,
        },
        "distribution_transition_readiness": readiness,
        "datasets": {
            "funding_carry": {
                "dataset_id": funding_fixture.dataset_id,
                "artifact_provenance": funding_fixture.manifest.get(
                    "derived_from_artifact"
                ),
                "parent_alignment": funding_fixture.manifest.get(
                    "parent_alignment"
                ),
                "compact_alignment": funding_fixture.manifest.get("alignment"),
                "actual": funding_actual,
                "reference_target_reporting_only": {
                    "must_qualify": funding_reference["must_qualify"],
                    "min_expected_net_return": funding_reference[
                        "min_expected_net_return"
                    ],
                    "expected_net_return_delta": str(
                        funding_actual.expected_net_return
                        - Decimal(
                            funding_reference["min_expected_net_return"]
                        )
                    ),
                    "note": (
                        "reference target is displayed for context only; "
                        "V0 historical acceptance gates provenance and "
                        "replay semantics, not historical return"
                    ),
                },
            },
            "cash_and_carry": {
                "dataset_id": cash_case.case_id,
                "actual": cash_actual,
                "reference_target_reporting_only": {
                    "must_qualify": cash_reference["must_qualify"],
                    "min_realized_net_return": cash_reference[
                        "min_realized_net_return"
                    ],
                    "realized_target_comparable": (
                        cash_actual.realized_net_return is not None
                    ),
                    "note": (
                        "the historical opportunity was correctly rejected "
                        "before execution, so realized return is unavailable; "
                        "reference target is not used as a historical gate"
                    ),
                },
            },
        },
        "smoke_invariants": checks,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        evidence = asyncio.run(build_evidence())
    except Exception as error:
        write_backtest_evidence(
            {
                "schema_version": 1,
                "evidence_type": "pinned_historical_smoke",
                "policy_id": "historical-acceptance-v0",
                "historical_gate_semantics": "provenance_and_semantics",
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            OUTPUT,
        )
        raise

    write_backtest_evidence(evidence, OUTPUT)
    gate = evidence.get("gate")
    if not isinstance(gate, dict) or gate.get("passed") is not True:
        raise SystemExit("historical provenance-and-semantics gate failed")


if __name__ == "__main__":
    main()
