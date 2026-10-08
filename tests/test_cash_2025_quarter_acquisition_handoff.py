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
    pinned = [
        item["entry_market_date"]
        for item in json.loads(INDEX.read_text())["entries"]
        if item["strategy"] == "cash-and-carry"
    ]
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
