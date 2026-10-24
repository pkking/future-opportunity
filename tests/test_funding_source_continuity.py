"""Offline, HTTP GET-only acceptance tests for longitudinal Funding originals."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/report_funding_source_continuity.py"
DAYS = ["2026-10-23", "2026-10-24", "2026-10-25"]
NOW = datetime(2026, 10, 25, 8, tzinfo=UTC)


def _module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_source_continuity", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ms(day):
    return str(int(datetime.fromisoformat(day + "T00:00:00+00:00").timestamp() * 1000))


def _raw(day, *, rate="0.001", close="100", empty=False, open_candle=False):
    source_days = ["2026-10-21", "2026-10-22", "2026-10-23"]
    funding = [
        {
            "instId": "BTC-USDT-SWAP",
            "instType": "SWAP",
            "fundingTime": _ms(d),
            "realizedRate": rate if i == 1 else "0.002",
        } for i, d in enumerate(source_days)
    ]
    candles = [
        [_ms(d), "100", "101", "80",
         close if i == 1 else "100", "1", "1", "1",
         "0" if i == 2 and open_candle else "1"]
        for i, d in enumerate(source_days)
    ]
    return {
        "start_date": day, "end_date": day,
        "funding_response": {"code": "0", "data": [] if empty else funding},
        "spot_response": {"code": "0", "data": [] if empty else candles},
    }


def _zip(raw):
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("raw-api-capture.json", json.dumps(raw, sort_keys=True))
        z.writestr("http-timing.json", "{}")
        z.writestr("preentry-research-evidence.json", "{}")
    return memory.getvalue()


def _audit(day):
    return {
        "id": 200 + DAYS.index(day), "event": "release",
        "head_branch": f"funding-vps-{day}",
        "name": "Audit Immutable VPS Funding Evidence Release",
        "status": "completed", "conclusion": "success",
        "created_at": f"{day}T00:00:17Z", "run_attempt": 1,
    }


def _mock(*, records=None, missing_audit=(), tamper=(), audits=None):
    if records is None:
        records = {day: _raw(day) for day in DAYS}
    original = {day: _zip(record) for day, record in records.items()}
    calls = []
    if audits is None:
        audits = [_audit(day) for day in reversed(DAYS) if day not in missing_audit]

    def handler(request):
        calls.append((request.method, request.url.host, request.url.path))
        assert request.method == "GET"
        assert request.url.host in ("github.com", "api.github.com")
        if "/actions/workflows/" in request.url.path:
            return httpx.Response(200, json={"workflow_runs": audits})
        if "/releases/tags/" in request.url.path:
            day = request.url.path[-10:]
            return httpx.Response(200, json={"tag_name": f"funding-vps-{day}"})
        if "/releases/download/" in request.url.path:
            day = request.url.path.split("/")[5].removeprefix("funding-vps-")
            body = b"tampered original" if day in tamper else original[day]
            return httpx.Response(200, content=body)
        return httpx.Response(404)

    def verify(day, *, client):
        assert isinstance(client, httpx.Client)
        return {
            "status": "github_immutable_release_metadata_and_offline_replay_only",
            "tag": f"funding-vps-{day}",
            "published_at": f"{day}T00:00:15Z",
            "archive_sha256": hashlib.sha256(original[day]).hexdigest(),
            "regime": "nonnegative_high_volatility",
        }

    return httpx.Client(transport=httpx.MockTransport(handler)), verify, calls


def _check(mod, client, verify):
    return mod.audit_continuity(
        DAYS[0], DAYS[-1], now=lambda: NOW,
        client=client, token="synthetic-read-only", verify=verify,
    )


def test_three_day_chain_compares_every_adjacent_pair_once_and_never_promotes(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, calls = _mock()
    with client:
        report = _check(mod, client, verify)
    assert report["status"] == "OVERLAP_VALUES_CONSISTENT_ONLY"
    assert report["checked_day_count"] == 3
    assert report["expected_pair_count"] == 2
    assert report["consistent_pair_count"] == 2
    assert report["revision_pair_count"] == 0
    assert report["unassessed_pair_count"] == 0
    assert report["every_adjacent_pair_assessed"] is True
    assert [(p["earlier_day"], p["later_day"]) for p in report["pairs"]] == [
        (DAYS[0], DAYS[1]), (DAYS[1], DAYS[2])
    ]
    assert all(p["comparison"]["funding"]["overlap_count"] == 3 for p in report["pairs"])
    assert report["source_regime_coverage"]["github_audited_day_count"] == 3
    assert sum("/releases/download/" in path for _, _, path in calls) == 3
    assert len(calls) == 1 + 3 + 3  # one workflow history + 3 metadata + 3 originals
    assert all(method == "GET" and host in ("github.com", "api.github.com")
               for method, host, _ in calls)
    for flag in (
        "exchange_signed", "point_in_time_publication_verified",
        "acquisition_approved", "promotion_approved"
    ):
        assert report[flag] is False
    assert report["market_wide_opportunity_arrival_rate"] is None
    assert json.loads(json.dumps(report))["expected_pair_count"] == 2


def test_missing_middle_audit_keeps_two_explicit_gaps_not_one_long_pair(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, calls = _mock(missing_audit=(DAYS[1],))
    with client:
        report = _check(mod, client, verify)
    assert report["status"] == "UNASSESSED"
    assert report["expected_pair_count"] == 2
    assert report["unassessed_pair_count"] == 2
    assert report["consistent_pair_count"] == 0
    assert report["source_days"][1]["custody_status"] == "AUDIT_MISSING"
    assert report["source_regime_coverage"]["github_audited_day_count"] == 2
    assert all(pair["status"] == "UNASSESSED" for pair in report["pairs"])
    assert [p["later_day"] for p in report["pairs"]] == DAYS[1:]
    assert sum("/releases/download/" in path for _, _, path in calls) == 2


def test_funding_numeric_revision_is_explicit_not_hidden_by_missing_other_pair(monkeypatch):
    mod = _module(monkeypatch)
    raw = {d: _raw(d) for d in DAYS}
    raw[DAYS[1]] = _raw(DAYS[1], rate="0.003")
    client, verify, _ = _mock(records=raw, tamper=(DAYS[2],))
    with client:
        report = _check(mod, client, verify)
    assert report["status"] == "SOURCE_REVISION_DETECTED"
    assert report["expected_pair_count"] == 2
    assert report["revision_pair_count"] == 1
    assert report["unassessed_pair_count"] == 1
    assert report["every_adjacent_pair_assessed"] is False
    assert report["pairs"][0]["comparison"]["funding"]["realized_rate_revisions"]
    assert report["pairs"][1]["status"] == "UNASSESSED"
    assert report["source_days"][2]["source_status"] == "UNASSESSED"


def test_normal_daily_confirmation_advance_is_not_revision(monkeypatch):
    mod = _module(monkeypatch)
    source = {d: _raw(d) for d in DAYS}
    source[DAYS[0]] = _raw(DAYS[0], open_candle=True)
    client, verify, _ = _mock(records=source)
    with client:
        report = _check(mod, client, verify)
    assert report["status"] == "OVERLAP_VALUES_CONSISTENT_ONLY"
    assert report["pairs"][0]["comparison"]["spot"]["confirmation_state_advances"] == [
        "2026-10-23T00:00:00+00:00",
    ]
    assert report["pairs"][0]["comparison"]["spot"]["confirmation_state_regressions"] == []


def test_empty_retention_overlap_is_explicit_unassessed(monkeypatch):
    mod = _module(monkeypatch)
    raw = {d: _raw(d) for d in DAYS}
    raw[DAYS[1]] = _raw(DAYS[1], empty=True)
    client, verify, _ = _mock(records=raw)
    with client:
        report = _check(mod, client, verify)
    assert report["status"] == "UNASSESSED"
    assert report["unassessed_pair_count"] == 2
    assert all(p["status"] == "UNASSESSED_INSUFFICIENT_OVERLAP"
               for p in report["pairs"])


@pytest.mark.parametrize("start,end,at", [
    (DAYS[0], DAYS[0], NOW),
    ("2026-10-22", DAYS[0], NOW),
    (DAYS[-1], DAYS[0], NOW),
    (DAYS[0], "2026-10-2x", NOW),
    (DAYS[0], "2027-01-22", datetime(2027, 2, 1, tzinfo=UTC)),
    (DAYS[0], DAYS[-1], datetime(2026, 10, 25, 0, 14, tzinfo=UTC)),
    (DAYS[0], DAYS[-1], datetime(2026, 10, 25)),
])
def test_invalid_range_fails_before_github_calls(monkeypatch, start, end, at):
    mod = _module(monkeypatch)
    client, verify, calls = _mock()
    with client, pytest.raises(ValueError):
        mod.audit_continuity(
            start, end, now=lambda: at,
            client=client, token="synthetic", verify=verify,
        )
    assert calls == []


def test_exact_90day_window_is_allowed_after_deadline(monkeypatch):
    mod = _module(monkeypatch)
    date0 = datetime(2026, 10, 23, tzinfo=UTC).date()
    last = date0 + timedelta(days=89)
    assert len(mod.eligible_days(
        DAYS[0], last.isoformat(), datetime(2027, 2, 1, tzinfo=UTC)
    )) == 90
    assert mod.MAX_CONTINUITY_DAYS == 90
