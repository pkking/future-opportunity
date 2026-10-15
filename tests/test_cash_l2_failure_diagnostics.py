"""Raw Cash L2 failure evidence must be bounded, replayable and fail-closed."""
from __future__ import annotations

import hashlib
import io
import json
import runpy
import shutil
from decimal import Decimal
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_sampled_archive,
)
from future_opportunity.adapters.historical.okx_l2_diagnostics import (
    inspect_first_l2_record,
)
from future_opportunity.backtest.model import HistoricalInstrumentMetadata


ROOT = Path(__file__).parents[1]
PREPARER = ROOT / "scripts/prepare_okx_cash_and_carry_fixture.py"
WORKFLOW = ROOT / ".github/workflows/prepare-cash-historical-fixture.yml"
STAMP = datetime(2025, 7, 4, 0, 15, tzinfo=UTC)


def archive_with_bad_first_price(tmp_path: Path) -> tuple[Path, bytes]:
    raw_line = json.dumps(
        {
            "instId": "BTC-USDT",
            "action": "snapshot",
            "ts": str(int(STAMP.timestamp() * 1000)),
            "bids": [["0", "1", "1"], ["100000", "2", "1"]],
            "asks": [["100001", "3", "2"]],
        },
        separators=(",", ":"),
    ).encode() + b"\n"
    archive_path = tmp_path / "spot-example.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        member = tarfile.TarInfo("BTC-USDT-L2orderbook-400lv-2025-07-04.data")
        member.size = len(raw_line)
        tar.addfile(member, io.BytesIO(raw_line))
    return archive_path, raw_line


def test_first_record_diagnostic_identifies_invalid_level_without_repair(
    tmp_path: Path,
) -> None:
    archive, first_line = archive_with_bad_first_price(tmp_path)
    source = archive.read_bytes()
    member = "BTC-USDT-L2orderbook-400lv-2025-07-04.data"

    view = inspect_first_l2_record(
        archive, member_name=member, expected_instrument_id="BTC-USDT",
        component="entry_spot", sample_at=STAMP.isoformat(),
        raw_sha256=hashlib.sha256(source).hexdigest(),
        downloaded_bytes=len(source),
    )
    assert view["evidence_type"] == "okx_l2_first_record_diagnostic"
    assert view["first_line_sha256"] == hashlib.sha256(first_line).hexdigest()
    assert view["levels"]["bids"]["count"] == 2
    assert view["levels"]["bids"]["first_three_levels"][0] == ["0", "1", "1"]
    assert view["actual_instrument_id"] == "BTC-USDT"
    assert view["source_url_recorded"] is False
    assert view["normalization_succeeded"] is False

    with pytest.raises(ValueError, match="historical price must be positive"):
        list(
            iter_okx_l2_sampled_archive(
                archive, instrument_type="SPOT",
                expected_instrument_id="BTC-USDT", start=STAMP, end=STAMP,
                cadence=timedelta(minutes=15),
            )
        )


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not json\n",
        b" " * (128 * 1024 + 20) + b"\n",
    ],
)
def test_diagnostic_fails_closed_on_empty_invalid_or_oversize(
    tmp_path: Path, payload: bytes,
) -> None:
    archive = tmp_path / "bad.tar.gz"
    member = "BTC-USDT-L2orderbook-400lv-2025-07-04.data"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo(member)
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises((ValueError, json.JSONDecodeError)):
        inspect_first_l2_record(
            archive, member_name=member, expected_instrument_id="BTC-USDT",
            component="entry_spot", sample_at=STAMP.isoformat(),
            raw_sha256="f" * 64, downloaded_bytes=archive.stat().st_size,
        )


def test_preparer_writes_failed_diagnostic_without_masking_error(
    tmp_path: Path,
) -> None:
    archive, _ = archive_with_bad_first_price(tmp_path)
    module = runpy.run_path(str(PREPARER))
    prepare_component = module["prepare_component"]
    environment = prepare_component.__globals__
    environment["OUTPUT"] = tmp_path / "output"
    environment["catalog"] = lambda *_args: [
        SimpleNamespace(
            filename="spot-from-official-catalog.tar.gz",
            url="https://example.com/signed-url?token=NEVER-STORE-ME",
            instrument_id="BTC-USDT", instrument_family="",
        )
    ]

    def stub_download(_client: object, _url: str, destination: Path) -> tuple[str, int]:
        shutil.copyfile(archive, destination)
        data = destination.read_bytes()
        return hashlib.sha256(data).hexdigest(), len(data)

    environment["download"] = stub_download
    with pytest.raises(ValueError, match="historical price must be positive"):
        prepare_component(
            object(), tmp_path, name="entry_spot", sample_at=STAMP,
            instrument_type="SPOT",
        )

    output = environment["OUTPUT"] / "diagnostics" / "entry_spot.json"
    report = json.loads(output.read_text())
    assert report["component"] == "entry_spot"
    assert report["normalization_error"]["type"] == "ValueError"
    assert report["first_line_sha256"]
    assert report["levels"]["bids"]["first_three_levels"][0][0] == "0"
    assert "NEVER-STORE-ME" not in output.read_text()
    assert "signed-url" not in output.read_text()
    normalized = environment["OUTPUT"] / "entry_spot.jsonl"
    assert not normalized.exists() or not normalized.read_text()


