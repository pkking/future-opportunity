from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/probe_cash_independent_l2.py"
WORKFLOW = ROOT / ".github/workflows/probe-cash-independent-l2.yml"
spec = importlib.util.spec_from_file_location("cash_independent_l2_probe", SCRIPT)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

ENTRY = "2025-06-12T00:15:00+00:00"
EXIT = "2025-06-26T00:15:00+00:00"


def books_for(tmp_path: Path):
    books = {}
    for name in ("entry_spot", "entry_future", "exit_spot", "exit_future"):
        data = (json.dumps({"source": name}) + "\n").encode()
        (tmp_path / (name + ".jsonl")).write_bytes(data)
        books[name] = {
            "path": name + ".jsonl",
            "sample_at": ENTRY if name.startswith("entry_") else EXIT,
            "age_ms": 100,
            "sha256": hashlib.sha256(data).hexdigest(),
            "best_bid": "100",
            "best_ask": "101",
        }
    return books


def test_four_books_verify_exact_hash_timestamp_and_positive_spread(tmp_path):
    probe.verify_four_books(tmp_path, books_for(tmp_path), entry_at=ENTRY, exit_at=EXIT)


@pytest.mark.parametrize("change,pattern", [
    (lambda books: books.pop("exit_future"), "four"),
    (lambda books: books["entry_spot"].update({"sample_at": EXIT}), "timestamp"),
    (lambda books: books["entry_spot"].update({"age_ms": 5001}), "staleness"),
    (lambda books: books["entry_spot"].update({"best_ask": "90"}), "invalid"),
    (lambda books: books["entry_spot"].update({"sha256": "f"*64}), "SHA-256"),
    (lambda books: books["entry_spot"].update({"path": "../bad.jsonl"}), "basename"),
])
def test_bad_or_missing_book_never_becomes_source_verified(tmp_path, change, pattern):
    books = books_for(tmp_path)
    change(books)
    with pytest.raises(ValueError, match=pattern):
        probe.verify_four_books(tmp_path, books, entry_at=ENTRY, exit_at=EXIT)


def test_research_workflow_cannot_publish_promotable_fixture():
    workflow = WORKFLOW.read_text()
    script = SCRIPT.read_text()
    assert "contents: read" in workflow
    assert "workflow_dispatch:" in workflow
    assert "--candidate-id 2025q2" in workflow
    assert "run_cash_historical_backtest.py" not in workflow
    assert "finalize_cash_compact_fixture.py" not in workflow
    assert "git push" not in workflow
    assert "CASH_SELECTION_PROVENANCE_JSON" in script
    assert 'os.environ["CASH_SELECTION_PROVENANCE_JSON"] = ""' in script
    assert '"historical_sampling_provenance": None' in script
    assert '"economics_evaluated": False' in script
    assert '"acquisition_approved": False' in script
