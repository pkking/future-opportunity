from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from future_opportunity.backtest.campaign_planning import (
    VerifiedHistoricalCandidate,
)
from future_opportunity.backtest.promotion import (
    inspect_historical_compact_fixture,
)


_SHA256 = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_KEYS = {
    "source_root",
    "source_workflow_run",
    "compact_artifact_name",
    "compact_artifact_id",
    "compact_artifact_digest",
    "parent_artifact_id",
    "parent_artifact_sha256",
}


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"planner inventory requires {key}")
    return value


def verified_candidates_from_inventory(
    path: Path,
) -> tuple[tuple[VerifiedHistoricalCandidate, ...], list[dict[str, str]]]:
    """Validate downloaded compact fixtures without staging corpus changes.

    The Actions workflow independently verifies artifact API digests before
    writing this input. This offline parser checks schema, parent manifest
    provenance, canonical fixture checksums, and business identity.
    """
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "items"}:
        raise ValueError("invalid planner inventory fields")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise ValueError("unsupported planner inventory schema")
    raw_items = raw.get("items")
    if not isinstance(raw_items, list):
        raise TypeError("planner inventory items must be an array")
    if len(raw_items) > 620:
        raise ValueError("planner inventory exceeds 620 compact artifacts")

    candidates: list[VerifiedHistoricalCandidate] = []
    evidence: list[dict[str, str]] = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict) or set(item) != _KEYS:
            raise ValueError(f"planner inventory item {idx} fields differ from schema")
        fields = {key: _required_string(item, key) for key in _KEYS}
        for key in ("source_workflow_run", "compact_artifact_id", "parent_artifact_id"):
            if not fields[key].isdigit():
                raise ValueError(f"planner inventory item {idx} {key} must be numeric")
        for key in ("compact_artifact_digest", "parent_artifact_sha256"):
            if _SHA256.fullmatch(fields[key]) is None:
                raise ValueError(f"planner inventory item {idx} {key} invalid SHA-256")
        entry = inspect_historical_compact_fixture(
            Path(fields["source_root"]),
            source_workflow_run=fields["source_workflow_run"],
            expected_parent_artifact_id=fields["parent_artifact_id"],
            expected_parent_artifact_sha256=fields["parent_artifact_sha256"],
        )
        candidates.append(
            VerifiedHistoricalCandidate(
                source_workflow_run=fields["source_workflow_run"],
                compact_artifact_name=fields["compact_artifact_name"],
                entry=entry,
            )
        )
        evidence.append({
            "source_workflow_run": fields["source_workflow_run"],
            "compact_artifact_name": fields["compact_artifact_name"],
            "compact_artifact_id": fields["compact_artifact_id"],
            "compact_artifact_digest": fields["compact_artifact_digest"],
            "parent_artifact_id": fields["parent_artifact_id"],
            "parent_artifact_sha256": fields["parent_artifact_sha256"],
            "dataset_id": entry.dataset_id,
            "strategy": entry.strategy,
            "entry_market_date": entry.entry_market_date,
        })
    return tuple(candidates), evidence
