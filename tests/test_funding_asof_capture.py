"""Offline negative/positive controls for prospective, not retrospective, Funding capture."""
from __future__ import annotations


from pathlib import Path

import pytest

from future_opportunity.backtest.funding_asof_capture import validate_preentry_source
from test_funding_raw_feature_lineage import make_capture

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/capture-funding-preentry-source.yml"
SCRIPT = ROOT / "scripts/capture_funding_preentry_source.py"


def _base():
    raw = make_capture()
    raw["start_date"] = raw["end_date"] = "2026-09-15"
    # Simulated observation at UTC 00:10 cannot include later settled events
    # or future daily candles; keep only genuine prior source rows.
    raw["funding_response"]["data"] = raw["funding_response"]["data"][:1]
    raw["spot_response"]["data"] = raw["spot_response"]["data"][:8]
    raw["captured_at"] = "2026-09-15T00:10:00+00:00"
    return raw, {
        "entry_at": "2026-09-15T00:15:00+00:00",
        "funding_request_started_at": "2026-09-15T00:01:00+00:00",
        "funding_response_received_at": "2026-09-15T00:02:00+00:00",
        "spot_request_started_at": "2026-09-15T00:03:00+00:00",
        "spot_response_received_at": "2026-09-15T00:04:00+00:00",
    }


def test_preentry_capture_reuses_exact_raw_event_time_features_without_promoting():
    raw, timing = _base()
    result = validate_preentry_source(raw, timing)
    assert result["http_transactions_completed_before_entry"] is True
    assert result["entry_at"] == "2026-09-15T00:15:00+00:00"
    assert result["lagged_funding_rate"] == "-0.00015"
    assert result["evidence_status"] == "local_capture_not_independently_attested"
    assert result["point_in_time_publication_verified"] is False
    assert result["exchange_signed"] is False
    assert result["acquisition_approved"] is False
    assert result["promotion_approved"] is False
    assert len(result["raw_source_sha256"]) == 64
    assert len(result["source_record_sha256"]) == 64


@pytest.mark.parametrize("field,value,error", [
    ("funding_request_started_at", "2026-09-14T23:59:59+00:00", "before entry"),
    ("funding_response_received_at", "2026-09-15T00:16:00+00:00", "before entry"),
    ("spot_request_started_at", "2026-09-15T00:01:00+00:00", "before entry"),
    ("spot_response_received_at", "2026-09-15T00:15:00+00:00", "before entry"),
    ("entry_at", "2026-09-15T00:14:00+00:00", "00:15"),
])
def test_time_boundary_fail_closed(field, value, error):
    raw, timing = _base()
    timing[field] = value
    with pytest.raises(ValueError, match=error):
        validate_preentry_source(raw, timing)


def test_capture_after_entry_never_certifies_publication():
    raw, timing = _base()
    raw["captured_at"] = "2026-09-15T00:15:01+00:00"
    with pytest.raises(ValueError, match="before entry"):
        validate_preentry_source(raw, timing)


def test_rejects_historical_relabeling_and_source_missing():
    raw, timing = _base()
    raw["start_date"] = raw["end_date"] = "2026-09-14"
    with pytest.raises(ValueError, match="source date"):
        validate_preentry_source(raw, timing)
    raw, timing = _base()
    raw["spot_response"]["data"][7][8] = "0"
    with pytest.raises(ValueError, match="missing or stale"):
        validate_preentry_source(raw, timing)
    raw, timing = _base()
    raw["funding_response"]["data"] = []
    with pytest.raises(ValueError, match="missing or stale"):
        validate_preentry_source(raw, timing)
    raw, timing = _base()
    raw["extra_profitability"] = 123
    with pytest.raises(ValueError, match="schema"):
        validate_preentry_source(raw, timing)


def test_future_funding_event_and_future_confirmed_candle_fail_closed():
    raw, timing = _base()
    row = dict(raw["funding_response"]["data"][0])
    row["fundingTime"] = "1790006400000"
    raw["funding_response"]["data"].append(row)
    with pytest.raises(ValueError, match="future settled funding"):
        validate_preentry_source(raw, timing)

    raw, timing = _base()
    row = list(raw["spot_response"]["data"][-1])
    row[0] = "1789516800000"
    raw["spot_response"]["data"].append(row)
    with pytest.raises(ValueError, match="future confirmed daily candle"):
        validate_preentry_source(raw, timing)


def test_observer_is_manual_only_read_only_and_offline_tests_are_deterministic():
    wf = WORKFLOW.read_text()
    script = SCRIPT.read_text()
    assert "workflow_dispatch:" in wf
    assert "  push:" not in wf and "  schedule:" not in wf
    assert "attest-build-provenance@v2" in wf
    assert "id-token: write" in wf and "attestations: write" in wf
    assert "contents: read" in wf
    assert "api-key" not in script and "apiKey" not in script
    assert "client.get(" in script and "client.post(" not in script
    assert "orders" not in script.lower()
    assert "_now()" in script and "00:00..00:15" in script
    assert "follow_redirects=False" in script
    assert "if: always()" in wf