def test_diagnostic_probe_failure_preserves_primary_normalization_error(
    tmp_path: Path,
) -> None:
    archive, _ = archive_with_bad_first_price(tmp_path)
    module = runpy.run_path(str(PREPARER))
    fn = module["prepare_component"]
    glob = fn.__globals__
    glob["OUTPUT"] = tmp_path / "output"
    glob["catalog"] = lambda *_args: [
        SimpleNamespace(
            filename="sample.tar.gz", url="https://example.org/raw",
            instrument_id="BTC-USDT", instrument_family="",
        )
    ]

    def copy_download(_client: object, _url: str, path: Path) -> tuple[str, int]:
        shutil.copyfile(archive, path)
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest(), len(data)

    glob["download"] = copy_download

    def fail_probe(*_args: object, **_kwargs: object) -> dict:
        raise RuntimeError("probe unavailable")

    glob["inspect_first_l2_record"] = fail_probe
    with pytest.raises(ValueError, match="historical price must be positive"):
        fn(object(), tmp_path, name="entry_spot", sample_at=STAMP,
           instrument_type="SPOT")

    report = json.loads(
        (glob["OUTPUT"] / "diagnostics" / "entry_spot.json").read_text()
    )
    assert report["probe_error"] == "probe unavailable"
    assert report["normalization_error"]["type"] == "ValueError"


def test_workflow_uploads_failure_diagnostics_and_remains_read_only() -> None:
    text = WORKFLOW.read_text()
    assert "if: always()" in text
    assert "cash-l2-diagnostics-" in text
    assert "artifacts/cash-historical-fixture/diagnostics/*.json" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "gh pr create" not in text



def test_deep_400_level_futures_snapshot_reports_offending_indices_bounded(
    tmp_path: Path,
) -> None:
    """The initial three prices may be valid even when deeper levels are not."""
    bids = [
        [str(110000 - index), "0.02", "1"] for index in range(400)
    ]
    asks = [
        [str(110001 + index), "0.03", "2"] for index in range(400)
    ]
    for index in range(380, 392):
        bids[index] = ["0", "0", "0"]
    asks[399] = ["-1", "2.28", "1"]

    raw = (
        json.dumps(
            {
                "instId": "BTC-USDT-250926",
                "action": "snapshot",
                "ts": str(int(STAMP.timestamp() * 1000)),
                "bids": bids,
                "asks": asks,
            }
        ) + "\n"
    ).encode()
    member_name = "BTC-USDT-250926-L2orderbook-400lv-2025-07-04.data"
    path = tmp_path / "BTC-USDT-futureschain-L2orderbook-400lv-2025-07-04.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(member_name)
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))

    data = path.read_bytes()
    view = inspect_first_l2_record(
        path, member_name=member_name,
        expected_instrument_id="BTC-USDT-250926",
        component="entry_future", sample_at=STAMP.isoformat(),
        raw_sha256=hashlib.sha256(data).hexdigest(),
        downloaded_bytes=len(data),
    )
    assert view["first_line_sha256"] == hashlib.sha256(raw).hexdigest()
    bid_report = view["levels"]["bids"]
    ask_report = view["levels"]["asks"]
    assert bid_report["count"] == 400
    assert ask_report["count"] == 400
    assert bid_report["first_three_levels"][0][0] == "110000"
    assert bid_report["price_anomaly_counts"]["nonpositive_price"] == 12
    assert ask_report["price_anomaly_counts"]["nonpositive_price"] == 1
    assert bid_report["price_anomaly_example_limit"] == 8
    assert len(bid_report["first_price_anomalies"]) == 8
    assert bid_report["first_price_anomalies"][0] == {
        "level_index_zero_based": 380,
        "reason": "nonpositive_price",
        "raw_level": ["0", "0", "0"],
    }
    assert ask_report["first_price_anomalies"] == [{
        "level_index_zero_based": 399,
        "reason": "nonpositive_price",
        "raw_level": ["-1", "2.28", "1"],
    }]
    assert len(json.dumps(view)) < 5500

    # The new diagnostic does not modify or bypass normal replay.
    with pytest.raises(ValueError, match="historical price must be positive"):
        list(iter_okx_l2_sampled_archive(
            path, instrument_type="FUTURES",
            expected_instrument_id="BTC-USDT-250926", start=STAMP, end=STAMP,
            cadence=timedelta(minutes=15),
            metadata=HistoricalInstrumentMetadata(
                instrument_id="BTC-USDT-250926",
                instrument_family="BTC-USDT",
                instrument_type="FUTURES",
                contract_value=Decimal("0.01"),
                contract_multiplier=Decimal(1),
                contract_value_currency="BTC",
                settlement_currency="USDT",
                list_time=None,
                expiry_time=STAMP + timedelta(days=80),
            ),
        ))


def test_invalid_price_category_classification_and_value_bound() -> None:
    from future_opportunity.adapters.historical.okx_l2_diagnostics import (
        _bounded_level, _level_price_anomaly,
    )

    assert _level_price_anomaly(["0", "0", "0"]) == "nonpositive_price"
    assert _level_price_anomaly(["-1", "0", "0"]) == "nonpositive_price"
    assert _level_price_anomaly(["NaN", "0", "0"]) == "nonfinite_price"
    assert _level_price_anomaly(["Infinity", "0", "0"]) == "nonfinite_price"
    assert _level_price_anomaly(["not-a-price", "0", "0"]) == "invalid_price"
    assert _level_price_anomaly([0, "0", "0"]) == "invalid_price"
    assert _level_price_anomaly(["100", "0"]) == "invalid_level_shape"
    assert _level_price_anomaly(["100", "0", "0"]) is None
    assert _bounded_level(["4" * 500, "0", "0"])[0].endswith("[truncated]")
    assert len(_bounded_level(["4" * 500, "0", "0"])[0]) < 120
