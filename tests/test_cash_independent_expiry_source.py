from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/probe_cash_independent_expiries.py"
REGISTRY = ROOT / "docs/historical-acquisition-plans/cash-independent-expiry-source-probes-v1.json"
WORKFLOW = ROOT / ".github/workflows/probe-cash-independent-expiries.yml"
spec = importlib.util.spec_from_file_location("cash_independent_source_probe", SCRIPT)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def registry():
    return json.loads(REGISTRY.read_text())


def test_candidates_are_unpinned_distinct_expiries_and_before_observation():
    raw = registry()
    assert raw["source_availability_status"] == "unverified"
    assert raw["acquisition_approved"] is False
    assert raw["promotion_approved"] is False
    assert raw["outcome_blind"] is True
    pinned = probe.pinned_cash_futures()
    assert pinned == set(raw["known_pinned_futures_expiries"])
    selected = probe.validated_candidates(raw, pinned)
    assert len(selected) == 2
    assert all(row["future_id"] not in pinned for row in selected)
    assert {row["id"] for row in selected} == {"2025q2", "2026q3"}
    wf = WORKFLOW.read_text()
    for row in selected:
        assert row["id"] in wf
    assert "contents: read" in wf
    assert "workflow_dispatch:" in wf
    assert "fail-fast: false" in wf
    assert "promote-" not in wf
    assert "git push" not in wf
    assert "full_orderbook_source_readiness" in SCRIPT.read_text()


@pytest.mark.parametrize("change,match", [
    (lambda d: d["candidates"][0].update({"future_id": "BTC-USDT-250926"}), "identity or date"),
    (lambda d: d["candidates"][0].update({"future_id": "BTC-USDT-260925"}), "identity or date"),
    (lambda d: d["candidates"][0].update({"exit_market_date": "2025-06-01"}), "identity or date"),
    (lambda d: d["candidates"][0].update({"exit_market_date": "2025-06-27"}), "identity or date"),
    (lambda d: d["candidates"][0].update({"expiry_at": "2025-06-27T09:00:00+00:00"}), "identity or date"),
    (lambda d: d["candidates"][1].update({"id": "2025q2"}), "duplicate"),
    (lambda d: d.update({"acquisition_approved": True}), "governance"),
    (lambda d: d.update({"known_pinned_futures_expiries": []}), "governance"),
    (lambda d: d["candidates"].append(copy.deepcopy(d["candidates"][0])), "two frozen"),
])
def test_rejects_pinned_drift_or_invalid_contract_constraints(change, match):
    raw = registry()
    change(raw)
    with pytest.raises(ValueError, match=match):
        probe.validated_candidates(raw, probe.pinned_cash_futures())


def _future_evidence(day: str, contract: str):
    return {
        "market_date": day,
        "status": "multiple_future_contracts",
        "catalog": {
            "raw_sha256": "a" * 64,
            "archive_members": [f"{contract}-L2orderbook-400lv-{day}.data"],
        },
        "future_candidates": [{"instrument_id": contract}],
    }


def test_probe_never_claims_complete_l2_from_catalog_only(monkeypatch, tmp_path):
    candidate = registry()["candidates"][0]
    monkeypatch.setattr(
        probe, "source_discovery",
        lambda day, dest: _future_evidence(day, candidate["future_id"]),
    )
    monkeypatch.setattr(
        probe, "spot_archive_catalog_status",
        lambda client, day: {"status": "catalog_identity_only"},
    )
    result = probe.probe_candidate(candidate, tmp_path, object())
    assert result["source_identity_verified"] is True
    assert result["complete_l2_sample_verified"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False
    assert len(result["dates"]) == 2


def test_missing_spot_or_wrong_future_fails_closed(monkeypatch, tmp_path):
    candidate = registry()["candidates"][0]
    monkeypatch.setattr(
        probe, "source_discovery",
        lambda day, dest: _future_evidence(day, "BTC-USDT-250926"),
    )
    monkeypatch.setattr(
        probe, "spot_archive_catalog_status",
        lambda client, day: {"status": "unavailable"},
    )
    result = probe.probe_candidate(candidate, tmp_path, object())
    assert result["source_identity_verified"] is False
    assert result["complete_l2_sample_verified"] is False
    assert result["dates"]["entry"]["future"]["status"] == "unavailable"
