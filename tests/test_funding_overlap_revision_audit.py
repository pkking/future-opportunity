"""No-network original-asset tests for two-day Funding source revision review."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/audit_funding_source_revision.py"
OLD, NEW = "2026-10-23", "2026-10-24"
NOW = datetime(2026, 10, 24, 7, tzinfo=UTC)


def _module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_revision_source_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ms(day):
    return str(int(datetime.fromisoformat(day + "T00:00:00+00:00").timestamp() * 1000))


def _source(day, *, funding_rate="0.002", close="90", empty=False, confirmed="1"):
    dates = ["2026-10-19", "2026-10-20", "2026-10-21"]
    return {
        "start_date": day,
        "end_date": day,
        "funding_response": {"code": "0", "data": [] if empty else [
            {"instId": "BTC-USDT-SWAP", "instType": "SWAP",
             "fundingTime": _ms(x), "realizedRate": funding_rate if i == 1 else "0.001"}
            for i, x in enumerate(dates)
        ]},
        "spot_response": {"code": "0", "data": [] if empty else [
            [_ms(x), "100", "101", "80", close if i == 1 else "100",
             "1", "1", "1", confirmed if i == 1 else "1"]
            for i, x in enumerate(dates)
        ]},
    }


def _zip(source, *, malformed=False):
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("raw-api-capture.json", json.dumps(source, sort_keys=True))
        z.writestr("http-timing.json", "{}")
        if malformed:
            z.writestr("raw-api-capture.json", "{}")
        else:
            z.writestr("preentry-research-evidence.json", "{}")
    return buff.getvalue()


def _aud(day, *, conclusion="success"):
    return {
        "id": 300 if day == OLD else 301,
        "event": "release",
        "head_branch": f"funding-vps-{day}",
        "name": "Audit Immutable VPS Funding Evidence Release",
        "created_at": f"{day}T00:00:17Z",
        "status": "completed",
        "conclusion": conclusion,
        "run_attempt": 1,
    }


def _client(*, old=None, new=None, audits=None, later_bytes=None):
    archives = {
        OLD: _zip(old if old is not None else _source(OLD)),
        NEW: _zip(new if new is not None else _source(NEW)),
    }
    assert later_bytes is None or isinstance(later_bytes, bytes)
    requested = []
    if audits is None:
        audits = [_aud(NEW), _aud(OLD)]

    def handler(req):
        requested.append((req.method, req.url.host, req.url.path))
        assert req.method == "GET"
        assert req.url.host in {"api.github.com", "github.com"}
        if "/actions/workflows/" in req.url.path:
            return httpx.Response(200, json={"workflow_runs": audits})
        if "/releases/tags/" in req.url.path:
            day = req.url.path[-10:]
            return httpx.Response(200, json={"tag_name": f"funding-vps-{day}"})
        if "/releases/download/" in req.url.path:
            day = req.url.path.split("/")[5].removeprefix("funding-vps-")
            return httpx.Response(
                200, content=(
                    later_bytes if day == NEW and later_bytes is not None
                    else archives[day]
                ),
            )
        return httpx.Response(404)

    def verify(day, *, client):
        assert isinstance(client, httpx.Client)
        return {
            "status": "github_immutable_release_metadata_and_offline_replay_only",
            "tag": f"funding-vps-{day}",
            "published_at": f"{day}T00:00:15Z",
            "archive_sha256": hashlib.sha256(archives[day]).hexdigest(),
            "regime": "nonnegative_high_volatility",
        }

    return httpx.Client(transport=httpx.MockTransport(handler)), verify, requested


def _audit(mod, client, verify):
    return mod.audit_pair(
        OLD, NEW, now=lambda: NOW, client=client,
        token="mock-read-only-gh-token", verify=verify,
    )


def test_stable_overlap_is_only_source_consistency_not_exchange_authentication(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, requests = _client()
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "OVERLAP_VALUES_CONSISTENT_ONLY"
    assert result["source_custody_ledger_status"] == "AUDITED_GITHUB_CUSTODY_ONLY"
    assert result["comparison"]["funding"]["overlap_count"] == 3
    assert result["comparison"]["spot"]["confirmed_close_overlap_count"] == 3
    assert result["comparison"]["funding"]["realized_rate_revisions"] == []
    assert result["comparison"]["spot"]["confirmed_close_revisions"] == []
    assert len(result["original_archive_sha256"]) == 2
    for flag in (
        "exchange_signed", "point_in_time_publication_verified",
        "acquisition_approved", "promotion_approved",
    ):
        assert result[flag] is False
    assert result["market_wide_opportunity_arrival_rate"] is None
    assert len(requests) == 5
    assert all(method == "GET" and host in {"api.github.com", "github.com"}
               for method, host, _ in requests)
    assert json.loads(json.dumps(result))["comparison"]["status"] == (
        "OVERLAP_VALUES_CONSISTENT_ONLY"
    )


@pytest.mark.parametrize("change,field", [
    ({"funding_rate": "0.004"}, "realized_rate_revisions"),
    ({"close": "91"}, "confirmed_close_revisions"),
    ({"confirmed": "0"}, "confirmation_state_conflicts"),
])
def test_revisions_in_overlapping_settled_or_confirmed_values_fail_closed(
    monkeypatch, change, field,
):
    mod = _module(monkeypatch)
    client, verify, _ = _client(new=_source(NEW, **change))
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "SOURCE_REVISION_DETECTED"
    group = "funding" if field == "realized_rate_revisions" else "spot"
    assert len(result["comparison"][group][field]) == 1
    assert result["acquisition_approved"] is False


def test_equivalent_decimal_text_is_not_a_numeric_rate_revision(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, _ = _client(new=_source(NEW, funding_rate="0.0020", close="90.00"))
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "OVERLAP_VALUES_CONSISTENT_ONLY"


def test_no_overlapping_valid_settlements_or_candles_is_unassessed(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, _ = _client(new=_source(NEW, empty=True))
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "UNASSESSED_INSUFFICIENT_OVERLAP"
    assert result["comparison"]["funding"]["overlap_count"] == 0


def test_original_zip_hash_tampering_is_unassessed_not_stable(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, _ = _client(later_bytes=b"not the reviewed original ZIP")
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "UNASSESSED"
    assert result["comparison"] is None
    assert result["original_archive_sha256"][NEW] is not None


def test_zip_duplicate_and_surplus_file_fail_closed(monkeypatch):
    mod = _module(monkeypatch)
    broken = _zip(_source(NEW), malformed=True)
    client, verify, _ = _client()
    with client, pytest.raises(ValueError, match="duplicate, missing or extra"):
        mod.fetch_original_capture(
            NEW, hashlib.sha256(broken).hexdigest(),
            client=httpx.Client(transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content=broken)
            )),
        )


def test_missing_independent_release_audit_stops_before_downloading_originals(
    monkeypatch,
):
    mod = _module(monkeypatch)
    client, verify, requests = _client(audits=[_aud(OLD)])
    with client:
        result = _audit(mod, client, verify)
    assert result["status"] == "UNASSESSED"
    assert result["comparison"] is None
    assert len(requests) == 3
    assert all("/releases/download/" not in path for _, _, path in requests)


@pytest.mark.parametrize("old,new,when", [
    ("2026-10-22", "2026-10-23", NOW),
    (NEW, OLD, NOW),
    (OLD, OLD, NOW),
    (OLD, "2026-10-25", NOW),
    (OLD, NEW, datetime(2026, 10, 24, 0, 14, tzinfo=UTC)),
    (OLD, "2026-10-2x", NOW),
])
def test_invalid_pair_fails_before_network(monkeypatch, old, new, when):
    mod = _module(monkeypatch)
    client, verify, requests = _client()
    with client, pytest.raises(ValueError):
        mod.audit_pair(
            old, new, now=lambda: when,
            client=client, token="test-token", verify=verify,
        )
    assert not requests



def test_manual_workflow_is_read_only_without_a_new_market_capture(monkeypatch):
    _module(monkeypatch)
    workflow = (
        ROOT / ".github/workflows/audit-funding-original-overlap.yml"
    ).read_text()
    assert "\n  workflow_dispatch:" in workflow
    assert "\n  push:" in workflow
    assert "branches: [main]" in workflow
    assert "\n  schedule:" not in workflow
    assert "permissions:\n  contents: read\n  actions: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "scripts/audit_funding_source_revision.py" in workflow
    assert "if: always()" in workflow
    assert "if: failure()" in workflow
    assert "retention-days: 90" in workflow
    assert "acquisition_approved" in workflow
    assert "promotion_approved" in workflow
    for forbidden in (
        "gh release create", "gh release upload", "curl ",
        "capture_funding_preentry_source.py", "run_vps_funding_preentry.py",
        "api/v5/public/", "api/v5/market/",
        "contents: write", "actions: write",
    ):
        assert forbidden not in workflow



def test_realistic_current_utc_candle_progresses_from_open_to_confirmed(monkeypatch):
    """The first day's still-open 1Dutc candle normally confirms next day."""
    mod = _module(monkeypatch)
    first = _source(OLD)
    second = _source(NEW)
    current_day_open_ms = _ms("2026-10-23")
    first["spot_response"]["data"][1][0] = current_day_open_ms
    second["spot_response"]["data"][1][0] = current_day_open_ms
    first["spot_response"]["data"][1][8] = "0"
    second["spot_response"]["data"][1][8] = "1"
    # An unfinished candle's interim close can evolve before confirmation.
    first["spot_response"]["data"][1][4] = "91000"
    second["spot_response"]["data"][1][4] = "91500"
    client, verify, _ = _client(old=first, new=second)
    with client:
        report = _audit(mod, client, verify)
    assert report["status"] == "OVERLAP_VALUES_CONSISTENT_ONLY"
    assert report["comparison"]["spot"]["confirmed_close_overlap_count"] == 2
    assert report["comparison"]["spot"]["confirmation_state_advances"] == [
        "2026-10-23T00:00:00+00:00",
    ]
    assert report["comparison"]["spot"]["confirmation_state_regressions"] == []
    assert report["comparison"]["spot"]["confirmation_state_conflicts"] == []
    assert report["comparison"]["spot"]["confirmed_close_revisions"] == []
    assert report["point_in_time_publication_verified"] is False
    assert report["promotion_approved"] is False


def test_already_confirmed_candle_must_not_become_unconfirmed_later(monkeypatch):
    mod = _module(monkeypatch)
    client, verify, _ = _client(new=_source(NEW, confirmed="0"))
    with client:
        report = _audit(mod, client, verify)
    assert report["status"] == "SOURCE_REVISION_DETECTED"
    changed = report["comparison"]["spot"]
    assert changed["confirmation_state_regressions"] == [
        "2026-10-20T00:00:00+00:00",
    ]
    assert changed["confirmation_state_conflicts"] == changed[
        "confirmation_state_regressions"
    ]
    assert changed["confirmation_state_advances"] == []
    assert report["acquisition_approved"] is False
