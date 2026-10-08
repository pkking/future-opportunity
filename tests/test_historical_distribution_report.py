from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.application.backtest.cash_and_carry import (
    CashAndCarryBacktestCaseResult,
)
from future_opportunity.application.backtest.funding_carry import (
    FundingCarryBacktestCaseResult,
)
from future_opportunity.backtest.distribution_report import (
    _selection_provenance_view,
    _summary,
    build_historical_corpus_distribution,
    decimal_distribution,
)
from future_opportunity.backtest.evidence import write_backtest_evidence
from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_payload,
    sample_historical_market_days,
)
from future_opportunity.backtest.selection_provenance import (
    historical_selection_provenance_payload,
    selection_provenance_from_sampling_evidence,
)


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests/fixtures/historical"
INDEX = FIXTURES / "corpus-index.json"
POLICY = ROOT / "tests/e2e/historical-target-policy.json"


def test_decimal_distribution_has_nulls_for_no_assessed_samples() -> None:
    empty = decimal_distribution(())
    assert empty.assessed_count == 0
    assert empty.minimum is None
    assert empty.p25 is None
    assert empty.median is None
    assert empty.p90 is None
    assert empty.maximum is None
    assert empty.mean is None

    single = decimal_distribution((Decimal("0.03"),))
    assert single.assessed_count == 1
    assert (single.p25, single.median, single.p90) == (
        Decimal("0.03"),
        Decimal("0.03"),
        Decimal("0.03"),
    )


def test_decimal_distribution_uses_documented_linear_quantiles() -> None:
    result = decimal_distribution(
        (Decimal(30), Decimal(10), Decimal(0), Decimal(20))
    )
    assert result.assessed_count == 4
    assert result.minimum == Decimal(0)
    assert result.p25 == Decimal("7.5")
    assert result.median == Decimal(15)
    assert result.p90 == Decimal(27)
    assert result.maximum == Decimal(30)
    assert result.mean == Decimal(15)


def test_funding_summary_never_counts_unassessed_as_zero_realized() -> None:
    common = {
        "entry_at": "2026-09-01T00:15:00+00:00",
        "exit_at": "2026-09-01T23:45:00+00:00",
        "assessed_ex_funding_pnl": None,
        "funding_cash_flow_lower": None,
        "funding_cash_flow_upper": None,
        "realized_return_lower": None,
        "realized_return_upper": None,
        "funding_event_count": 0,
        "funding_interval_evidence_complete": False,
        "initial_delta_pct": None,
        "deployment_policy": "strict",
        "partial_deployment": False,
        "risk_states": (),
        "evidence_ids": ("source",),
    }
    cases = (
        FundingCarryBacktestCaseResult(
            case_id="qualified-unassessed",
            qualified=True,
            qualification_reasons=(),
            expected_net_return=Decimal("0.01"),
            **common,
        ),
        FundingCarryBacktestCaseResult(
            case_id="rejected",
            qualified=False,
            qualification_reasons=("expected_net_return_not_positive",),
            expected_net_return=Decimal("-0.01"),
            **common,
        ),
    )
    summary = _summary(cases, strategy="funding-carry")

    assert summary["pinned_case_qualification_rate"] == Decimal("0.5")
    assert summary["market_wide_opportunity_arrival_rate"] is None
    assert summary["qualified_cases_with_assessed_realized_return"] == 0
    assert summary["qualified_cases_with_unassessed_realized_return"] == 1
    lower = summary["realized_return"]["realized_return_interval_lower"]
    assert lower["assessed_count"] == 0
    assert lower["mean"] is None
    assert summary["qualification_reason_case_counts"] == {
        "expected_net_return_not_positive": 1
    }


def test_cash_summary_excludes_incomplete_realized_even_if_numeric() -> None:
    case = CashAndCarryBacktestCaseResult(
        case_id="incomplete",
        observed_at="2026-06-01T00:15:00+00:00",
        expiry="2026-06-26T08:00:00+00:00",
        exit_at="2026-06-25T00:15:00+00:00",
        close_mode="pre-expiry",
        qualified=True,
        qualification_reasons=(),
        expected_net_return=Decimal("0.03"),
        realized_net_return=Decimal("0.02"),
        initial_delta_pct=Decimal(0),
        return_complete=False,
        basis_convergence=Decimal(0),
        residual_directional_pnl=Decimal(0),
        deployment_policy="strict",
        partial_deployment=False,
        risk_states=(),
        evidence_ids=("source",),
    )
    summary = _summary((case,), strategy="cash-and-carry")

    assert summary["qualified_case_count"] == 1
    assert summary["qualified_cases_with_assessed_realized_return"] == 0
    assert summary["qualified_cases_with_unassessed_realized_return"] == 1
    assert summary["realized_return"]["realized_net_return_with_complete_evidence"][
        "median"
    ] is None


