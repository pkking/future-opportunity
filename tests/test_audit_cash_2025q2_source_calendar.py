from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/audit_cash_2025q2_source_calendar.py"
spec = importlib.util.spec_from_file_location("cash_q2_calendar_audit", SCRIPT)
assert spec and spec.loader
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def write_archive(tmp_path, raw, report):
    output = tmp_path / "proof.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("catalog-raw-api-capture.json", json.dumps(raw))
        z.writestr("source-calendar-report.json", json.dumps(report))
    return output, hashlib.sha256(output.read_bytes()).hexdigest()


def fixture_payloads():
    days = verify.expected_dates()
    raw = {}
    rows = []
    for day in days:
        row = {"market_date": day}
        ts = str(int(datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=UTC).timestamp() * 1000))
        for kind in ("FUTURES", "SPOT"):
            filename = (
                f"BTC-USDT-futureschain-L2orderbook-400lv-{day}.tar.gz"
                if kind == "FUTURES" else f"BTC-USDT-L2orderbook-400lv-{day}.tar.gz"
            )
            query = {"module": "4", "instType": kind, "dateAggrType": "daily", "begin": ts, "end": ts}
            query["instFamilyList" if kind == "FUTURES" else "instIdList"] = "BTC-USDT"
            response = {"code": "0", "data": [{"dateAggrType": "daily", "details": [{
                "instType": kind, "instFamily": "BTC-USDT" if kind == "FUTURES" else "",
                "instId": "BTC-USDT" if kind == "SPOT" else "",
                "dateRangeStart": ts, "dateRangeEnd": ts,
                "groupDetails": [{"dateTs": ts, "filename": filename,
                                  "url": f"https://static.okx.com/cdn/okx/match/orderbook/L2/400lv/daily/{day.replace('-', '')}/{filename}"}],
            }]}]}
            sha = verify.canonical_sha256(response)
            raw[f"{day}/{kind}"] = {"query": query, "response": response, "sha256": sha}
            row[kind.lower()] = {
                "status": "unique_catalog_archive_only", "candidate_count": 1,
                "archive_filename": filename, "response_sha256": sha,
                "contract_member_inside_futures_archive_verified": False,
                "sampled_book_verified": False,
            }
        rows.append(row)
    report = {
        "schema_version": 1, "evidence_type": "cash_2025q2_retrospective_daily_catalog_population",
        "requested_calendar_days": 90, "source_catalog_days": 90,
        "paired_catalog_day_count": 90, "paired_catalog_dates": list(days),
        "query_error_days": [], "source_population_complete": True,
        "futures_member_identified_per_candidate_day": False,
        "l2_sampled_per_candidate_day": False, "historical_selection_frozen": False,
        "sampled_economic_returns_inspected": False, "research_only": True,
        "acquisition_approved": False, "promotion_approved": False,
        "observations": rows,
    }
    return raw, report


def test_complete_synthetic_offline_audit(tmp_path):
    raw, report = fixture_payloads()
    archive, digest = write_archive(tmp_path, raw, report)
    result = verify.audit(archive, digest)
    assert result["verified_calendar_dates"] == 90
    assert result["verified_raw_api_responses"] == 180
    assert result["exact_future_contract_membership_verified"] is False
    assert result["acquisition_approved"] is False


@pytest.mark.parametrize("tamper", [
    lambda raw, report: raw.pop("2025-03-29/FUTURES"),
    lambda raw, report: raw["2025-03-29/FUTURES"]["response"].update({"code": "1"}),
    lambda raw, report: raw["2025-03-29/FUTURES"]["query"].update({"begin": "0"}),
    lambda raw, report: report["observations"][0]["futures"].update({"sampled_book_verified": True}),
    lambda raw, report: report.update({"historical_selection_frozen": True}),
    lambda raw, report: report["paired_catalog_dates"].pop(),
    lambda raw, report: raw["2025-03-29/FUTURES"]["response"]["data"][0]["details"][0]["groupDetails"][0].update({"url": "https://example.com/bad.tar.gz"}),
    lambda raw, report: report.update({"promotion_approved": True}),
])
def test_fails_closed_on_tampering(tmp_path, tamper):
    raw, report = fixture_payloads()
    tamper(raw, report)
    archive, digest = write_archive(tmp_path, raw, report)
    with pytest.raises(ValueError):
        verify.audit(archive, digest)


def test_wrong_expected_digest_rejected(tmp_path):
    raw, report = fixture_payloads()
    archive, _ = write_archive(tmp_path, raw, report)
    with pytest.raises(ValueError, match="ZIP digest"):
        verify.audit(archive, "0" * 64)


def test_archive_must_not_contain_extra_files(tmp_path):
    raw, report = fixture_payloads()
    archive, digest = write_archive(tmp_path, raw, report)
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr("unexpected.txt", "extra")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="exactly the two"):
        verify.audit(archive, digest)
