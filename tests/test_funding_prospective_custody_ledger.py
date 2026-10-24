"""Offline strict tests for longitudinal GitHub Funding source custody coverage."""
from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/report_funding_prospective_custody_ledger.py"
START = "2026-10-23"
END = "2026-10-24"
NOW = datetime(2026, 10, 24, 6, tzinfo=UTC)


def _module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("funding_custody_ledger_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _audit(day):
    return {
        "id": 900 if day == START else 901,
        "event": "release",
        "head_branch": f"funding-vps-{day}",
        "name": "Audit Immutable VPS Funding Evidence Release",
        "created_at": f"{day}T00:00:17Z",
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
    }


def _verified(day, *, client):
    assert isinstance(client, httpx.Client)
    return {
        "status": "github_immutable_release_metadata_and_offline_replay_only",
        "tag": f"funding-vps-{day}",
        "published_at": f"{day}T00:00:15Z",
        "archive_sha256": "a" * 64,
        "regime": "negative_high_volatility" if day == START
                  else "nonnegative_low_volatility",
    }


def _mock(*, missing=None, audits=None, audit_error=None):
    requested = []
    if audits is None:
        audits = [_audit(END), _audit(START)]
    def handler(request):
        requested.append((request.method, str(request.url)))
        assert request.method == "GET", "GitHub monitor must never write"
        assert request.url.host == "api.github.com", "No exchange API allowed"
        if "/actions/workflows/" in request.url.path:
            if audit_error is not None:
                return httpx.Response(audit_error, json={"message": "not available"})
            return httpx.Response(200, json={"workflow_runs": audits})
        if "/releases/tags/" in request.url.path:
            day = request.url.path[-10:]
            if day == missing:
                return httpx.Response(404, json={"message": "Not Found"})
            return httpx.Response(200, json={
                "tag_name": f"funding-vps-{day}",
                "immutable": True, "draft": False,
                "published_at": f"{day}T00:00:15Z",
            })
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler)), requested


def test_two_real_day_ids_are_inventoried_without_source_promotion(monkeypatch):
    mod = _module(monkeypatch)
    with _mock()[0] as client:
        report = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic-test-token", verify=_verified,
        )
    assert report["status"] == "AUDITED_GITHUB_CUSTODY_ONLY"
    assert report["checked_day_count"] == 2
    assert report["github_audited_day_count"] == 2
    assert len(report["days"]) == 2
    assert report["regime_coverage"]["strata"]["negative_high_volatility"] == {
        "count": 1, "dates": [START],
    }
    assert report["regime_coverage"]["strata"]["nonnegative_low_volatility"] == {
        "count": 1, "dates": [END],
    }
    assert report["regime_coverage"]["empty_strata"] == [
        "negative_low_volatility", "nonnegative_high_volatility",
    ]
    for flag in (
        "exchange_signed", "point_in_time_publication_verified",
        "acquisition_approved", "promotion_approved",
    ):
        assert report[flag] is False
        assert report["regime_coverage"][flag] is False
    assert report["market_wide_opportunity_arrival_rate"] is None
    assert json.loads(json.dumps(report))["checked_day_count"] == 2


def test_missing_day_and_missing_independent_audit_fail_closed(monkeypatch):
    mod = _module(monkeypatch)
    with _mock(missing=END)[0] as client:
        report = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic", verify=_verified,
        )
    assert report["status"] == "UNASSESSED"
    assert report["github_audited_day_count"] == 1
    assert report["days"][1]["status"] == "MISSING_PUBLISHED_RELEASE"
    assert report["regime_coverage"]["non_audited_days"] == [
        {"date": END, "status": "MISSING_PUBLISHED_RELEASE"},
    ]
    with _mock(audits=[_audit(START)])[0] as client:
        unreviewed = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic", verify=_verified,
        )
    assert unreviewed["days"][1]["status"] == "AUDIT_MISSING"
    assert unreviewed["status"] == "UNASSESSED"


@pytest.mark.parametrize("error", [401, 403, 429, 500])
def test_api_failure_is_unassessed_for_all_days(monkeypatch, error):
    mod = _module(monkeypatch)
    client, calls = _mock(audit_error=error)
    with client:
        report = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic", verify=_verified,
        )
    assert report["status"] == "UNASSESSED"
    assert [x["status"] for x in report["days"]] == ["UNASSESSED", "UNASSESSED"]
    assert report["github_audited_day_count"] == 0
    assert len(calls) == 1


