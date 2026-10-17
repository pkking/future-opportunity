from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from probe_cash_independent_expiries import (
    REGISTRY,
    pinned_cash_futures,
    validated_candidates,
)


def verify_four_books(
    output: Path, books: dict[str, dict[str, Any]],
    *, entry_at: str, exit_at: str,
) -> None:
    if set(books) != {"entry_spot", "entry_future", "exit_spot", "exit_future"}:
        raise ValueError("all four Cash SPOT/FUTURES entry/exit books are required")
    for label, record in books.items():
        expected_at = entry_at if label.startswith("entry_") else exit_at
        if record["sample_at"] != expected_at:
            raise ValueError("Cash book sample must match frozen exact UTC timestamp")
        if not isinstance(record["age_ms"], int) or not 0 <= record["age_ms"] <= 5000:
            raise ValueError("Cash book staleness exceeds 5000ms")
        bid, ask = Decimal(record["best_bid"]), Decimal(record["best_ask"])
        if not bid.is_finite() or not ask.is_finite() or bid <= 0 or ask <= bid:
            raise ValueError("Cash book best bid/ask invalid or crossed")
        name = record["path"]
        if name != label + ".jsonl":
            raise ValueError("Cash canonical book basename mismatch")
        path = output / name
        contents = path.read_bytes()
        if not contents or hashlib.sha256(contents).hexdigest() != record["sha256"]:
            raise ValueError("Cash canonical book SHA-256 mismatch")
        lines = contents.splitlines()
        if len(lines) != 1:
            raise ValueError("Cash research sample requires exactly one canonical L2 observation")
        json.loads(lines[0])


def run_source_only(candidate: dict[str, str], output: Path) -> dict[str, Any]:
    entry_at = candidate["entry_market_date"] + "T00:15:00+00:00"
    exit_at = candidate["exit_market_date"] + "T00:15:00+00:00"
    expiry_at = datetime.fromisoformat(candidate["expiry_at"]).astimezone(UTC)
    assert datetime.fromisoformat(entry_at) < datetime.fromisoformat(exit_at) < expiry_at
    output.mkdir(parents=True, exist_ok=True)

    # Import after configuring the original strictly validated source reader.
    # Invoke prepare_component only: never call its main(), compact generator,
    # history replay, return attribution or any corpus promotion.
    os.environ["CASH_ENTRY_AT"] = entry_at
    os.environ["CASH_EXIT_AT"] = exit_at
    os.environ["CASH_EXPIRY_AT"] = candidate["expiry_at"]
    os.environ["CASH_FUTURE_ID"] = candidate["future_id"]
    os.environ["CASH_HISTORICAL_FIXTURE_DIR"] = str(output)
    os.environ["CASH_HISTORY_MAX_RAW_MB"] = "600"
    os.environ["CASH_HISTORY_MAX_STALENESS_MS"] = "5000"
    os.environ["CASH_SELECTION_PROVENANCE_JSON"] = ""
    import prepare_okx_cash_and_carry_fixture as original_reader

    if (
        original_reader.ENTRY_AT.isoformat() != entry_at
        or original_reader.EXIT_AT.isoformat() != exit_at
        or original_reader.EXPIRY.isoformat() != candidate["expiry_at"]
        or original_reader.RAW_FUTURE_ID != candidate["future_id"]
        or original_reader.RAW_SELECTION_PROVENANCE
    ):
        raise ValueError("source reader received unexpected frozen selection or timestamps")

    books: dict[str, dict[str, Any]] = {}
    sources: dict[str, dict[str, Any]] = {}
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        with tempfile.TemporaryDirectory() as tmp:
            for name, at, kind in (
                ("entry_spot", original_reader.ENTRY_AT, "SPOT"),
                ("entry_future", original_reader.ENTRY_AT, "FUTURES"),
                ("exit_spot", original_reader.EXIT_AT, "SPOT"),
                ("exit_future", original_reader.EXIT_AT, "FUTURES"),
            ):
                normalized, origin = original_reader.prepare_component(
                    client, Path(tmp), name=name, sample_at=at, instrument_type=kind
                )
                books[name] = normalized
                sources[name] = origin
    verify_four_books(output, books, entry_at=entry_at, exit_at=exit_at)
    return {
        "schema_version": 1,
        "evidence_type": "cash_independent_expiry_full_l2_source_research",
        "research_only": True,
        "candidate_id": candidate["id"],
        "future_id": candidate["future_id"],
        "entry_at": entry_at,
        "exit_at": exit_at,
        "expiry_at": candidate["expiry_at"],
        "status": "four_canonical_books_verified",
        "sampled_book_count": len(books),
        "max_sampled_book_staleness_ms": max(x["age_ms"] for x in books.values()),
        "normalized": books,
        "sources": sources,
        "historical_sampling_provenance": None,
        "economics_evaluated": False,
        "complete_acquisition_provenance": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "note": "No historical selection provenance, future-candidate population or outcome-blind case selection frozen; not a promotable fixture.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text())
    candidates = validated_candidates(registry, pinned_cash_futures())
    selected = [x for x in candidates if x["id"] == args.candidate_id]
    if len(selected) != 1:
        parser.error("candidate must be an exact registered unpinned expiry")
    try:
        result = run_source_only(selected[0], args.output_dir)
        (args.output_dir / "research-report.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
        print(json.dumps({
            "status": result["status"],
            "candidate_id": result["candidate_id"],
            "max_staleness_ms": result["max_sampled_book_staleness_ms"],
            "acquisition_approved": False,
            "promotion_approved": False,
        }))
    except Exception as error:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "source-error.json").write_text(
            json.dumps({
                "schema_version": 1,
                "research_only": True,
                "candidate_id": args.candidate_id,
                "status": "source_incomplete",
                "error_type": type(error).__name__,
                "reason": str(error)[:350],
                "acquisition_approved": False,
                "promotion_approved": False,
            }, sort_keys=True, indent=2) + "\n"
        )
        raise


if __name__ == "__main__":
    main()
