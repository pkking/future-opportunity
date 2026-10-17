from __future__ import annotations

import json
from pathlib import Path

from future_opportunity.backtest.acquisition import (
    load_historical_acquisition_manifest,
)
from future_opportunity.backtest.cash_prior_quarter_selection import (
    validate_cash_prior_quarter_preregistration,
)


ROOT = Path(__file__).parents[1]
PLANS = ROOT / "docs/historical-acquisition-plans"
FROZEN = PLANS / "cash-2025-q3q4-24day-preregistration-v1.json"
Q3 = PLANS / "cash-2025-q3-12day-wave-001.json"
Q4 = PLANS / "cash-2025-q4-12day-wave-001.json"
INDEX = ROOT / "tests/fixtures/historical/corpus-index.json"


def test_2025_quarter_manifests_replay_exact_source_selection() -> None:
    frozen = json.loads(FROZEN.read_text())
    # Replaying the *pre-promotion* selection after this wave is merged must
    # not mistake exact source-matching pinned examples for date-selection
    # drift. Reject any mismatched source, expiry, exit or partial cohort.
    selected_by_date = {
        day: (quarter, Q3 if quarter["quarter"] == "2025-Q3" else Q4)
        for quarter in frozen["quarters"]
        for day in quarter["selected_market_dates"]
    }
    pinned: list[str] = []
    promoted: set[str] = set()
    for item in json.loads(INDEX.read_text())["entries"]:
        if item["strategy"] != "cash-and-carry":
            continue
        day = item["entry_market_date"]
        if day not in selected_by_date:
            pinned.append(day)
            continue
        quarter, source_manifest_path = selected_by_date[day]
        staged = json.loads(
            (ROOT / "tests/fixtures/historical" / item["fixture_path"] / "manifest.json")
            .read_text()
        )
        source = json.loads(source_manifest_path.read_text())
        assert staged["entry_market_date"] == day
        assert staged["instrument"]["future_instrument_id"] == quarter["future_id"]
        assert staged["sample_times"]["entry"] == day + "T00:15:00+00:00"
        assert staged["sample_times"]["exit"] == quarter["exit_at"]
        assert staged["selection_provenance"] == source["selection_provenance"]["cash"]
        promoted.add(day)
    assert len(set(pinned)) == len(pinned)
    assert not promoted or promoted == set(selected_by_date), (
        "frozen cohort must be promoted atomically"
    )
    selection = validate_cash_prior_quarter_preregistration(
        frozen, pinned_cash_market_dates=pinned,
    )
    q3 = load_historical_acquisition_manifest(Q3)
    q4 = load_historical_acquisition_manifest(Q4)

    for manifest, cohort, future, exit_at, expiry_at, evidence_hash in (
        (
            q3,
            selection["quarters"][0],
            "BTC-USDT-250926",
            "2025-09-25T00:15:00+00:00",
            "2025-09-26T08:00:00+00:00",
            "3449f56506669a382dbc6c7290d762a00d518a84bebc9530eb904c03e3ab70cd",
        ),
        (
            q4,
            selection["quarters"][1],
            "BTC-USDT-251226",
            "2025-12-25T00:15:00+00:00",
            "2025-12-26T08:00:00+00:00",
            "97c3b6c4f296e5819055eace56b5c396c317e285051ea142be2dcb8799073f8b",
        ),
    ):
        assert manifest.funding is None
        assert len(manifest.cash_cases) == 12
        assert [c.entry_market_date for c in manifest.cash_cases] == cohort["selected_market_dates"]
        assert all(c.future_id == future for c in manifest.cash_cases)
        assert all(c.entry_at.endswith("T00:15:00+00:00") for c in manifest.cash_cases)
        assert all(c.exit_at == exit_at for c in manifest.cash_cases)
        assert all(c.expiry_at == expiry_at for c in manifest.cash_cases)
        provenance = manifest.cash_selection_provenance
        assert provenance is not None
        assert provenance.selection_kind == "pre_registered_availability_sample"
        assert provenance.sampling_evidence_sha256 == evidence_hash
        assert provenance.source.workflow_run == "37755705789"
        assert provenance.source.artifact_id == "11539833591"
        assert provenance.source.artifact_digest == (
            "sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74"
        )

    q3_dates = {c.entry_market_date for c in q3.cash_cases}
    q4_dates = {c.entry_market_date for c in q4.cash_cases}
    assert q3_dates.isdisjoint(q4_dates)
    assert q3_dates.union(q4_dates) == set(selection["selected_market_dates"])
    assert not q3_dates.union(q4_dates).intersection(pinned)


def test_cash_2025_preparation_workflow_requires_dispatch_and_no_promotion() -> None:
    workflow = (
        ROOT / ".github/workflows/prepare-cash-2025-quarter-wave.yml"
    ).read_text()
    assert "workflow_dispatch:" in workflow
    assert "\n  push:" not in workflow
    assert "- q3" in workflow
    assert "- q4" in workflow
    assert "acquire-historical-campaign.yml" in workflow
    assert "max-cash-cases 12" in workflow
    assert "promotion_dispatched: false" in workflow
    assert "corpus_mutation: false" in workflow
    assert "promote-historical-campaign.yml" not in workflow
    assert "promote-planned-historical-wave.yml" not in workflow
