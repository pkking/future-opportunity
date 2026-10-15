"""Bounded evidence extraction from an already-downloaded OKX L2 archive.

Diagnostics only: never repair, drop, or interpret an order-book level.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
import tarfile
from pathlib import Path
from typing import Any


_MAX_FIRST_LINE_BYTES = 128 * 1024


def inspect_first_l2_record(
    archive_path: Path,
    *,
    member_name: str,
    expected_instrument_id: str,
    component: str,
    sample_at: str,
    raw_sha256: str,
    downloaded_bytes: int,
) -> dict[str, Any]:
    """Inspect only first nonblank source row; omit temporary/signed download URLs."""
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        member = archive.getmember(member_name)
        if not member.isfile() or not member.name.endswith(".data"):
            raise ValueError("diagnostic archive member is not a .data file")
        source = archive.extractfile(member)
        if source is None:
            raise ValueError("unable to inspect L2 diagnostic archive member")
        with source:
            source_line = 0
            while True:
                raw = source.readline(_MAX_FIRST_LINE_BYTES + 1)
                source_line += 1
                if len(raw) > _MAX_FIRST_LINE_BYTES:
                    raise ValueError("L2 first record exceeds diagnostic size cap")
                if not raw:
                    raise ValueError("L2 archive contains no nonblank first record")
                if raw.strip():
                    break
    line_sha = hashlib.sha256(raw).hexdigest()
    # utf-8-sig matches the normalizer; retain only a small structural sample.
    event = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(event, dict):
        raise ValueError("L2 first diagnostic record is not an object")

    view: dict[str, Any] = {
        "schema_version": 1,
        "evidence_type": "okx_l2_first_record_diagnostic",
        "component": component,
        "sample_at": sample_at,
        "expected_instrument_id": expected_instrument_id,
        "archive_filename": archive_path.name,
        "archive_member": member_name,
        "raw_sha256": raw_sha256,
        "downloaded_bytes": downloaded_bytes,
        "source_line": source_line,
        "first_line_sha256": line_sha,
        "action": event.get("action"),
        "actual_instrument_id": event.get("instId"),
        "raw_timestamp": event.get("ts"),
        "levels": {},
        "diagnostic_only": True,
        "normalization_succeeded": False,
        "source_url_recorded": False,
    }

    for side in ("bids", "asks"):
        levels = event.get(side)
        if not isinstance(levels, list):
            view["levels"][side] = {"shape": type(levels).__name__}
            continue
        anomaly_counts = {
            "nonpositive_price": 0,
            "nonfinite_price": 0,
            "invalid_price": 0,
            "invalid_level_shape": 0,
        }
        first_anomalies: list[dict[str, Any]] = []
        # Analyze all prices, but publish at most eight bounded examples
        # per side. This is evidence, not replay or source correction.
        for index, level in enumerate(levels):
            reason = _level_price_anomaly(level)
            if reason is None:
                continue
            anomaly_counts[reason] += 1
            if len(first_anomalies) < 8:
                first_anomalies.append(
                    {
                        "level_index_zero_based": index,
                        "reason": reason,
                        "raw_level": _bounded_level(level),
                    }
                )
        view["levels"][side] = {
            "count": len(levels),
            "first_three_levels": [_bounded_level(x) for x in levels[:3]],
            "price_anomaly_counts": anomaly_counts,
            "price_anomaly_example_limit": 8,
            "first_price_anomalies": first_anomalies,
        }
    return view


def _level_price_anomaly(level: Any) -> str | None:
    if not isinstance(level, list) or len(level) != 3:
        return "invalid_level_shape"
    raw_price = level[0]
    if not isinstance(raw_price, str):
        return "invalid_price"
    try:
        price = Decimal(raw_price)
    except InvalidOperation:
        return "invalid_price"
    if not price.is_finite():
        return "nonfinite_price"
    if price <= 0:
        return "nonpositive_price"
    return None


def _bounded_level(level: Any) -> Any:
    """Keep the visible raw tuple for ordinary records; cap anomalous fields."""
    if not isinstance(level, list):
        return _bounded_field(level)
    return [_bounded_field(value) for value in level[:3]]


def _bounded_field(value: Any) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = str(value)
    return text if len(text) <= 96 else text[:96] + "...[truncated]"
