"""No-network UTC missing-day Funding Release health and audit watch tests."""
from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/check_funding_release_watch.py"
DAY = "2026-10-23"
TAG = f"funding-vps-{DAY}"
PUBLISHED = "2026-10-23T00:00:15+00:00"
ZIP_SHA = "bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068"


def _watch(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_release_watch_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stamp(hour=1, minute=0):
    return datetime(2026, 10, 23, hour, minute, tzinfo=UTC)


def _release():
    return {
        "tag_name": TAG, "immutable": True, "published_at": PUBLISHED,
        "id": 1357, "draft": False,
    }


def _audit(*, state="completed", conclusion="success", tag=TAG, started="2026-10-23T00:00:17Z"):
    return {
        "id": 39875400476, "event": "release", "head_branch": tag,
        "name": "Audit Immutable VPS Funding Evidence Release",
        "created_at": started, "status": state, "conclusion": conclusion,
        "run_attempt": 1,
    }


def _verified(day, *, client):
    assert day == DAY
    assert isinstance(client, httpx.Client)
    return {
        "status": "github_immutable_release_metadata_and_offline_replay_only",
        "tag": TAG, "published_at": PUBLISHED, "archive_sha256": ZIP_SHA,
        "regime": "nonnegative_high_volatility",
    }


def _mock(*, release=None, audits=None, release_status=200, audit_status=200):
    if release is None:
        release = _release()
    if audits is None:
        audits = [_audit()]
    requests = []

    def handler(request: httpx.Request):
        requests.append((request.method, str(request.url)))
        assert request.method == "GET"
        if "/actions/workflows/" in str(request.url):
            return httpx.Response(audit_status, json={"workflow_runs": audits})
        if request.url.path.endswith("/releases/tags/" + TAG):
            return httpx.Response(release_status, json=release)
        return httpx.Response(404, json={"message": "Not Found"})

    return httpx.Client(transport=httpx.MockTransport(handler)), requests


def test_genuine_2026_10_23_real_release_success_and_audit(monkeypatch):
    mod = _watch(monkeypatch)
    with _mock()[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["status"] == "HEALTHY"
    assert result["days"][0]["status"] == mod.VALID_STATUS
    assert result["days"][0]["archive_sha256"] == ZIP_SHA
    assert result["days"][0]["audit_run_id"] == 39875400476
    assert result["days"][0]["github_hosted_preentry_source_verified"] is True
    assert result["days"][0]["github_release_attestation_verified"] is True
    for key in (
        "exchange_signed", "point_in_time_publication_verified",
        "acquisition_approved", "promotion_approved",
    ):
        assert result[key] is False
        assert result["days"][0][key] is False


def test_missing_published_release_fails_closed_after_entry(monkeypatch):
    mod = _watch(monkeypatch)
    with _mock(release_status=404)[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=lambda *a, **k: pytest.fail("cannot replay missing Release"),
        )
    rec = result["days"][0]
    assert result["status"] == "UNASSESSED"
    assert rec["status"] == "MISSING_PUBLISHED_RELEASE"
    assert rec["github_hosted_preentry_source_verified"] is False


@pytest.mark.parametrize("audit,expected", [
    ([], "AUDIT_MISSING"),
    ([_audit(state="queued", conclusion=None)], "AUDIT_PENDING"),
    ([_audit(state="in_progress", conclusion=None)], "AUDIT_PENDING"),
    ([_audit(state="completed", conclusion="failure")], "AUDIT_FAILED"),
    ([_audit(tag="diagnostic-funding-vps-2026-10-21")], "AUDIT_MISSING"),
    ([_audit(started="2026-10-23T00:00:11Z")], "UNASSESSED"),
])
def test_release_existence_does_not_imply_successful_independent_audit(
    monkeypatch, audit, expected,
):
    mod = _watch(monkeypatch)
    with _mock(audits=audit)[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["status"] == "UNASSESSED"
    assert result["days"][0]["status"] == expected
    assert result["days"][0]["github_release_attestation_verified"] is False


@pytest.mark.parametrize("failure", [
    "late", "altered-zip", "missing-asset", "not-immutable", "wrong-regime",
])
def test_invalid_release_metadata_or_replay_never_counts_as_healthy(monkeypatch, failure):
    mod = _watch(monkeypatch)

    def bad_verify(day, *, client):
        if failure == "late":
            raise ValueError("GitHub Release published too late for research entry")
        if failure == "altered-zip":
            raise ValueError("downloaded ZIP digest mismatched original GitHub asset")
        if failure == "missing-asset":
            raise ValueError("exactly two GitHub original assets are required")
        if failure == "not-immutable":
            raise ValueError("GitHub Release must be published and immutable")
        return {**_verified(day, client=client), "status": "UNASSESSED"}

    with _mock()[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=bad_verify,
        )
    assert result["days"][0]["status"] == "INVALID_RELEASE"
    assert result["status"] == "UNASSESSED"


@pytest.mark.parametrize("code", [401, 403, 429, 500, 502])
def test_api_outage_or_missing_permission_is_unassessed_not_no_release(monkeypatch, code):
    mod = _watch(monkeypatch)
    with _mock(audit_status=code)[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["days"][0]["status"] == "UNASSESSED"


@pytest.mark.parametrize("code", [401, 403, 429, 500])
def test_release_api_failure_is_not_misclassified_as_missing(monkeypatch, code):
    mod = _watch(monkeypatch)
    with _mock(release_status=code)[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["days"][0]["status"] == "UNASSESSED"


def test_malformed_release_identity_is_invalid(monkeypatch):
    mod = _watch(monkeypatch)
    with _mock(release={"tag_name": "diagnostic-2026-10-21"})[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["days"][0]["status"] == "INVALID_RELEASE"


def test_audit_transport_disconnect_is_not_misreported_as_missing(monkeypatch):
    mod = _watch(monkeypatch)
    def fail(request):
        raise httpx.ConnectError("simulated API offline", request=request)
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["days"][0]["status"] == "UNASSESSED"


def test_rollout_and_midnight_scheduling_boundaries(monkeypatch):
    mod = _watch(monkeypatch)
    assert mod.recent_completed_days(_stamp(0, 14), count=3) == []
    assert [d.isoformat() for d in mod.recent_completed_days(
        _stamp(0, 15), count=3
    )] == [DAY]
    days = mod.recent_completed_days(datetime(2026, 10, 25, 0, 41, tzinfo=UTC), count=3)
    assert [d.isoformat() for d in days] == [
        "2026-10-25", "2026-10-24", "2026-10-23",
    ]
    assert mod.recent_completed_days(
        datetime(2026, 10, 25, 0, 14, tzinfo=UTC), count=3
    )[0].isoformat() == "2026-10-24"
    with _mock()[0] as client:
        result = mod.watch(
            now=lambda: _stamp(0, 14), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["status"] == "UNASSESSED"
    assert result["days"][0]["status"] == "UNASSESSED"


@pytest.mark.parametrize("bad", ["2026-1-23", "2026-02-30", "today", "2026-10-23Z"])
def test_utc_day_input_must_be_canonical(monkeypatch, bad):
    mod = _watch(monkeypatch)
    with pytest.raises(ValueError):
        mod._day(bad)


def test_late_reviewer_finds_previous_days_without_new_market_capture(monkeypatch):
    mod = _watch(monkeypatch)
    days = mod.recent_completed_days(
        datetime(2026, 10, 26, 13, tzinfo=UTC), count=3
    )
    assert [x.isoformat() for x in days] == [
        "2026-10-26", "2026-10-25", "2026-10-24",
    ]
    assert mod._day("2026-10-23").isoformat() == DAY


def test_review_is_read_only_on_mock_http_transport(monkeypatch):
    mod = _watch(monkeypatch)
    client, calls = _mock()
    with client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["status"] == "HEALTHY"
    assert len(calls) == 2
    assert all(method == "GET" for method, _ in calls)
    assert any("/actions/workflows/" in url for _, url in calls)
    assert any("/releases/tags/" in url for _, url in calls)


def test_report_shape_is_json_serializable_and_always_nonpromotion(monkeypatch):
    mod = _watch(monkeypatch)
    with _mock(release_status=404)[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only", entry_day=DAY,
            verify=_verified,
        )
    encoded = json.dumps(result, sort_keys=True)
    assert json.loads(encoded)["days"][0]["status"] == "MISSING_PUBLISHED_RELEASE"
    assert json.loads(encoded)["promotion_approved"] is False



def _daily_record(mod, day, regime, *, status=None, attested=True):
    if status is None:
        status = mod.VALID_STATUS
    return {
        "entry_market_date": day,
        "status": status,
        "regime": regime,
        "github_hosted_preentry_source_verified": True,
        "github_release_attestation_verified": attested,
    }


def test_audited_release_regime_inventory_has_fixed_2x2_and_dates(monkeypatch):
    mod = _watch(monkeypatch)
    records = [
        _daily_record(mod, "2026-10-24", "negative_high_volatility"),
        _daily_record(mod, "2026-10-23", "nonnegative_high_volatility"),
    ]
    coverage = mod.summarize_audited_regimes(records)
    assert coverage["status"] == "AUDITED_GITHUB_CUSTODY_ONLY"
    assert coverage["checked_day_count"] == 2
    assert coverage["github_audited_day_count"] == 2
    assert coverage["non_audited_days"] == []
    assert coverage["strata"]["negative_high_volatility"] == {
        "count": 1, "dates": ["2026-10-24"],
    }
    assert coverage["strata"]["nonnegative_high_volatility"] == {
        "count": 1, "dates": ["2026-10-23"],
    }
    assert coverage["empty_strata"] == [
        "negative_low_volatility", "nonnegative_low_volatility",
    ]
    assert len(coverage["strata"]) == 4
    assert coverage["market_wide_opportunity_arrival_rate"] is None
    for flag in ("exchange_signed", "point_in_time_publication_verified",
                 "acquisition_approved", "promotion_approved"):
        assert coverage[flag] is False


def test_failed_and_missing_release_are_not_fabricated_as_audited_days(monkeypatch):
    mod = _watch(monkeypatch)
    records = [
        _daily_record(mod, "2026-10-25", "negative_low_volatility",
                      status="AUDIT_FAILED", attested=False),
        _daily_record(mod, "2026-10-24", "nonnegative_low_volatility",
                      status="MISSING_PUBLISHED_RELEASE", attested=False),
        _daily_record(mod, "2026-10-23", "nonnegative_high_volatility"),
    ]
    coverage = mod.summarize_audited_regimes(records)
    assert coverage["status"] == "PARTIAL"
    assert coverage["checked_day_count"] == 3
    assert coverage["github_audited_day_count"] == 1
    assert coverage["strata"]["negative_low_volatility"]["count"] == 0
    assert coverage["strata"]["nonnegative_low_volatility"]["count"] == 0
    assert coverage["non_audited_days"] == [
        {"date": "2026-10-24", "status": "MISSING_PUBLISHED_RELEASE"},
        {"date": "2026-10-25", "status": "AUDIT_FAILED"},
    ]


@pytest.mark.parametrize("records", [
    [
        {"entry_market_date": "2026-10-23", "status": "UNKNOWN"},
    ],
    [
        {"entry_market_date": "2026-10-23", "status": "AUDIT_FAILED"},
        {"entry_market_date": "2026-10-23", "status": "AUDIT_FAILED"},
    ],
    [
        {"entry_market_date": "2026-2-03", "status": "AUDIT_FAILED"},
    ],
])
def test_regime_inventory_rejects_unknown_duplicate_or_noncanonical_days(
    monkeypatch, records,
):
    mod = _watch(monkeypatch)
    with pytest.raises(ValueError):
        mod.summarize_audited_regimes(records)


@pytest.mark.parametrize("regime,attested", [
    ("negative_below_volatility", True),
    ("nonnegative_high_volatility", False),
    (None, True),
])
def test_no_healthy_watch_with_untrusted_or_unknown_verified_regime(
    monkeypatch, regime, attested,
):
    mod = _watch(monkeypatch)

    def verified(day, *, client):
        return {**_verified(day, client=client), "regime": regime}

    with _mock()[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=verified,
        )
    if attested:
        assert result["status"] == "UNASSESSED"
        assert result["regime_coverage"]["status"] == "UNASSESSED"
    else:
        result["days"][0]["github_release_attestation_verified"] = False
        with pytest.raises(ValueError, match="audited original"):
            mod.summarize_audited_regimes(result["days"])
    assert result["point_in_time_publication_verified"] is False
    assert result["acquisition_approved"] is False


def test_watch_success_includes_bounded_regime_inventory(monkeypatch):
    mod = _watch(monkeypatch)
    with _mock()[0] as client:
        result = mod.watch(
            now=lambda: _stamp(), client=client, token="test-only",
            entry_day=DAY, verify=_verified,
        )
    assert result["status"] == "HEALTHY"
    inv = result["regime_coverage"]
    assert inv["github_audited_day_count"] == 1
    assert inv["strata"]["nonnegative_high_volatility"]["dates"] == [DAY]
    assert inv["empty_strata"] == [
        "negative_low_volatility", "negative_high_volatility",
        "nonnegative_low_volatility",
    ]
