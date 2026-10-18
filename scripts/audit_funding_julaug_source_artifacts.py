"""Replay the three approved July/August Funding raw-source ZIPs offline.

Never fetch new market data, alter sampling, or approve corpus promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from future_opportunity.backtest.funding_raw_feature_lineage import (
    reconstruct_funding_regime_features,
)
from future_opportunity.backtest.funding_regime_research import (
    plan_funding_regime_research,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/research/funding-2026-julaug-source-run-audit-v1.json"
FILES = {
    "coverage-summary.json", "planner-input.json", "raw-api-capture.json",
    "reconstructed-features.json", "research-selection.json",
}
REGIMES = (
    "negative_low_volatility", "negative_high_volatility",
    "nonnegative_low_volatility", "nonnegative_high_volatility",
)


def audit_zip(path: Path, expected: dict) -> dict:
    """Fail closed on ZIP identity, original source, or replay mismatch."""
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected["zip_sha256"]:
        raise ValueError("funding source ZIP SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        if set(archive.namelist()) != FILES or len(archive.namelist()) != 5:
            raise ValueError("Funding research ZIP members mismatch")
        if any(member.file_size > 2_000_000 for member in archive.infolist()):
            raise ValueError("Funding research ZIP member exceeds bounded size")
        reports = {name: json.loads(archive.read(name)) for name in FILES}
    raw = reports["raw-api-capture.json"]
    if (raw.get("start_date"), raw.get("end_date"), raw.get("seed")) != (
        expected["first"], expected["last"], expected["seed"]
    ):
        raise ValueError("raw source dates/seed diverge from frozen registration")
    reconstructed = reconstruct_funding_regime_features(raw)
    planner = plan_funding_regime_research(reconstructed["planner_input"])
    if (reports["reconstructed-features.json"] != reconstructed
        or reports["planner-input.json"] != reconstructed["planner_input"]
        or reports["research-selection.json"] != planner):
        raise ValueError("raw source reconstruction or selection replay mismatch")
    summary = reports["coverage-summary.json"]
    if (summary.get("window_id") != expected["id"]
        or summary.get("source_sha256") != reconstructed["source_sha256"]
        or reconstructed["source_sha256"] != expected["source_sha256"]
        or summary.get("regimes") != planner["regimes"]
        or summary.get("missing_days") != []):
        raise ValueError("Funding coverage/source digest mismatch")
    if len(reconstructed["planner_input"]["observations"]) != expected["raw_feature_days"]:
        raise ValueError("Funding reconstructed row count mismatch")
    if raw["pinned_market_dates"] != expected["pinned_market_dates"]:
        raise ValueError("Funding pinned sample exclusion mismatch")
    if planner["selected_dates"] != expected["selected_dates"]:
        raise ValueError("Funding source-blind selected population mismatch")
    obs = reconstructed["planner_input"]["observations"]
    counts = {regime: 0 for regime in REGIMES}
    from decimal import Decimal
    for row in obs:
        label = ("negative" if Decimal(row["lagged_funding_rate"]) < 0
                 else "nonnegative") + "_" + (
                     "high_volatility" if Decimal(row["trailing_spot_volatility_bps"]) >= 100
                     else "low_volatility"
                 )
        counts[label] += 1
    if counts != expected["regimes"]:
        raise ValueError("Funding market regime count mismatch")
    if (summary.get("acquisition_approved") is not False
        or summary.get("promotion_approved") is not False
        or summary.get("point_in_time_publication_verified") is not False):
        raise ValueError("Funding research evidence cannot authorize promotion or as-of time")
    return {"window": expected["id"], "source_sha256": expected["source_sha256"],
            "observed": len(obs), "regimes": counts,
            "eligible_new": len(obs) - len(raw["pinned_market_dates"])}


def audit_run(files: dict[str, Path], manifest: dict) -> dict:
    windows = manifest["windows"]
    if set(files) != {w["id"] for w in windows}:
        raise ValueError("Funding source audit requires exactly three frozen windows")
    reports = [audit_zip(files[w["id"]], w) for w in windows]
    total = {name: sum(item["regimes"][name] for item in reports) for name in REGIMES}
    if (total != manifest["regime_population_all_observed"]
        or sum(item["observed"] for item in reports) != manifest["raw_feature_days"]
        or sum(item["eligible_new"] for item in reports) != manifest["new_eligible_days"]):
        raise ValueError("Funding research population totals mismatch")
    return {"status": "replayed_research_only", "run_id": manifest["run_id"],
            "windows": reports, "regimes": total,
            "point_in_time_publication_verified": False,
            "promotion_approved": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jul-27-aug-02", type=Path, required=True)
    parser.add_argument("--aug-10-16", type=Path, required=True)
    parser.add_argument("--aug-24-30", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(AUDIT.read_text())
    files = {
        "2026-07-27-to-08-02": args.jul_27_aug_02,
        "2026-08-10-to-16": args.aug_10_16,
        "2026-08-24-to-30": args.aug_24_30,
    }
    print(json.dumps(audit_run(files, manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
