from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
POLICY = ROOT / "tests/e2e/historical-target-policy.json"
SCRIPT = ROOT / "scripts/report_pending_corpus_prs.py"


def _entry(strategy: str, day: str) -> dict[str, str]:
    dataset_id = f"{strategy}-{day}"
    return {
        "dataset_id": dataset_id,
        "strategy": strategy,
        "entry_market_date": day,
        "fixture_path": dataset_id,
    }


def test_pending_corpus_cli_emits_index_only_union_evidence(
    tmp_path: Path,
) -> None:
    base_entries = [
        _entry("funding-carry", "2026-09-01"),
        _entry("funding-carry", "2026-09-02"),
        _entry("cash-and-carry", "2026-06-01"),
        _entry("cash-and-carry", "2026-06-02"),
    ]
    baseline = tmp_path / "main-index.json"
    baseline.write_text(
        json.dumps({"schema_version": 1, "entries": base_entries})
    )
    proposals = tmp_path / "proposals"
    proposals.mkdir()
    for number, additions, sha in (
        (
            3,
            [
                _entry("funding-carry", "2026-09-03"),
                _entry("cash-and-carry", "2026-06-03"),
            ],
            "a" * 40,
        ),
        (
            4,
            [
                _entry("funding-carry", "2026-01-01"),
                _entry("funding-carry", "2026-01-08"),
                _entry("funding-carry", "2026-01-13"),
                _entry("funding-carry", "2026-01-22"),
                _entry("funding-carry", "2026-01-29"),
                _entry("cash-and-carry", "2026-06-04"),
                _entry("cash-and-carry", "2026-06-08"),
            ],
            "b" * 40,
        ),
    ):
        (proposals / f"pr-{number}.json").write_text(
            json.dumps(
                {
                    "pr_number": number,
                    "head_sha": sha,
                    "index": {
                        "schema_version": 1,
                        "entries": base_entries + additions,
                    },
                }
            )
        )

    output = tmp_path / "review" / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--base-index",
            str(baseline),
            "--policy",
            str(POLICY),
            "--proposals-dir",
            str(proposals),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    evidence = json.loads(output.read_text())
    assert evidence["evidence_scope"] == "index_identity_only"
    assert evidence["pinned_counts"] == {
        "funding-carry": 2,
        "cash-and-carry": 2,
    }
    assert evidence["projected_union_counts_if_all_approved"] == {
        "funding-carry": 8,
        "cash-and-carry": 5,
    }
    assert [item["pr_number"] for item in evidence["proposals"]] == [3, 4]
    assert evidence["unmerged_proposals_count_toward_pinned"] is False
    assert evidence["minimum_ready_now"] is False


def test_pending_corpus_cli_rejects_malformed_proposal_envelope(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "index.json"
    baseline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [_entry("funding-carry", "2026-09-01")],
            }
        )
    )
    proposals = tmp_path / "proposals"
    proposals.mkdir()
    (proposals / "pr-3.json").write_text(json.dumps({"pr_number": 3}))
    output = tmp_path / "out.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--base-index",
            str(baseline),
            "--policy",
            str(POLICY),
            "--proposals-dir",
            str(proposals),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid pending PR evidence envelope" in result.stderr
    assert not output.exists()
