from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
p = ROOT / "scripts/freeze_cash_2025q2_selection.py"
spec = importlib.util.spec_from_file_location("cash_q2_selection_control", p)
assert spec and spec.loader
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def inputs():
    registry = json.loads(control.REGISTRY.read_text())
    member_audit = json.loads(control.AUDIT.read_text())
    manifest = json.loads(control.MANIFEST.read_text())
    corpus = json.loads(control.CORPUS.read_text())
    dates = [entry["entry_market_date"] for entry in corpus["entries"]
             if entry["strategy"] == "cash-and-carry"]
    selected = set(registry["selected_market_dates"])
    assert (set(dates) & selected) in (set(), selected)
    dates = [d for d in dates if d not in selected]
    return registry, member_audit, manifest, dates


def test_approved_selection_control_produces_inert_evidence():
    registry, audit, manifest, pinned = inputs()
    report = control.build_control(
        registry, audit, manifest, pinned_dates=pinned,
        registration_sha256="a" * 64,
    )
    assert report["historical_selection_frozen"] is True
    assert report["approval_merge_commit"] == "4acf3e945769d49dd001b686ad1cd114f5bb32f8"
    assert report["approval_main_ci_run"] == "39050288482"
    assert report["selection_evidence_sha256"] == control.EXPECTED_SELECTION_SHA
    assert report["selected_market_dates"] == list(control.EXPECTED_SELECTED)
    assert len(report["selected_market_dates"]) == 12
    assert report["excluded_market_dates"] == ["2025-06-26"]
    assert report["member_source_verified_for_calendar"] is True
    assert report["sampled_l2_verified"] is False
    assert report["economic_outcomes_inspected"] is False
    assert report["acquisition_approved"] is False
    assert report["promotion_approved"] is False
    assert report["live_trading_enabled"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update({"selected_market_dates": list(reversed(r["selected_market_dates"]))}),
    lambda r: r.update({"excluded_market_dates": []}),
    lambda r: r.update({"selection_evidence_sha256": "0" * 64}),
    lambda r: r["invariants"].update({"independent_human_preregistration_review_required": False}),
    lambda r: r.update({"future_id": "BTC-USDT-251226"}),
])
def test_unapproved_or_modified_selection_fails_closed(mutation):
    registry, audit, manifest, pinned = inputs()
    bad = copy.deepcopy(registry)
    mutation(bad)
    with pytest.raises(ValueError):
        control.build_control(bad, audit, manifest, pinned_dates=pinned,
                              registration_sha256="a" * 64)


def test_invalid_registration_digest_fails_closed():
    registry, audit, manifest, pinned = inputs()
    with pytest.raises(ValueError, match="registration or SHA"):
        control.build_control(registry, audit, manifest, pinned_dates=pinned,
                              registration_sha256="not-sha")


def test_cli_replay_writes_evidence_without_acquisition(tmp_path, monkeypatch):
    registry, audit, manifest, pinned = inputs()
    corpus = json.loads(control.CORPUS.read_text())
    corpus["entries"] = [
        e for e in corpus["entries"]
        if e["strategy"] != "cash-and-carry"
        or e["entry_market_date"] not in registry["selected_market_dates"]
    ]
    fixture = tmp_path / "corpus-before-approved-promotion.json"
    fixture.write_text(json.dumps(corpus))
    monkeypatch.setattr(control, "CORPUS", fixture)
    monkeypatch.setattr(sys, "argv", [str(p), "--output", str(tmp_path / "control.json")])
    control.main()
    report = json.loads((tmp_path / "control.json").read_text())
    assert report["acquisition_approved"] is False
    assert report["promotion_approved"] is False
    assert report["historical_selection_frozen"] is True
