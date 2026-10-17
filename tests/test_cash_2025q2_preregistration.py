from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/validate_cash_2025q2_preregistration.py"
spec = importlib.util.spec_from_file_location("cash_q2_source_selection", SCRIPT)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def registered():
    registry = json.loads(validator.REGISTRY.read_text())
    audit = json.loads(validator.AUDIT.read_text())
    manifest = json.loads(validator.MANIFEST.read_text())
    corpus = json.loads(validator.CORPUS.read_text())
    pinned = [x["entry_market_date"] for x in corpus["entries"]
              if x["strategy"] == "cash-and-carry"]
    return registry, audit, manifest, pinned


def test_source_bound_preregistration_replay_is_outcome_blind():
    registry, audit, manifest, pinned = registered()
    result = validator.validate_selection(
        registry, audit, manifest, pinned_dates=pinned
    )
    assert result["eligible_population_size"] == 89
    assert result["selected_market_dates"] == [
        "2025-04-01", "2025-04-09", "2025-04-16", "2025-04-23",
        "2025-05-01", "2025-05-08", "2025-05-16", "2025-05-23",
        "2025-05-31", "2025-06-07", "2025-06-14", "2025-06-22",
    ]
    assert result["selection_evidence_sha256"] == (
        "9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37"
    )
    assert result["independent_human_review_required"] is True
    assert result["historical_selection_approved"] is False
    assert result["complete_selected_l2_verified"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update({"requested_sample_size": 11}),
    lambda r: r.update({"selection_policy_version": "unapproved"}),
    lambda r: r.update({"selected_market_dates": r["selected_market_dates"][1:]}),
    lambda r: r.update({"selection_evidence_sha256": "0" * 64}),
    lambda r: r.update({"excluded_market_dates": []}),
    lambda r: r.update({"eligible_population_size": 90}),
    lambda r: r.update({"source_unavailable_market_dates": ["2025-03-29"]}),
    lambda r: r["source_evidence"].update({"member_run": "untrusted-run"}),
    lambda r: r["invariants"].update({"automatic_promotion": True}),
    lambda r: r["invariants"].update({"independent_human_preregistration_review_required": False}),
])
def test_reject_bad_source_or_selection_before_any_acquisition(mutation):
    registry, audit, manifest, pinned = registered()
    changed = copy.deepcopy(registry)
    mutation(changed)
    with pytest.raises(ValueError):
        validator.validate_selection(changed, audit, manifest, pinned_dates=pinned)


def test_cannot_promote_member_catalog_to_complete_l2():
    registry, audit, manifest, pinned = registered()
    changed = copy.deepcopy(audit)
    changed["l2_orderbook_verified"] = True
    with pytest.raises(ValueError):
        validator.validate_selection(registry, changed, manifest, pinned_dates=pinned)


def test_missing_source_day_is_not_silently_an_eligible_entry():
    registry, audit, manifest, pinned = registered()
    changed = copy.deepcopy(audit)
    changed["counts"]["identity_verified"] = 89
    changed["counts"]["unavailable"] = 1
    with pytest.raises(ValueError):
        validator.validate_selection(registry, changed, manifest, pinned_dates=pinned)


def test_overlapping_pinned_day_fails():
    registry, audit, manifest, pinned = registered()
    with pytest.raises(ValueError, match="pinned corpus"):
        validator.validate_selection(
            registry, audit, manifest,
            pinned_dates=pinned + [registry["selected_market_dates"][0]],
        )


def test_cli_writes_review_only_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", [
        str(SCRIPT), "--output", str(tmp_path / "proposal.json")
    ])
    validator.main()
    report = json.loads((tmp_path / "proposal.json").read_text())
    assert report["historical_selection_approved"] is False
    assert report["independent_human_review_required"] is True
