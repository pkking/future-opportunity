from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from future_opportunity.backtest.availability_selection import (
    AvailabilitySelectionRequest,
    replay_availability_selection,
)

ROOT = Path(__file__).parents[1] / "docs" / "research"
MANIFEST = ROOT / "cash-2025q2-member-artifacts-manifest-v1.json"
AUDIT = ROOT / "cash-2025q2-member-population-audit-v1.json"

# SHA-256 of source-bound, reviewed immutable research controls.
MANIFEST_SHA = "88669cef7860f616b0483723c07edea82040bd86033a61bcc55a51bf4eb41b72"
AUDIT_SHA = "6030971d2060c603d6ce78222d68e0ea1f7a040f0c099b108fbf88247a298c6c"


def test_immutable_source_manifest_has_all_nine_official_artifacts():
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == MANIFEST_SHA
    raw = json.loads(MANIFEST.read_text())
    assert raw["member_source_run"] == "39045070860"
    assert raw["member_source_head_sha"] == "b5980b907d8e698906ef4fe49de18fba6b451cf6"
    assert raw["source_catalog_run"] == "39038071038"
    assert raw["source_catalog_artifact_id"] == "12103210971"
    assert raw["source_catalog_sha256"] == (
        "1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae"
    )
    batches = raw["batches"]
    assert len(batches) == 9
    assert [b["batch_index"] for b in batches] == list(range(9))
    assert len({b["artifact_id"] for b in batches}) == 9
    assert all(
        b["artifact_name"] == f"cash-2025q2-exact-members-batch-{i}"
        and len(b["zip_sha256"]) == 64
        for i, b in enumerate(batches)
    )


def test_member_census_is_complete_but_not_a_sample_or_trade_permission():
    assert hashlib.sha256(AUDIT.read_bytes()).hexdigest() == AUDIT_SHA
    manifest = json.loads(MANIFEST.read_text())
    audit = json.loads(AUDIT.read_text())
    assert audit["source_catalog_sha256"] == manifest["source_catalog_sha256"]
    assert audit["member_source_run"] == manifest["member_source_run"]
    assert audit["member_source_head_sha"] == manifest["member_source_head_sha"]
    assert audit["counts"] == {
        "identity_verified": 90, "unavailable": 0, "ambiguous": 0, "error": 0
    }
    assert audit["complete_member_population_verified"] is True
    assert audit["verified_member_available_dates"] == audit["frozen_calendar_dates"]
    assert audit["source_unavailable_dates"] == []
    assert len(audit["frozen_calendar_dates"]) == len(set(audit["frozen_calendar_dates"])) == 90
    assert audit["frozen_calendar_dates"][0] == "2025-03-29"
    assert audit["frozen_calendar_dates"][-1] == "2025-06-26"
    for flag in (
        "sample_selection_frozen", "l2_orderbook_verified", "economics_evaluated",
        "acquisition_approved", "promotion_approved",
    ):
        assert audit[flag] is False


def test_exit_day_is_source_available_but_cannot_be_selected_as_an_entry():
    raw = json.loads(AUDIT.read_text())
    exit_at = datetime.fromisoformat("2025-06-26T00:15:00+00:00")
    dates = raw["verified_member_available_dates"]
    assert dates[-1] == exit_at.date().isoformat()
    eligible = tuple(day for day in dates if
                     datetime.fromisoformat(day + "T00:15:00+00:00") < exit_at)
    assert len(eligible) == 89

    # This is a deterministic proposal replay, not a frozen sample. Its
    # output must be preregistered in a separate independently reviewed PR.
    selection = replay_availability_selection(AvailabilitySelectionRequest(
        strategy="cash-and-carry",
        start_date="2025-03-29",
        end_date="2025-06-26",
        excluded_market_dates=("2025-06-26",),
        sample_size=12,
    ))
    assert selection.eligible_market_dates == eligible
    assert len(selection.selected_market_dates) == 12
    assert all(
        datetime.fromisoformat(day + "T00:15:00+00:00") < exit_at
        for day in selection.selected_market_dates
    )
