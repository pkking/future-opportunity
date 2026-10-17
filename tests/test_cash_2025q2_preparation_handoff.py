from __future__ import annotations

import json

from scripts.validate_cash_2025q2_preparation_handoff import (
    AUDIT, CORPUS, MANIFEST, REGISTRY, WAVE, validate_handoff,
)


def test_offline_handoff_does_not_dispatch():
    pinned = [
        x["entry_market_date"]
        for x in json.loads(CORPUS.read_text())["entries"]
        if x["strategy"] == "cash-and-carry"
    ]
    report = validate_handoff(
        json.loads(WAVE.read_text()),
        json.loads(REGISTRY.read_text()),
        json.loads(AUDIT.read_text()),
        json.loads(MANIFEST.read_text()),
        pinned_dates=pinned,
    )
    assert report["expected_cash_preparations"] == 12
    assert report["historical_acquisition_dispatched"] is False
    assert report["promotion_approved"] is False
