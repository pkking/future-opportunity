"""Raw Cash L2 failure evidence must be bounded, replayable and fail-closed."""
from __future__ import annotations

import hashlib
import io
import json
import runpy
import shutil
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
