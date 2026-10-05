from __future__ import annotations

import io
import json
import tarfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_archive,
    iter_okx_l2_jsonl,
)
from future_opportunity.backtest.model import HistoricalInstrumentMetadata


def line(
    *,
    action: str,
    ts: str,
    bids: list[list[str]],
    asks: list[list[str]],
    instrument_id: str = "BTC-USDT",
) -> str:
    return json.dumps(
        {
            "instId": instrument_id,
            "action": action,
            "ts": ts,
            "bids": bids,
            "asks": asks,
        }
    )


def derivative_metadata(
    *,
    currency: str = "BTC",
) -> HistoricalInstrumentMetadata:
    return HistoricalInstrumentMetadata(
        instrument_id="BTC-USDT-SWAP",
        instrument_family="BTC-USDT",
        instrument_type="SWAP",
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal(1),
        contract_value_currency=currency,
        settlement_currency="USDT",
        list_time=datetime(2025, 1, 1, tzinfo=UTC),
        expiry_time=None,
    )


def test_spot_snapshot_and_updates_reconstruct_canonical_book() -> None:
    observations = list(
        iter_okx_l2_jsonl(
            [
                line(
                    action="snapshot",
                    ts="1760000000000",
                    bids=[["100", "2", "3"], ["99", "4", "2"]],
                    asks=[["101", "3", "4"], ["102", "5", "1"]],
                ),
                line(
                    action="update",
                    ts="1760000000100",
                    bids=[["100", "0", "0"], ["100.5", "1.5", "2"]],
                    asks=[["101", "2.5", "3"]],
                ),
            ],
            instrument_type="SPOT",
            expected_instrument_id="BTC-USDT",
        )
    )

    assert [item.action for item in observations] == ["snapshot", "update"]
    assert observations[1].source_line == 2
    assert [(level.price, level.quantity) for level in observations[1].book.bids] == [
        (Decimal("100.5"), Decimal("1.5")),
        (Decimal(99), Decimal(4)),
    ]
    assert [(level.price, level.quantity) for level in observations[1].book.asks] == [
        (Decimal(101), Decimal("2.5")),
        (Decimal(102), Decimal(5)),
    ]


def test_derivative_contract_counts_require_metadata_and_normalize_to_base() -> None:
    raw = [
        line(
            instrument_id="BTC-USDT-SWAP",
            action="snapshot",
            ts="1760000000000",
            bids=[["100000", "50", "2"]],
            asks=[["100001", "25", "1"]],
        )
    ]

    with pytest.raises(ValueError, match="requires pinned instrument metadata"):
        list(
            iter_okx_l2_jsonl(
                raw,
                instrument_type="SWAP",
                expected_instrument_id="BTC-USDT-SWAP",
            )
        )

    observation = list(
        iter_okx_l2_jsonl(
            raw,
            instrument_type="SWAP",
            expected_instrument_id="BTC-USDT-SWAP",
            metadata=derivative_metadata(),
        )
    )[0]

    assert observation.book.bids[0].quantity == Decimal("0.50")
    assert observation.book.asks[0].quantity == Decimal("0.25")


def test_derivative_replay_fails_closed_when_contract_currency_is_not_base() -> None:
    with pytest.raises(ValueError, match="price-dependent normalization"):
        list(
            iter_okx_l2_jsonl(
                [
                    line(
                        instrument_id="BTC-USDT-SWAP",
                        action="snapshot",
                        ts="1760000000000",
                        bids=[["100000", "1", "1"]],
                        asks=[["100001", "1", "1"]],
                    )
                ],
                instrument_type="SWAP",
                expected_instrument_id="BTC-USDT-SWAP",
                metadata=derivative_metadata(currency="USD"),
            )
        )


def test_replay_requires_initial_snapshot_and_known_actions() -> None:
    update = line(
        action="update",
        ts="1760000000000",
        bids=[],
        asks=[],
    )
    with pytest.raises(ValueError, match="must begin with a snapshot"):
        list(
            iter_okx_l2_jsonl(
                [update],
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )

    unknown = line(
        action="reset",
        ts="1760000000000",
        bids=[],
        asks=[],
    )
    with pytest.raises(ValueError, match="unsupported historical action"):
        list(
            iter_okx_l2_jsonl(
                [unknown],
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )


def test_replay_rejects_schema_drift_and_time_regression() -> None:
    malformed = json.dumps(
        {
            "instId": "BTC-USDT",
            "action": "snapshot",
            "ts": "1760000000000",
            "bids": [["100", "1"]],
            "asks": [],
        }
    )
    with pytest.raises(ValueError, match="price,size,orderCount"):
        list(
            iter_okx_l2_jsonl(
                [malformed],
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )

    with pytest.raises(ValueError, match="non-decreasing"):
        list(
            iter_okx_l2_jsonl(
                [
                    line(
                        action="snapshot",
                        ts="1760000000100",
                        bids=[],
                        asks=[],
                    ),
                    line(
                        action="update",
                        ts="1760000000000",
                        bids=[],
                        asks=[],
                    ),
                ],
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )


def test_tar_gz_archive_streams_single_data_member(tmp_path: Path) -> None:
    archive_path = tmp_path / "book.tar.gz"
    payload = (
        line(
            action="snapshot",
            ts="1760000000000",
            bids=[["100", "1", "1"]],
            asks=[["101", "1", "1"]],
        )
        + "\n"
    ).encode()

    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo("BTC-USDT-L2orderbook-400lv.data")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    observations = list(
        iter_okx_l2_archive(
            archive_path,
            instrument_type="SPOT",
            expected_instrument_id="BTC-USDT",
        )
    )

    assert len(observations) == 1
    assert observations[0].book.best_bid == Decimal(100)
    assert observations[0].book.best_ask == Decimal(101)


def test_tar_gz_archive_rejects_ambiguous_multiple_data_members(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "ambiguous.tar.gz"
    payload = b"{}\n"

    with tarfile.open(archive_path, "w:gz") as archive:
        for name in ("a.data", "b.data"):
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    with pytest.raises(ValueError, match="exactly one .data member"):
        list(
            iter_okx_l2_archive(
                archive_path,
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )
