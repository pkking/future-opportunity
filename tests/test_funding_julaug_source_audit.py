"""Offline safeguards for immutable Funding Jul/Aug source-run research audit."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date,timedelta
import importlib.util

import pytest

ROOT=Path(__file__).parents[1]
SOURCE=ROOT/"docs/research/funding-2026-julaug-source-run-audit-v1.json"
REGISTRY=ROOT/"docs/historical-acquisition-plans/funding-2026-jul-aug-regime-source-windows-v1.json"
SCRIPT=ROOT/"scripts/audit_funding_julaug_source_artifacts.py"


def _audit():
    spec=importlib.util.spec_from_file_location("funding_source_auditor",SCRIPT)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frozen_source_run_identity_and_population() -> None:
    doc=json.loads(SOURCE.read_text())
    prereg=json.loads(REGISTRY.read_text())
    assert doc["issue_number"] == 85
    assert doc["run_id"] == 39102598192
    assert doc["run_head_sha"] == "2228bab91ce74b83abef54ffb544286cc90f29d8"
    assert doc["run_event"] == "workflow_dispatch"
    assert doc["run_conclusion"] == "success"
    assert [x["id"] for x in doc["windows"]] == [x["id"] for x in prereg["candidate_windows"]]
    all_dates=set()
    for item,frozen in zip(doc["windows"],prereg["candidate_windows"],strict=True):
        assert (item["first"],item["last"],item["seed"]) == (
            frozen["start_date"],frozen["end_date"],frozen["seed"])
        assert len(item["zip_sha256"])==len(item["source_sha256"])==64
        assert item["raw_feature_days"] == 7
        assert item["eligible_new_days"] == 7-len(item["pinned_market_dates"])
        assert sum(item["regimes"].values()) == 7
        assert len(item["selected_dates"]) <= 8
        window={str(date.fromisoformat(item["first"])+timedelta(days=i)) for i in range(7)}
        assert all_dates.isdisjoint(window)
        all_dates.update(window)
        assert set(item["selected_dates"])<=window-set(item["pinned_market_dates"])
    assert len(all_dates) == doc["raw_feature_days"] == 21
    assert doc["new_eligible_days"] == 20
    assert doc["total_selected_new_days"] == sum(len(w["selected_dates"]) for w in doc["windows"]) == 8
    assert doc["previously_pinned_days"] == ["2026-08-29"]
    assert doc["regime_population_all_observed"] == {
        "negative_low_volatility":0,"negative_high_volatility":2,
        "nonnegative_low_volatility":7,"nonnegative_high_volatility":12}
    assert not doc["acquisition_approved"] and not doc["promotion_approved"]
    assert doc["stage2_economics_gate_enabled"] is False
    assert doc["live_order_execution_approved"] is False
    assert doc["point_in_time_publication_verified"] is False
    assert doc["source_authentication_status"] == "requires_independent_review"


def test_replay_script_is_offline_and_fails_closed_on_missing_wrong_artifacts(tmp_path:Path):
    auditor=_audit()
    doc=json.loads(SOURCE.read_text())
    script=SCRIPT.read_text()
    assert "httpx" not in script and "requests." not in script and "urllib.request" not in script
    assert "reconstruct_funding_regime_features" in script
    assert "plan_funding_regime_research" in script
    with pytest.raises(ValueError,match="exactly three"):
        auditor.audit_run({},doc)
    bad=tmp_path/"wrong.zip"
    bad.write_bytes(b"not an original Actions source ZIP")
    with pytest.raises(ValueError,match="SHA-256"):
        auditor.audit_zip(bad,doc["windows"][0])
