"""Deterministic no-network tests: independent witness draft never grants R2 trust."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/review_funding_witness_draft.py"
DAY = "2026-10-25"
ENTRY = "2026-10-25T00:15:00+00:00"


def _module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_r2_candidate_draft", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ts(iso):
    return str(int(datetime.fromisoformat(iso).timestamp() * 1_000))


def _capture():
    funding = {"code": "0", "data": [
        {
            "instId": "BTC-USDT-SWAP",
            "instType": "SWAP",
            "fundingTime": _ts("2026-10-24T16:00:00+00:00"),
            "realizedRate": "0.00021",
            "fundingRate": "0.00022",
        },
    ]}
    daily = [
        [
            _ts(f"2026-10-{day:02d}T00:00:00+00:00"),
            "100", "110", "90", str(100 + day), "10", "10", "10", "1",
        ]
        for day in range(17, 25)
    ]
    # The current-day candle is legitimately still uncompleted at entry.
    daily.insert(0, [
        _ts("2026-10-25T00:00:00+00:00"),
        "110", "111", "109", "110", "2", "2", "2", "0",
    ])
    spot = {"code": "0", "data": daily}
    return {
        "schema_version": 1,
        "captured_at": "2026-10-25T00:05:00+00:00",
        "start_date": DAY, "end_date": DAY,
        "seed": "synthetic-r1-no-market-request",
        "requested_per_regime": 1,
        "pinned_market_dates": [],
        "funding_query": {"instId": "BTC-USDT-SWAP", "limit": "400"},
        "funding_response": funding,
        "spot_query": {"instId": "BTC-USDT", "bar": "1Dutc", "limit": "100"},
        "spot_response": spot,
    }


def _json_bytes(body):
    return (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _receipt(funding, spot):
    return {
        "schema_version": 1,
        "entry_market_date": DAY,
        "entry_at": ENTRY,
        "observer_id": "independent-operator-A",
        "collector_id": "collector-original-VPS",
        "observer_network": "network-A",
        "collector_network": "network-B",
        "clock_uncertainty_ms": 100,
        "witness_recorded_at": "2026-10-25T00:04:00+00:00",
        "funding": {
            "endpoint": "/api/v5/public/funding-rate-history",
            "query": {"instId": "BTC-USDT-SWAP", "limit": "400"},
            "started_at": "2026-10-25T00:01:00+00:00",
            "received_at": "2026-10-25T00:02:00+00:00",
            "raw_sha256": hashlib.sha256(_json_bytes(funding)).hexdigest(),
        },
        "spot": {
            "endpoint": "/api/v5/market/history-candles",
            "query": {"instId": "BTC-USDT", "bar": "1Dutc", "limit": "100"},
            "started_at": "2026-10-25T00:02:30+00:00",
            "received_at": "2026-10-25T00:03:30+00:00",
            "raw_sha256": hashlib.sha256(_json_bytes(spot)).hexdigest(),
        },
    }


def _files(tmp_path, *, source=None, receipt=None, funding=None, spot=None):
    r1 = copy.deepcopy(source if source is not None else _capture())
    f = copy.deepcopy(funding if funding is not None else r1["funding_response"])
    s = copy.deepcopy(spot if spot is not None else r1["spot_response"])
    rcpt = copy.deepcopy(receipt if receipt is not None else _receipt(f, s))
    paths = [tmp_path / name for name in ("receipt.json", "funding.json", "spot.json", "r1.json")]
    for path, blob in zip(paths, (_json_bytes(rcpt), _json_bytes(f), _json_bytes(s), _json_bytes(r1)), strict=True):
        path.write_bytes(blob)
    return paths


def _run(mod, paths):
    return mod.review_draft(*paths)


def test_semantic_match_still_never_attests_observer_or_approves_acquisition(
    monkeypatch, tmp_path,
):
    mod = _module(monkeypatch)
    report = _run(mod, _files(tmp_path))
    assert report["status"] == "CANDIDATE_MATCH_UNATTESTED"
    assert report["declared_timing_and_source_internally_consistent"] is True
    assert report["source_record_match"] is True
    assert report["entry_market_date"] == DAY
    assert len(report["candidate_source_record_sha256"]) == 64
    assert report["candidate_source_record_sha256"] == report["r1_source_record_sha256"]
    for flag in (
        "observer_identity_attested", "trusted_time_attested",
        "r1_source_custody_verified_here", "exchange_signed",
        "point_in_time_publication_verified", "acquisition_approved",
        "promotion_approved",
    ):
        assert report[flag] is False
    assert report["market_wide_opportunity_arrival_rate"] is None


@pytest.mark.parametrize("field,left,right", [
    ("observer_id", "collector_id", "same-VPS"),
    ("observer_network", "collector_network", "same-network"),
])
def test_self_witness_declaration_is_rejected(monkeypatch, tmp_path, field, left, right):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    receipt = json.loads(paths[0].read_text())
    receipt[field] = receipt[left]
    paths[0].write_bytes(_json_bytes(receipt))
    report = _run(mod, paths)
    assert report["status"] == "UNASSESSED"
    assert report["acquisition_approved"] is False


@pytest.mark.parametrize("changes", [
    {"witness_recorded_at": "2026-10-25T00:15:00+00:00"},
    {"clock_uncertainty_ms": 1001},
    {"clock_uncertainty_ms": True},
    {
        "witness_recorded_at": "2026-10-25T00:14:59.900+00:00",
        "clock_uncertainty_ms": 1000,
    },
    {"entry_at": "2026-10-25T00:30:00+00:00"},
    {"entry_market_date": "2026-10-26"},
])
def test_observer_deadline_clock_bound_and_day_fail_closed(monkeypatch, tmp_path, changes):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    receipt = json.loads(paths[0].read_text())
    receipt.update(changes)
    paths[0].write_bytes(_json_bytes(receipt))
    assert _run(mod, paths)["status"] == "UNASSESSED"


@pytest.mark.parametrize("field,new_value", [
    ("spot", {"endpoint": "/api/v5/trade/order"}),
    ("funding", {"query": {"instId": "ETH-USDT-SWAP", "limit": "400"}}),
    ("funding", {"started_at": "2026-10-25T00:03:30+00:00"}),
    ("spot", {"received_at": "2026-10-25T00:15:01+00:00"}),
])
def test_invalid_endpoint_query_or_order_fail_closed(monkeypatch, tmp_path, field, new_value):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    receipt = json.loads(paths[0].read_text())
    receipt[field].update(new_value)
    paths[0].write_bytes(_json_bytes(receipt))
    assert _run(mod, paths)["status"] == "UNASSESSED"


def test_original_byte_digest_mismatch_and_duplicate_json_keys_rejected(monkeypatch, tmp_path):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    paths[1].write_bytes(paths[1].read_bytes() + b" ")
    assert _run(mod, paths)["status"] == "UNASSESSED"
    paths = _files(tmp_path)
    paths[1].write_bytes(b'{"code":"0","code":"0","data":[]}')
    assert _run(mod, paths)["status"] == "UNASSESSED"


def test_missing_completed_candle_is_unassessed_even_if_other_records_agree(
    monkeypatch, tmp_path,
):
    mod = _module(monkeypatch)
    r1 = _capture()
    spot = copy.deepcopy(r1["spot_response"])
    spot["data"] = [
        item for item in spot["data"]
        if item[0] != _ts("2026-10-20T00:00:00+00:00")
    ]
    paths = _files(tmp_path, source=r1, spot=spot)
    rec = _receipt(r1["funding_response"], spot)
    paths[0].write_bytes(_json_bytes(rec))
    report = _run(mod, paths)
    assert report["status"] == "UNASSESSED"


def test_same_event_changed_funding_or_confirmed_close_is_conflict_not_approval(
    monkeypatch, tmp_path,
):
    mod = _module(monkeypatch)
    for field in ("funding", "close"):
        folder = tmp_path / field
        folder.mkdir()
        r1 = _capture()
        funding = copy.deepcopy(r1["funding_response"])
        spot = copy.deepcopy(r1["spot_response"])
        if field == "funding":
            funding["data"][0]["realizedRate"] = "0.004"
        else:
            spot["data"][1][4] = "999"
        paths = _files(folder, funding=funding, spot=spot)
        paths[0].write_bytes(_json_bytes(_receipt(funding, spot)))
        report = _run(mod, paths)
        assert report["status"] == "CANDIDATE_CONFLICT_UNATTESTED"
        assert report["declared_timing_and_source_internally_consistent"] is True
        assert report["source_record_match"] is False
        assert report["point_in_time_publication_verified"] is False


def test_symlink_and_malformed_r1_custody_claim_not_trusted(monkeypatch, tmp_path):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    actual = paths[1]
    link = tmp_path / "funding-link.json"
    link.symlink_to(actual)
    report = _run(mod, [paths[0], link, paths[2], paths[3]])
    assert report["status"] == "UNASSESSED"
    paths[3].write_bytes(b"{}")
    assert _run(mod, paths)["status"] == "UNASSESSED"


def test_cli_exclusive_report_write_and_no_network_sdk(monkeypatch, tmp_path):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    destination = tmp_path / "report.json"
    monkeypatch.setattr(
        sys, "argv", ["review-witness", "--receipt", str(paths[0]),
                      "--funding-body", str(paths[1]), "--spot-body", str(paths[2]),
                      "--r1-source", str(paths[3]), "--output", str(destination)],
    )
    mod.main()
    assert json.loads(destination.read_text())["status"] == "CANDIDATE_MATCH_UNATTESTED"
    with pytest.raises(FileExistsError):
        mod.main()
    script = SCRIPT.read_text()
    for forbidden in ("import httpx", "requests.get", "client.get(", "api/v5/trade/order"):
        assert forbidden not in script


def test_outcome_blind_and_non_promotion_flags_cannot_be_supplied_by_receipt(
    monkeypatch, tmp_path,
):
    mod = _module(monkeypatch)
    paths = _files(tmp_path)
    receipt = json.loads(paths[0].read_text())
    receipt["acquisition_approved"] = True
    paths[0].write_bytes(_json_bytes(receipt))
    assert _run(mod, paths)["status"] == "UNASSESSED"
