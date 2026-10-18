from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/resolve_cash_q2_failed_source_repair.py"
spec = importlib.util.spec_from_file_location("cash_q2_one_case_repair", SCRIPT)
assert spec and spec.loader
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


def frozen_inputs():
    wave = json.loads(repair.WAVE.read_text())
    registration = json.loads(repair.REGISTRY.read_text())
    member_audit = json.loads(repair.AUDIT.read_text())
    manifest = json.loads(repair.MANIFEST.read_text())
    corpus = json.loads(repair.CORPUS.read_text())
    pinned = [e["entry_market_date"] for e in corpus["entries"]
              if e["strategy"] == "cash-and-carry"]
    selected = set(registration["selected_market_dates"])
    assert (set(pinned) & selected) in (set(), selected)
    pinned = [d for d in pinned if d not in selected]
    return wave, registration, member_audit, manifest, pinned


def test_repair_only_the_known_source_failure_retaining_all_twelve_selection_days():
    wave, registration, audit, source, pinned = frozen_inputs()
    result = repair.resolve_source_cap_repair(
        wave, registration, audit, source, pinned_dates=pinned
    )
    assert len(result["cash_cases"]) == 1
    assert result["cash_cases"][0] == {
        "entry_at": "2025-04-09T00:15:00+00:00",
        "exit_at": "2025-06-26T00:15:00+00:00",
        "future_id": "BTC-USDT-250627",
        "expiry_at": "2025-06-27T08:00:00+00:00",
    }
    assert result["funding"] is None
    assert result["acquisition_id"] == repair.REPAIR_ACQUISITION_ID
    assert result["selection_provenance"] == wave["selection_provenance"]
    assert len(result["selection_provenance"]["cash"]["sampling"]["selected_market_dates"]) == 12


@pytest.mark.parametrize("mutation", [
    lambda wave: wave["cash_cases"].pop(1),
    lambda wave: wave["cash_cases"][1].update({"entry_at": "2025-04-10T00:15:00+00:00"}),
    lambda wave: wave["cash_cases"][1].update({"future_id": "BTC-USDT-250926"}),
    lambda wave: wave["selection_provenance"]["cash"]["source"].update({"artifact_digest": "sha256:" + "0" * 64}),
    lambda wave: wave["selection_provenance"]["cash"]["sampling"].update({"selected_market_dates": []}),
])
def test_repair_refuses_any_modified_frozen_12_day_source(mutation):
    wave, registration, audit, source, pinned = frozen_inputs()
    drifted = copy.deepcopy(wave)
    mutation(drifted)
    with pytest.raises((ValueError, TypeError)):
        repair.resolve_source_cap_repair(
            drifted, registration, audit, source, pinned_dates=pinned
        )


def test_missing_target_case_cannot_be_substituted():
    wave, registration, audit, source, pinned = frozen_inputs()
    changed = copy.deepcopy(wave)
    changed["cash_cases"][1]["entry_at"] = "2025-04-08T00:15:00+00:00"
    with pytest.raises(ValueError):
        repair.resolve_source_cap_repair(
            changed, registration, audit, source, pinned_dates=pinned
        )


def test_repair_workflow_is_manual_only_and_enforces_bounded_cost():
    workflow = (ROOT / ".github/workflows/repair-cash-q2-2025-04-09-source.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "APPROVE-CASH-2025Q2-2025-04-09-SOURCE-REPAIR" in workflow
    assert "cash_max_raw_mb: 1024" in workflow
    assert "push:" not in workflow
    assert "schedule:" not in workflow
    assert "promote-historical" not in workflow
    assert "2025-04-09" in workflow


def test_cli_creates_reproducible_control_without_dispatch(tmp_path, monkeypatch):
    wave, registration, audit, source, pinned = frozen_inputs()
    corpus = json.loads(repair.CORPUS.read_text())
    corpus["entries"] = [
        e for e in corpus["entries"]
        if e["strategy"] != "cash-and-carry"
        or e["entry_market_date"] not in registration["selected_market_dates"]
    ]
    fixture = tmp_path / "corpus-before-approved-promotion.json"
    fixture.write_text(json.dumps(corpus))
    monkeypatch.setattr(repair, "CORPUS", fixture)
    op = tmp_path / "operator.json"
    control = tmp_path / "control.json"
    monkeypatch.setattr(sys, "argv", [
        str(SCRIPT), "--output", str(op), "--control-output", str(control)
    ])
    repair.main()
    plan = json.loads(op.read_text())
    evidence = json.loads(control.read_text())
    assert len(plan["cash_cases"]) == 1
    assert evidence["failed_market_date"] == "2025-04-09"
    assert evidence["repair_case_count"] == 1
    assert evidence["other_eleven_dates_untouched"] is True
    assert evidence["human_repair_dispatch_approved"] is False
    assert evidence["repair_dispatched"] is False
    assert evidence["promotion_approved"] is False
