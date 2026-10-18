"""Schema and provenance regressions for the two-run Q2 research evidence index.

This file is an audit-only index. It must never silently become a pinned
corpus promotion or imply the 12 dates are 12 independent expiries.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).parents[1]
AUDIT = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-cross-run-audit-v1.json"
SELECTION = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json"


def load() -> tuple[dict, dict]:
    return json.loads(AUDIT.read_text()), json.loads(SELECTION.read_text())


def test_audit_covers_exact_original_preregistered_population() -> None:
    audit, frozen = load()
    assert audit["evidence_type"] == "cash_2025q2_cross_run_complete_research_audit_index"
    assert audit["registration_policy"] == frozen["selection_policy_version"]
    assert audit["selection_evidence_sha256"] == frozen["selection_evidence_sha256"]
    assert audit["registered_entry_date_count"] == frozen["requested_sample_size"] == 12
    assert audit["source_registry_population_size"] == frozen["eligible_population_size"] == 89
    assert audit["contract"] == frozen["future_id"]
    assert audit["exit_at"] == frozen["exit_at"]
    assert audit["expiry_at"] == frozen["expiry_at"]
    assert [c["entry_market_date"] for c in audit["cases"]] == frozen["selected_market_dates"]
    assert audit["selection_control"]["artifact_id"] == 12106828444
    assert audit["results"]["complete_case_count"] == 12
    assert audit["results"]["missing_case_count"] == 0


def test_only_the_failed_day_was_repaired_and_all_36_artifacts_are_traceable() -> None:
    audit, _ = load()
    cases = audit["cases"]
    runs = {r["run_id"] for r in audit["acquisition_runs"]}
    assert runs == {39079100154, 39091438598}
    assert cases[1]["entry_market_date"] == "2025-04-09"
    assert cases[1]["source_run_id"] == 39091438598
    assert all(c["source_run_id"] == 39079100154 for c in cases if c["entry_market_date"] != "2025-04-09")
    assert audit["acquisition_runs"][0]["run_conclusion"] == "failure"
    assert audit["acquisition_runs"][1]["run_conclusion"] == "success"
    seen_ids = set()
    names = set()
    for case in cases:
        assert set(case["artifacts"]) == {"prepared", "compact", "actuals"}
        for kind, artifact in case["artifacts"].items():
            assert isinstance(artifact["id"], int)
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["zip_sha256"])
            assert artifact["id"] not in seen_ids
            assert artifact["name"] not in names
            assert artifact["name"].endswith(
                f"-{case['entry_market_date']}-BTC-USDT-250627-{case['source_run_id']}"
            )
            if kind == "compact":
                assert "cash-and-carry-compact-" in artifact["name"]
            elif kind == "actuals":
                assert "cash-and-carry-actuals-" in artifact["name"]
            else:
                assert "cash-and-carry-20" in artifact["name"]
            seen_ids.add(artifact["id"])
            names.add(artifact["name"])
    assert len(seen_ids) == len(names) == audit["results"]["prepared_compact_actuals_artifact_count"] == 36


def test_negative_observations_are_not_replaced_with_zero_or_synthetic_returns() -> None:
    audit, _ = load()
    cases = audit["cases"]
    qualified = [c for c in cases if c["qualification"] == "qualified"]
    rejected = [c for c in cases if c["qualification"] == "unqualified"]
    assert len(qualified) == audit["results"]["qualified_case_count"] == 9
    assert len(rejected) == audit["results"]["unqualified_case_count"] == 3
    assert [c["entry_market_date"] for c in rejected] == [
        "2025-06-07", "2025-06-14", "2025-06-22"
    ]
    assert all(c["qualification_reasons"] == ["expected_net_return_not_positive"] for c in rejected)
    assert all(c["realized_paper_net_return"] is None and not c["return_complete"] for c in rejected)
    assert all(c["return_complete"] and Decimal(c["realized_paper_net_return"]) > 0 for c in qualified)
    assert Decimal(audit["results"]["conditional_mean_paper_realized_net_return_executed_only"]) > 0
    assert audit["results"]["max_book_staleness_ms"] <= 5000


def test_research_audit_does_not_grant_corpus_promotion_or_trading_permission() -> None:
    audit, _ = load()
    policy = audit["policy_boundaries"]
    for key in ("corpus_promotion_approved", "stage2_economics_gate_activated",
                "margin_safety_fully_assessed", "venue_exposure_fully_assessed",
                "live_trading_enabled"):
        assert policy[key] is False
    assert policy["baseline_cash_cases"] == 54
    assert policy["baseline_funding_cases"] == 32
    assert re.fullmatch(r"[0-9a-f]{64}", audit["audit_report"]["sha256"])
    assert audit["results"]["complete_case_count"] == 12
    assert "not independent" in audit["results"]["conditional_return_warning"]
