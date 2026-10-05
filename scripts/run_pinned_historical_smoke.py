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
OUTPUT = ROOT / "artifacts/historical-smoke/evidence.json"


async def build_evidence() -> dict[str, object]:
    targets = json.loads(TARGETS.read_text())

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

    return {
        "schema_version": 1,
        "evidence_type": "pinned_historical_smoke",
        "historical_gate_semantics": "pending_human_decision",
        "decision_options": [
            "reuse_reference_per_opportunity_thresholds",
            "separate_historical_distribution_thresholds",
            "gate_provenance_and_semantics_only_report_returns",
        ],
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
                        "historical gate semantics are not yet approved"
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
        "smoke_invariants": {
            "funding_fixture_checksum_and_provenance_valid": True,
            "cash_fixture_checksum_and_provenance_valid": True,
            "funding_replay_semantics_stable": (
                not funding_actual.qualified
                and funding_actual.qualification_reasons
                == ("expected_net_return_not_positive",)
            ),
            "cash_replay_semantics_stable": (
                not cash_actual.qualified
                and cash_actual.qualification_reasons
                == ("expected_net_return_not_positive",)
            ),
        },
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        evidence = asyncio.run(build_evidence())
        write_backtest_evidence(evidence, OUTPUT)
    except Exception as error:
        write_backtest_evidence(
            {
                "schema_version": 1,
                "evidence_type": "pinned_historical_smoke",
                "historical_gate_semantics": "pending_human_decision",
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            },
            OUTPUT,
        )
        raise


if __name__ == "__main__":
    main()