@pytest.mark.parametrize("start,end,now", [
    ("2026-10-22", "2026-10-23", NOW),
    (END, START, NOW),
    ("2026-10-23", "2027-01-22", datetime(2027, 2, 1, tzinfo=UTC)),
    ("2026-10-23", END, datetime(2026, 10, 24, 0, 14, tzinfo=UTC)),
    ("2026-10-23", "2026-10-2x", NOW),
    (START, START, datetime(2026, 10, 23),),
])
def test_rejects_noncanonical_future_or_too_large_before_network(monkeypatch, start, end, now):
    mod = _module(monkeypatch)
    client, calls = _mock()
    with client, pytest.raises(ValueError):
        mod.build_report(start, end, now=lambda: now, client=client, token="synthetic")
    assert calls == []


def test_utc_deadline_and_exact_90_days(monkeypatch):
    mod = _module(monkeypatch)
    assert mod.eligible_days(START, START, datetime(2026, 10, 23, 0, 15, tzinfo=UTC)) == [
        datetime(2026, 10, 23, tzinfo=UTC).date(),
    ]
    last = datetime(2026, 10, 23, tzinfo=UTC).date() + timedelta(days=89)
    days = mod.eligible_days(START, last.isoformat(), datetime(2027, 2, 1, tzinfo=UTC))
    assert len(days) == 90
    assert days[0].isoformat() == START
    assert days[-1] == last


def test_paginated_audit_history_does_not_discard_older_matching_run(monkeypatch):
    mod = _module(monkeypatch)
    seen = []
    page_one = [
        {**_audit(END), "id": i, "created_at": "2026-10-24T01:00:00Z"}
        for i in range(100)
    ]
    page_two = [
        _audit(START),
        {**_audit(START), "id": 1, "created_at": "2026-10-22T23:00:00Z"},
    ]

    def handler(request):
        seen.append((request.method, str(request.url)))
        assert request.method == "GET"
        page = request.url.params.get("page")
        return httpx.Response(200, json={
            "workflow_runs": page_one if page == "1" else page_two,
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        audits = mod.fetch_window_audits(
            client, "synthetic", start_day=datetime(2026, 10, 23).date(),
        )
    assert len(audits) == 102
    assert any(x["id"] == 900 for x in audits)
    assert len(seen) == 2
    assert all(method == "GET" for method, _ in seen)


def test_unsorted_audit_history_fails_closed(monkeypatch):
    mod = _module(monkeypatch)
    audits = [
        _audit(START),
        _audit(END),
    ]
    client, _ = _mock(audits=audits)
    with client:
        report = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic", verify=_verified,
        )
    assert report["status"] == "UNASSESSED"
    assert all(x["status"] == "UNASSESSED" for x in report["days"])


def test_read_only_api_calls_never_contact_exchange(monkeypatch):
    mod = _module(monkeypatch)
    client, calls = _mock()
    with client:
        report = mod.build_report(
            START, END, now=lambda: NOW, client=client,
            token="synthetic", verify=_verified,
        )
    assert report["status"] == "AUDITED_GITHUB_CUSTODY_ONLY"
    assert len(calls) == 3
    assert all(method == "GET" and url.startswith("https://api.github.com/")
               for method, url in calls)



def test_audit_run_history_beyond_bounded_pages_is_unassessed(monkeypatch):
    mod = _module(monkeypatch)
    calls = []
    # All 20 pages contain only newer records; pretending that older runs
    # were absent would silently erase potentially verified historical days.
    newest = [
        {**_audit(END), "id": i, "created_at": "2026-10-24T01:00:00Z"}
        for i in range(100)
    ]
    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert "/actions/workflows/" in request.url.path
        return httpx.Response(200, json={"workflow_runs": newest})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = mod.build_report(
            START, END, now=lambda: NOW,
            client=client, token="synthetic", verify=_verified,
        )
    assert len(calls) == mod.MAX_AUDIT_PAGES
    assert report["status"] == "UNASSESSED"
    assert report["github_audited_day_count"] == 0
    assert all(item["status"] == "UNASSESSED" for item in report["days"])


def test_source_history_workflow_is_opt_in_read_only(monkeypatch):
    _module(monkeypatch)
    policy = (ROOT / ".github/workflows/review-funding-prospective-custody.yml").read_text()
    assert "\n  workflow_dispatch:" in policy
    assert "\n  push:" in policy
    assert "\n  schedule:" not in policy
    assert "contents: read" in policy and "actions: read" in policy
    assert "persist-credentials: false" in policy
    assert "scripts/report_funding_prospective_custody_ledger.py" in policy
    assert "Upload derived custody report" in policy
    assert "if: always()" in policy
    assert "acquisition_approved" in policy and "promotion_approved" in policy
    assert "gh release create" not in policy
    assert "curl " not in policy
    assert "api/v5/" not in policy
