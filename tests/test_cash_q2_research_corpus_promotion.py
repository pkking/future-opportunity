"""Fail-closed Q2 research promotion approval and source-scope controls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/stage_cash_2025q2_research_corpus.py"
spec = importlib.util.spec_from_file_location("cash_q2_research_corpus", SCRIPT)
assert spec and spec.loader
promo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promo)

AUDIT = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-cross-run-audit-v1.json"
SELECTION = ROOT / "docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json"
INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"
POLICY = ROOT / "tests/e2e/historical-target-policy.json"
AUTH = ROOT / "docs/historical-acquisition-plans/cash-2025q2-research-corpus-promotion-authorization-v1.json"
WF = ROOT / ".github/workflows/stage-cash-2025q2-research-corpus.yml"


def baseline():
    return [json.loads(p.read_text()) for p in (AUDIT, SELECTION, INDEX, POLICY)]


def test_approved_campaign_requires_full_12_dates_and_unmodified_baselines():
    audit, selection, index, policy = baseline()
    result = promo.approved_campaign(audit, selection, index, policy)
    assert len(result) == 12
    assert [c["entry_market_date"] for c in result] == selection["selected_market_dates"]
    assert [c["entry_market_date"] for c in result if c["qualification"] == "unqualified"] == list(promo.REJECTED)
    assert sum(c["qualification"] == "qualified" for c in result) == 9
    assert [c["source_run_id"] for c in result] == [
        promo.REPAIR if c["entry_market_date"] == "2025-04-09" else promo.ORIGINAL for c in result
    ]


@pytest.mark.parametrize("tamper", [
    lambda a,s,i,p: a["cases"].pop(2),
    lambda a,s,i,p: a["cases"][1].update({"source_run_id": promo.ORIGINAL}),
    lambda a,s,i,p: a["cases"][9].update({"qualification": "qualified"}),
    lambda a,s,i,p: a["cases"][9].update({"realized_paper_net_return": "0"}),
    lambda a,s,i,p: a["cases"][9].update({"qualification_reasons": []}),
    lambda a,s,i,p: s["selected_market_dates"].pop(),
    lambda a,s,i,p: p["stage2_decision_quality"].update({"economics_gate": "enabled"}),
    lambda a,s,i,p: p["reference_targets"].update({"usage": "acceptance_gate"}),
    lambda a,s,i,p: i["entries"].append(copy.deepcopy(i["entries"][0])),
])
def test_fail_closed_on_date_source_negative_outcome_policy_or_corpus_tamper(tamper):
    args = baseline()
    tamper(*args)
    with pytest.raises((ValueError, KeyError, TypeError)):
        promo.approved_campaign(*args)


def test_only_failed_original_overall_run_may_supply_successful_jobs(monkeypatch):
    audit, selection, index, policy = baseline()
    cases = promo.approved_campaign(audit, selection, index, policy)

    def fixture_api(path: str, *, repo: str):
        assert repo == "pkking/future-opportunity"
        run = promo.ORIGINAL if str(promo.ORIGINAL) in path else promo.REPAIR
        if path.endswith(f"/{run}"):
            return {"event": "workflow_dispatch", "status": "completed",
                    "conclusion": promo.HEADS[run][1],
                    "head_sha": promo.HEADS[run][0], "head_branch": "main"}
        selected = [c for c in cases if c["source_run_id"] == run]
        if path.endswith("/jobs?per_page=100"):
            jobs = [{"name": f"Cash {c['entry_market_date']}T00:15:00+00:00 BTC-USDT-250627 / prepare",
                     "status": "completed", "conclusion": "success"} for c in selected]
            return {"total_count": len(jobs), "jobs": jobs}
        if path.endswith("/artifacts?per_page=100"):
            artifacts = [dict(id=ref["id"], name=ref["name"], digest=ref["zip_sha256"], expired=False)
                         for c in selected for ref in c["artifacts"].values()]
            return {"total_count": len(artifacts), "artifacts": artifacts}
        raise AssertionError(f"unexpected API {path}")

    monkeypatch.setattr(promo, "github_json", fixture_api)
    promo.verify_actions_sources(cases, repo="pkking/future-opportunity")


def test_original_run_cannot_be_waived_if_its_case_job_failed(monkeypatch):
    audit, selection, index, policy = baseline()
    cases = promo.approved_campaign(audit, selection, index, policy)

    def fixture_api(path: str, *, repo: str):
        run = promo.ORIGINAL if str(promo.ORIGINAL) in path else promo.REPAIR
        if path.endswith(f"/{run}"):
            return {"event": "workflow_dispatch", "status": "completed",
                    "conclusion": promo.HEADS[run][1],
                    "head_sha": promo.HEADS[run][0], "head_branch": "main"}
        selected = [c for c in cases if c["source_run_id"] == run]
        if path.endswith("/jobs?per_page=100"):
            jobs = [{"name": f"Cash {c['entry_market_date']}T00:15:00+00:00 BTC-USDT-250627 / prepare",
                     "status": "completed", "conclusion": "failure"} for c in selected]
            return {"total_count": len(jobs), "jobs": jobs}
        if path.endswith("/artifacts?per_page=100"):
            artifacts = [dict(id=ref["id"], name=ref["name"], digest=ref["zip_sha256"], expired=False)
                         for c in selected for ref in c["artifacts"].values()]
            return {"total_count": len(artifacts), "artifacts": artifacts}
        raise AssertionError("unexpected API call")

    monkeypatch.setattr(promo, "github_json", fixture_api)
    with pytest.raises(ValueError, match="preparation job did not succeed"):
        promo.verify_actions_sources(cases, repo="pkking/future-opportunity")


def test_one_time_trigger_scope_and_authorization_exclude_trading():
    auth = json.loads(AUTH.read_text())
    workflow = WF.read_text()
    assert auth["status"] == "approved_for_research_only"
    assert auth["approved_date_count"] == 12
    assert auth["promotion_requires_reviewed_pr"] is True
    assert auth["corpus_auto_merge"] is False
    assert auth["live_trading_enabled"] is False
    assert auth["stage2_economics_gate_activated"] is False
    assert "push:" in workflow and "branches: [main]" in workflow
    assert "cash-2025q2-research-corpus-promotion-authorization-v1.json" in workflow
    assert "workflow_dispatch:" not in workflow
    assert "schedule:" not in workflow
    assert "git add tests/fixtures/historical" in workflow
    assert "gh pr create" in workflow
    assert "gh pr merge" not in workflow
    assert "gh workflow run" not in workflow
    assert "promote-planned-historical" not in workflow
