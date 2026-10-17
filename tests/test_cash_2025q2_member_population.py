from __future__ import annotations

import io
import importlib.util
import sys
import tarfile
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "cash_q2_futures_member_census", ROOT / "scripts/probe_cash_2025q2_members.py"
)
assert spec is not None and spec.loader is not None
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)


def fixture_archive(tmp_path, day: str, future_ids: tuple[str, ...]) -> Path:
    path = tmp_path / "source.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for future_id in future_ids:
            content = b"synthetic-non-economics-only"
            name = f"{future_id}-L2orderbook-400lv-{day}.data"
            item = tarfile.TarInfo(name)
            item.size = len(content)
            archive.addfile(item, io.BytesIO(content))
    return path


def test_ninety_day_population_is_partitioned_without_gaps():
    all_dates = [day for index in range(9) for day in census.dates_for_batch(index)]
    assert len(all_dates) == len(set(all_dates)) == 90
    assert all_dates[0] == "2025-03-29"
    assert all_dates[-1] == "2025-06-26"
    with pytest.raises(ValueError):
        census.dates_for_batch(-1)
    with pytest.raises(ValueError):
        census.dates_for_batch(9)


def test_source_member_identities_only(tmp_path):
    p = fixture_archive(tmp_path, "2025-06-12", ("BTC-USDT-250627", "BTC-USDT-250926"))
    observed = census.verify_members(p, "2025-06-12")
    assert observed["member_status"] == "identity_verified"
    assert observed["exact_contract_member"] == "BTC-USDT-250627-L2orderbook-400lv-2025-06-12.data"
    assert observed["matching_exact_contract_member_count"] == 1
    assert observed["member_instrument_ids"] == ["BTC-USDT-250627", "BTC-USDT-250926"]
    with pytest.raises(ValueError, match="market date"):
        census.verify_members(p, "2025-06-13")


def test_other_contract_is_unavailable_without_guessing(tmp_path):
    p = fixture_archive(tmp_path, "2025-05-01", ("BTC-USDT-250926",))
    observed = census.verify_members(p, "2025-05-01")
    assert observed["member_status"] == "unavailable"
    assert observed["exact_contract_member"] is None


def test_empty_or_broken_gzip_cannot_imply_unavailable(tmp_path):
    p = fixture_archive(tmp_path, "2025-06-12", ())
    with pytest.raises(ValueError, match="empty"):
        census.verify_members(p, "2025-06-12")
    p.write_bytes(b"invalid tar")
    with pytest.raises(tarfile.TarError):
        census.verify_members(p, "2025-06-12")


def test_duplicate_exact_member_is_an_error(tmp_path):
    p = tmp_path / "duplicate.tar.gz"
    with tarfile.open(p, "w:gz") as archive:
        for _ in range(2):
            contents = b"test"
            item = tarfile.TarInfo("BTC-USDT-250627-L2orderbook-400lv-2025-06-12.data")
            item.size = len(contents)
            archive.addfile(item, io.BytesIO(contents))
    with pytest.raises(ValueError, match="duplicate"):
        census.verify_members(p, "2025-06-12")


def test_streaming_uses_bounded_download_and_hash(tmp_path, monkeypatch):
    contents = b"source-only"
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=contents, request=request)
    ))
    try:
        digest, size = census.stream_archive(client, "https://static.okx.com/source", tmp_path / "test")
        assert size == len(contents)
        assert len(digest) == 64
        monkeypatch.setattr(census, "MAX_ARCHIVE_BYTES", len(contents) - 1)
        with pytest.raises(ValueError, match="exceeds"):
            census.stream_archive(client, "https://static.okx.com/source", tmp_path / "too-big")
    finally:
        client.close()


def test_failure_is_explicit_error_not_missing_market_day(tmp_path):
    def failure(request):
        return httpx.Response(503, request=request)
    client = httpx.Client(transport=httpx.MockTransport(failure))
    raw = {"2025-06-12/FUTURES": {
        "response": {"data": [{"details": [{"groupDetails": [{
            "url": "https://static.okx.com/source",
        }]}]}]},
        "sha256": "0" * 64,
    }}
    try:
        record = census.inspect_day(client, "2025-06-12", raw)
    finally:
        client.close()
    assert record["member_status"] == "error"
    assert record["error_type"] == "HTTPStatusError"
    assert record["archive_sha256"] is None
    assert record["member_identity_verified"] is False
    assert record["acquisition_approved"] is False


def test_batch_counts_preserve_error_status(monkeypatch):
    def pretend(client, day, raw):
        return {"market_date": day,
                "member_status": "error" if day.endswith("-29") else "unavailable",
                "member_identity_verified": False}
    monkeypatch.setattr(census, "inspect_day", pretend)
    report = census.census_batch(object(), {}, 0, source_zip_sha256="a" * 64)
    assert report["complete"] is False
    assert report["status_counts"]["error"] == 1
    assert report["status_counts"]["unavailable"] == 9
    assert report["sample_selection_frozen"] is False
    assert report["economic_returns_evaluated"] is False
    assert report["promotion_approved"] is False
