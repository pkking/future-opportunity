from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/probe_cash_2025q2_source_calendar.py"
REGISTRY = ROOT / "docs/historical-acquisition-plans/cash-2025q2-source-capacity-study-v1.json"
WORKFLOW = ROOT / ".github/workflows/probe-cash-2025q2-source-calendar.yml"
spec = importlib.util.spec_from_file_location("cash_q2_catalog_calendar", SCRIPT)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def study():
    return json.loads(REGISTRY.read_text())


def test_fixed_outcome_blind_q2_calendar_has_all_ninety_days():
    dates = probe.frozen_daily_population(study())
    assert len(dates) == len(set(dates)) == 90
    assert dates[0] == "2025-03-29"
    assert dates[-1] == "2025-06-26"
    assert study()["candidate_selection_prohibited_until_source_verification"] is True
    assert study()["acquisition_approved"] is False
    assert study()["promotion_approved"] is False


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.update({"target_sample_size": 13}),
    lambda raw: raw.update({"study_end_date": "2025-06-25"}),
    lambda raw: raw.update({"future_id": "BTC-USDT-250926"}),
    lambda raw: raw.update({"economic_outcomes_inspected": True}),
    lambda raw: raw.update({"acquisition_approved": True}),
])
def test_date_source_or_outcome_tampering_fails(mutation):
    raw = copy.deepcopy(study())
    mutation(raw)
    with pytest.raises(ValueError):
        probe.frozen_daily_population(raw)


def test_empty_official_catalog_is_unavailable_not_faked():
    query = probe.catalog_query("2025-06-12", "FUTURES")
    result = probe.classify_catalog_response(
        {"code": "0", "data": []}, query, "2025-06-12"
    )
    assert result["status"] == "missing"
    assert result["candidate_count"] == 0
    assert result["contract_member_inside_futures_archive_verified"] is False
    assert result["sampled_book_verified"] is False


def test_bounded_scan_preserves_each_raw_source_digest_and_empty_days(monkeypatch):
    monkeypatch.setattr(probe, "get_response", lambda client, query: {"code": "0", "data": []})
    monkeypatch.setattr(probe.time, "sleep", lambda seconds: None)
    days = ("2025-06-12", "2025-06-13")
    rows, raw = probe.scan_population(object(), days)
    summary = probe.summary_for(days, rows)
    assert len(rows) == 2 and len(raw) == 4
    assert all(len(x["sha256"]) == 64 for x in raw.values())
    assert summary["source_population_complete"] is True
    assert summary["paired_catalog_day_count"] == 0
    assert summary["historical_selection_frozen"] is False
    assert summary["sampled_economic_returns_inspected"] is False
    assert summary["promotion_approved"] is False
    with pytest.raises(ValueError, match="all frozen dates"):
        probe.summary_for(days, rows[:-1])


def test_immutable_scan_is_read_only_and_nonpromotable():
    workflow = WORKFLOW.read_text()
    code = SCRIPT.read_text()
    assert "contents: read" in workflow
    assert "workflow_dispatch:" in workflow
    assert "source-calendar-report.json" in code
    assert "catalog-raw-api-capture.json" in code
    assert "run_cash_historical_backtest" not in code
    assert "promote_historical" not in code
    assert "git push" not in workflow
    assert "acquisition_approved" in code