@pytest.mark.asyncio
async def test_report_replays_all_versioned_corpus_days_offline(
    tmp_path: Path,
) -> None:
    report = await build_historical_corpus_distribution(
        fixture_root=FIXTURES,
        index_path=INDEX,
        policy_path=POLICY,
    )
    entries = json.loads(INDEX.read_text())["entries"]
    assert report["evidence_type"] == "historical_corpus_distribution_actuals"
    assert report["economics_gate"] == "reporting_only"
    assert report["reference_targets_used_as_thresholds"] is False
    assert report["capital_usdt"] == Decimal("10000")

    stage2 = report["stage2_decision_quality"]
    assert stage2["adr"] == "ADR-0008"
    assert stage2["status"] == "accepted"
    assert stage2["economics_gate"] == "disabled"
    funding_stage2 = stage2["strategies"]["funding-carry"]
    assert funding_stage2["enabled"] is True
    assert funding_stage2["decision_quality_ready"] is True
    assert funding_stage2["qualified_case_count"] == 0
    assert funding_stage2["realized_return_gate_available"] is False
    assert funding_stage2["market_wide_opportunity_arrival_rate"] is None
    cash_stage2 = stage2["strategies"]["cash-and-carry"]
    assert cash_stage2["enabled"] is False
    assert cash_stage2["decision_quality_ready"] is False
    assert "strategy_not_stage2_enabled" in cash_stage2["reasons"]

    # Independently read indexed manifests rather than assuming the corpus
    # contains only legacy fixtures. The report must track provenance growth
    # without converting it into a historical economics pass/fail target.
    expected_classification = {
        entry["dataset_id"]: (
            "pre_registered_sample"
            if json.loads(
                (FIXTURES / entry["fixture_path"] / "manifest.json").read_text()
            ).get("selection_provenance") is not None
            else "legacy_untracked"
        )
        for entry in entries
    }
    pre_registered = sum(
        status == "pre_registered_sample"
        for status in expected_classification.values()
    )

    coverage = report["selection_provenance_coverage"]
    assert coverage["total_pinned_day_count"] == len(entries)
    assert coverage["pre_registered_sample_day_count"] == pre_registered
    assert coverage["legacy_untracked_day_count"] == (
        len(entries) - pre_registered
    )
    assert coverage["pre_registered_coverage_ratio"] == (
        Decimal(pre_registered) / Decimal(len(entries))
    )
    assert "readiness still counts all validated" in coverage[
        "readiness_semantics"
    ]

    for strategy in ("funding-carry", "cash-and-carry"):
        pinned = {
            entry["dataset_id"]
            for entry in entries
            if entry["strategy"] == strategy
        }
        cases = report["cases"][strategy]
        assert {item["provenance"]["dataset_id"] for item in cases} == pinned
        summary = report["strategies"][strategy]
        assert summary["pinned_entry_market_day_count"] == len(pinned)
        assert summary["evaluated_case_count"] == len(cases)
        assert summary["market_wide_opportunity_arrival_rate"] is None
        assert summary["economics_gate"] == "reporting_only"
        assert all(item["actual"]["evidence_ids"] for item in cases)

        selected_count = sum(
            expected_classification[dataset_id] == "pre_registered_sample"
            for dataset_id in pinned
        )
        strategy_coverage = coverage["by_strategy"][strategy]
        assert strategy_coverage["pinned_day_count"] == len(pinned)
        assert strategy_coverage["pre_registered_sample_day_count"] == (
            selected_count
        )
        assert strategy_coverage["legacy_untracked_day_count"] == (
            len(pinned) - selected_count
        )
        assert strategy_coverage["pre_registered_coverage_ratio"] == (
            Decimal(selected_count) / Decimal(len(pinned))
        )

        for item in cases:
            dataset_id = item["provenance"]["dataset_id"]
            selection = item["provenance"]["selection"]
            expected = expected_classification[dataset_id]
            assert selection["classification"] == expected
            assert (selection["source"] is not None) == (
                expected == "pre_registered_sample"
            )

    destination = tmp_path / "distribution.json"
    write_backtest_evidence(report, destination)
    serialized = json.loads(destination.read_text())
    assert serialized["economics_gate"] == "reporting_only"
    assert all(
        item["provenance"]["dataset_id"]
        for items in serialized["cases"].values()
        for item in items
    )


def test_selection_provenance_reporting_distinguishes_preregistered_from_legacy() -> None:
    legacy = _selection_provenance_view(
        {},
        strategy="funding-carry",
        market_date="2026-09-01",
    )
    assert legacy["classification"] == "legacy_untracked"
    assert legacy["source"] is None

    sample = historical_sampling_payload(
        sample_historical_market_days(
            HistoricalSamplingRequest(
                strategy="funding-carry",
                start_date="2026-09-01",
                end_date="2026-09-01",
                sample_size=1,
                seed="report-selection-test",
            )
        )
    )
    provenance = historical_selection_provenance_payload(
        selection_provenance_from_sampling_evidence(
            sample,
            source_workflow_run="123",
            artifact_name="sample-123",
            artifact_id="456",
            artifact_digest="sha256:" + "a" * 64,
        )
    )
    tracked = _selection_provenance_view(
        {"selection_provenance": provenance},
        strategy="funding-carry",
        market_date="2026-09-01",
    )
    assert tracked["classification"] == "pre_registered_sample"
    assert tracked["selection_kind"] == "pre_registered_sample"
    assert tracked["source"]["workflow_run"] == "123"
