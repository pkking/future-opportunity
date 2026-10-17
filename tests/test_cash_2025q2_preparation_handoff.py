from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from validate_cash_2025q2_preparation_handoff import (
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


def test_mutated_future_id_is_rejected():
    import copy
    import pytest

    raw = json.loads(WAVE.read_text())
    changed = copy.deepcopy(raw)
    changed["cash_cases"][0]["future_id"] = "BTC-USDT-250926"
    pinned = [
        x["entry_market_date"]
        for x in json.loads(CORPUS.read_text())["entries"]
        if x["strategy"] == "cash-and-carry"
    ]
    with pytest.raises(ValueError):
        validate_handoff(
            changed, json.loads(REGISTRY.read_text()),
            json.loads(AUDIT.read_text()),
            json.loads(MANIFEST.read_text()),
            pinned_dates=pinned,
        )


def test_selection_source_digest_cannot_drift():
    import copy
    import pytest

    raw = json.loads(WAVE.read_text())
    changed = copy.deepcopy(raw)
    changed["selection_provenance"]["cash"]["source"]["artifact_digest"] = (
        "sha256:" + "0" * 64
    )
    pinned = [
        x["entry_market_date"]
        for x in json.loads(CORPUS.read_text())["entries"]
        if x["strategy"] == "cash-and-carry"
    ]
    with pytest.raises(ValueError):
        validate_handoff(
            changed, json.loads(REGISTRY.read_text()),
            json.loads(AUDIT.read_text()),
            json.loads(MANIFEST.read_text()),
            pinned_dates=pinned,
        )
