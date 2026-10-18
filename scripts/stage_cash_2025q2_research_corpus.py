"""One-shot, allowlisted Q2 Cash historical *research* corpus promotion.

Unlike generic campaign promotion, original source run 39079100154 has an
overall FAILURE because *only* April 9 overflowed the old archive cap.
Eleven other successful individual cases remain independently verified.
This script validates exact run/head/job/artifact identities before staging
from those eleven + the successful, separately approved April 9 repair.

Run only in the reviewed GitHub Actions approval workflow, never trading.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

from future_opportunity.backtest.campaign import (
    ResolvedHistoricalCampaignItem,
    promote_historical_campaign,
)
from future_opportunity.backtest.promotion import inspect_historical_compact_fixture

ORIGINAL = 39079100154
REPAIR = 39091438598
HEADS = {
    ORIGINAL: ("3b2c9660bf0b22827a2c35e5d80b9619f481281a", "failure"),
    REPAIR: ("6600b330fd8bb78f3385b89227b7c06eb0749c72", "success"),
}
REJECTED = ("2025-06-07", "2025-06-14", "2025-06-22")
ARCHIVE_COMPONENTS = ("entry_spot", "entry_future", "exit_spot", "exit_future")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def approved_campaign(audit: dict, frozen: dict, index: dict, policy: dict) -> list[dict]:
    """Preflight without network or mutation; returns immutable approved case order."""
    require(audit.get("evidence_type") == "cash_2025q2_cross_run_complete_research_audit_index", "unexpected research audit")
    require(audit["selection_evidence_sha256"] == frozen["selection_evidence_sha256"] == "9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37", "selection SHA drift")
    cases = audit["cases"]
    days = frozen["selected_market_dates"]
    require(len(days) == len(cases) == 12, "requires exactly twelve preregistered dates")
    require([case["entry_market_date"] for case in cases] == days, "date replacement or order drift")
    require(audit["contract"] == frozen["future_id"] == "BTC-USDT-250627", "contract drift")
    require(audit["exit_at"] == frozen["exit_at"] == "2025-06-26T00:15:00+00:00", "exit drift")
    require(audit["expiry_at"] == frozen["expiry_at"] == "2025-06-27T08:00:00+00:00", "expiry drift")
    require(audit["results"]["complete_case_count"] == 12 and audit["results"]["prepared_compact_actuals_artifact_count"] == 36, "not fully audited")
    require({r["run_id"] for r in audit["acquisition_runs"]} == set(HEADS), "unapproved research source run")
    require(policy["mode"] == "provenance_and_semantics", "policy mode change")
    require(policy["reference_targets"]["usage"] == "reporting_only", "reference targets cannot gate returns")
    require(policy["stage2_decision_quality"]["economics_gate"] == "disabled", "economics gate must remain disabled")
    require(policy["transition_to_distribution_mode"]["activation_requires_human_approval"] is True, "missing human readiness gate")
    require(audit["policy_boundaries"]["corpus_promotion_approved"] is False, "research source metadata must not self-authorize promotion")
    require(audit["policy_boundaries"]["baseline_cash_cases"] == 54 and audit["policy_boundaries"]["baseline_funding_cases"] == 32, "baseline drift")
    entries = index["entries"]
    require(len(entries) == 86, "pre-promotion index count drift")
    require(sum(e["strategy"] == "cash-and-carry" for e in entries) == 54, "cash baseline drift")
    require(sum(e["strategy"] == "funding-carry" for e in entries) == 32, "funding baseline drift")
    existing_dates = {e["entry_market_date"] for e in entries if e["strategy"] == "cash-and-carry"}
    require(not existing_dates.intersection(days), "corpus strategy/date collision")
    require([c["entry_market_date"] for c in cases if c["qualification"] == "unqualified"] == list(REJECTED), "negative observations changed")
    require(sum(c["qualification"] == "qualified" for c in cases) == 9, "qualified count drift")
    for c in cases:
        day = c["entry_market_date"]
        expected_run = REPAIR if day == "2025-04-09" else ORIGINAL
        require(c["source_run_id"] == expected_run, f"{day} must retain original/repaired run provenance")
        require(set(c["artifacts"]) == {"prepared", "compact", "actuals"}, f"{day} incomplete")
        for kind, artifact in c["artifacts"].items():
            require(isinstance(artifact["id"], int) and re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["zip_sha256"]) is not None, f"{day} {kind} invalid artifact")
            expected_name = "okx-btc-cash-and-carry-" + ("" if kind == "prepared" else kind + "-") + day + "-BTC-USDT-250627-" + str(expected_run)
            require(artifact["name"] == expected_name, f"{day} {kind} artifact identity drift")
        if day in REJECTED:
            require(c["qualification_reasons"] == ["expected_net_return_not_positive"], f"{day} negative observation lost")
            require(c["realized_paper_net_return"] is None and c["return_complete"] is False, f"{day} zero/synthetic realization")
        else:
            require(c["qualification_reasons"] == [] and c["return_complete"] is True, f"{day} qualified observation changed")
            require(Decimal(c["realized_paper_net_return"]) > 0, f"{day} invalid paper realized return")
    return cases


def github_json(path: str, *, repo: str) -> dict:
    # Exact, read-only GitHub API calls only. No authenticated exchange calls.
    raw = subprocess.run(["gh", "api", "repos/" + repo + "/" + path],
                         check=True, capture_output=True, text=True).stdout
    value = json.loads(raw)
    require(isinstance(value, dict), "GitHub API returned non-object")
    return value


def verify_actions_sources(cases: list[dict], *, repo: str) -> None:
    for run_id, (head, conclusion) in HEADS.items():
        run = github_json(f"actions/runs/{run_id}", repo=repo)
        require(run["event"] == "workflow_dispatch", f"{run_id}: unexpected event")
        require(run["status"] == "completed" and run["conclusion"] == conclusion, f"{run_id}: unexpected conclusion")
        require(run["head_sha"] == head, f"{run_id}: source head SHA changed")
        require(run["head_branch"] == "main", f"{run_id}: unexpected branch")
        jobs_data = github_json(f"actions/runs/{run_id}/jobs?per_page=100", repo=repo)
        jobs = jobs_data["jobs"]
        require(jobs_data["total_count"] == len(jobs), f"{run_id}: job pages incomplete")
        artifacts_data = github_json(f"actions/runs/{run_id}/artifacts?per_page=100", repo=repo)
        artifacts = artifacts_data["artifacts"]
        require(artifacts_data["total_count"] == len(artifacts), f"{run_id}: artifact pages incomplete")
        artifacts_by_id = {a["id"]: a for a in artifacts}
        for c in cases:
            if c["source_run_id"] != run_id:
                continue
            day = c["entry_market_date"]
            job_suffix = f"Cash {day}T00:15:00+00:00 BTC-USDT-250627 / prepare"
            matching_jobs = [j for j in jobs if j["name"].endswith(job_suffix)]
            require(len(matching_jobs) == 1 and matching_jobs[0]["status"] == "completed"
                    and matching_jobs[0]["conclusion"] == "success", f"{day}: preparation job did not succeed")
            for kind, ref in c["artifacts"].items():
                artifact = artifacts_by_id.get(ref["id"])
                require(artifact is not None, f"{day}: {kind} artifact not found")
                require(artifact["name"] == ref["name"], f"{day}: {kind} artifact name drift")
                require(artifact["digest"] == ref["zip_sha256"], f"{day}: {kind} artifact digest drift")
                require(artifact["expired"] is False, f"{day}: {kind} artifact expired")


def verify_downloaded(c: dict, root: Path, actuals_root: Path, frozen: dict) -> ResolvedHistoricalCampaignItem:
    manifest = json.loads((root / "manifest.json").read_text())
    day, run = c["entry_market_date"], c["source_run_id"]
    require(manifest["pinning_status"] == "commit_ready", f"{day} unpinned")
    require(manifest["entry_market_date"] == day and manifest["strategy"] == "cash-and-carry", f"{day} manifest drift")
    require(manifest["sample_times"] == {"entry": day + "T00:15:00+00:00", "exit": frozen["exit_at"]}, f"{day} sample time drift")
    require(manifest["instrument"]["future_instrument_id"] == "BTC-USDT-250627", f"{day} future identity drift")
    require(manifest["instrument"]["expiry"] == frozen["expiry_at"], f"{day} expiry drift")
    sampling = manifest["selection_provenance"]["sampling"]
    require(sampling["selected_market_dates"] == frozen["selected_market_dates"], f"{day} selected dates drift")
    require(sampling["evidence_sha256"] == frozen["selection_evidence_sha256"], f"{day} selection hash drift")
    require(manifest["selection_provenance"]["source"]["artifact_id"] == "12106828444", f"{day} source control drift")
    parent = c["artifacts"]["prepared"]
    require(manifest["derived_from_artifact"] == {
        "workflow_run": str(run),
        "artifact_id": str(parent["id"]),
        "artifact_zip_sha256": parent["zip_sha256"].removeprefix("sha256:"),
    }, f"{day} parent ZIP/source mismatch")
    require(set(manifest["normalized"]) == set(ARCHIVE_COMPONENTS), f"{day} missing books")
    for key in ARCHIVE_COMPONENTS:
        comp = manifest["normalized"][key]
        file = (root / comp["path"])
        require(file.is_file() and comp["path"] == key + ".jsonl", f"{day} {key} path mismatch")
        # Source selection and compact canonical books get cryptographically verified by
        # inspect_historical_compact_fixture() below.
        require(comp["age_ms"] <= 5000, f"{day} {key} staleness excessive")
        source = manifest["sources"][key]["file"]
        expected_date = day if key.startswith("entry_") else "2025-06-26"
        expected_member = ("BTC-USDT-250627" if key.endswith("future") else "BTC-USDT") + "-L2orderbook-400lv-" + expected_date + ".data"
        require(source["archive_member"] == expected_member, f"{day} {key} source member drift")
        require(re.fullmatch("[0-9a-f]{64}", source["raw_sha256"]) is not None, f"{day} {key} source sha invalid")
    entry = inspect_historical_compact_fixture(
        root, source_workflow_run=str(run),
        expected_parent_artifact_id=str(parent["id"]),
        expected_parent_artifact_sha256=parent["zip_sha256"])
    require(entry.entry_market_date == day, f"{day} inspected date drift")
    report = json.loads((actuals_root / "report.json").read_text())
    actual = report["backtest"]["cases"]
    require(len(actual) == 1, f"{day} Actuals case count drift")
    actual = actual[0]
    require(actual["observed_at"] == day + "T00:15:00+00:00", f"{day} Actuals date drift")
    require(actual["expiry"] == frozen["expiry_at"] and actual["exit_at"] == frozen["exit_at"], f"{day} Actuals contract/exit drift")
    assert isinstance(c["return_complete"], bool)
    if c["qualification"] == "unqualified":
        require(actual["qualified"] is False and actual["qualification_reasons"] == ["expected_net_return_not_positive"], f"{day} rejected assessment changed")
        require(actual["realized_net_return"] is None and not actual["return_complete"], f"{day} rejected realization manufactured")
    else:
        require(actual["qualified"] is True and actual["qualification_reasons"] == [], f"{day} expected qualified case")
        require(actual["return_complete"] is True, f"{day} realized return missing")
        require(Decimal(actual["realized_net_return"]) == Decimal(c["realized_paper_net_return"]), f"{day} paper return altered")
    return ResolvedHistoricalCampaignItem(
        source_root=root, source_workflow_run=str(run),
        compact_artifact_name=c["artifacts"]["compact"]["name"],
        parent_artifact_id=str(parent["id"]),
        parent_artifact_sha256=parent["zip_sha256"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, default=Path("docs/historical-acquisition-plans/cash-2025q2-12day-cross-run-audit-v1.json"))
    parser.add_argument("--selection", type=Path, default=Path("docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json"))
    parser.add_argument("--index", type=Path, default=Path("tests/fixtures/historical/corpus-index.json"))
    parser.add_argument("--policy", type=Path, default=Path("tests/e2e/historical-target-policy.json"))
    parser.add_argument("--work", type=Path, default=Path("artifacts/cash-2025q2-research-promotion"))
    parser.add_argument("--repo", default="pkking/future-opportunity")
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text())
    frozen = json.loads(args.selection.read_text())
    original_index = json.loads(args.index.read_text())
    policy = json.loads(args.policy.read_text())
    cases = approved_campaign(audit, frozen, original_index, policy)
    verify_actions_sources(cases, repo=args.repo)

    args.work.mkdir(parents=True, exist_ok=True)
    resolved = []
    for c in cases:
        day, run = c["entry_market_date"], c["source_run_id"]
        source = args.work / "downloaded" / day
        actuals = args.work / "actuals" / day
        source.mkdir(parents=True, exist_ok=True)
        actuals.mkdir(parents=True, exist_ok=True)
        for kind, destination in (("compact", source), ("actuals", actuals)):
            subprocess.run(["gh", "run", "download", str(run),
                            "--repo", args.repo, "--name", c["artifacts"][kind]["name"],
                            "--dir", str(destination)], check=True)
        resolved.append(verify_downloaded(c, source, actuals, frozen))

    # Existing campaign promotion is transactional and validates each compact
    # manifest, normalized checksum and entire post-update corpus.
    outcome = promote_historical_campaign(
        tuple(resolved), fixture_root=args.index.parent,
        index_path=args.index)
    require(outcome.status == "staged", "twelve approved Q2 cases were not staged")
    updated = json.loads(args.index.read_text())["entries"]
    require(len(updated) == 98, "post-promotion corpus must have 98 exact entries")
    require(sum(e["strategy"] == "cash-and-carry" for e in updated) == 66, "unexpected Cash corpus count")
    require(sum(e["strategy"] == "funding-carry" for e in updated) == 32, "Funding corpus unexpectedly changed")
    audit_output = {
        "schema_version": 1,
        "evidence_type": "cash_2025q2_12case_research_promotion",
        "status": "staged_for_pr_review_only",
        "case_count": 12,
        "qualified_count": 9,
        "rejected_count": 3,
        "original_corpus_count": 86,
        "post_promotion_corpus_count": 98,
        "original_source_run_failed_but_valid_jobs_audited": ORIGINAL,
        "single_case_repair_source_run_succeeded": REPAIR,
        "selection_evidence_sha256": frozen["selection_evidence_sha256"],
        "corpus_promotion_requires_reviewed_pr": True,
        "stage2_economics_gate_enabled": False,
        "live_trading_enabled": False,
    }
    (args.work / "promotion-control.json").write_text(
        json.dumps(audit_output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit_output, sort_keys=True))


if __name__ == "__main__":
    main()
