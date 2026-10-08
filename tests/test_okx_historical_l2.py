from __future__ import annotations

import io
import json
import tarfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_archive,
    iter_okx_l2_jsonl,
    iter_okx_l2_sampled_archive,
    iter_okx_l2_sampled_jsonl,
    okx_l2_archive_member_name,
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

    with pytest.raises(ValueError, match="exactly one .data member for BTC-USDT"):
        list(
            iter_okx_l2_archive(
                archive_path,
                instrument_type="SPOT",
                expected_instrument_id="BTC-USDT",
            )
        )


def test_multi_contract_archive_selects_exact_expected_future(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "future-chain.tar.gz"
    start = datetime(2026, 1, 11, 0, 15, tzinfo=UTC)
    ts = str(int(start.timestamp() * 1000))

    with tarfile.open(archive_path, "w:gz") as archive:
        for future_id in ("BTC-USDT-260327", "BTC-USDT-260626"):
            payload = (
                line(
                    instrument_id=future_id,
                    action="snapshot",
                    ts=ts,
                    bids=[["100000", "50", "2"]],
                    asks=[["100001", "25", "1"]],
                )
                + "\n"
            ).encode()
            info = tarfile.TarInfo(
                f"{future_id}-L2orderbook-400lv-2026-01-11.data"
            )
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    assert okx_l2_archive_member_name(
        archive_path,
        expected_instrument_id="BTC-USDT-260327",
    ) == "BTC-USDT-260327-L2orderbook-400lv-2026-01-11.data"

    metadata = HistoricalInstrumentMetadata(
        instrument_id="BTC-USDT-260327",
        instrument_family="BTC-USDT",
        instrument_type="FUTURES",
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal(1),
        contract_value_currency="BTC",
        settlement_currency="USDT",
        list_time=None,
        expiry_time=datetime(2026, 3, 27, 8, tzinfo=UTC),
    )
    observations = tuple(
        iter_okx_l2_sampled_archive(
            archive_path,
            instrument_type="FUTURES",
            expected_instrument_id="BTC-USDT-260327",
            start=start,
            end=start,
            cadence=timedelta(minutes=15),
            metadata=metadata,
        )
    )
    assert len(observations) == 1
    assert observations[0].instrument_id == "BTC-USDT-260327"
    assert observations[0].book.bids[0].quantity == Decimal("0.50")


def test_multi_contract_archive_fails_closed_when_target_missing(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "missing.tar.gz"
    payload = b"{}\n"
    with tarfile.open(archive_path, "w:gz") as archive:
        for future_id in ("BTC-USDT-260327", "BTC-USDT-260626"):
            info = tarfile.TarInfo(
                f"{future_id}-L2orderbook-400lv-2026-01-11.data"
            )
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    with pytest.raises(ValueError, match="found 0 among 2 data members"):
        okx_l2_archive_member_name(
            archive_path,
            expected_instrument_id="BTC-USDT-260130",
        )


def test_multi_contract_archive_fails_closed_on_duplicate_target(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "duplicate.tar.gz"
    payload = b"{}\n"
    with tarfile.open(archive_path, "w:gz") as archive:
        for name in (
            "BTC-USDT-260327-L2orderbook-400lv-2026-01-11.data",
            "nested/BTC-USDT-260327-L2orderbook-400lv-2026-01-11.data",
        ):
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    with pytest.raises(ValueError, match="found 2 among 2 data members"):
        okx_l2_archive_member_name(
            archive_path,
            expected_instrument_id="BTC-USDT-260327",
        )


def test_sampled_replay_emits_as_of_books_only_at_cadence() -> None:
    start = datetime.fromtimestamp(1760000000, tz=UTC)
    observations = tuple(
        iter_okx_l2_sampled_jsonl(
            [
                line(
                    action="snapshot",
                    ts="1760000000000",
                    bids=[["100", "1", "1"]],
                    asks=[["101", "1", "1"]],
                ),
                line(
                    action="update",
                    ts="1760000005000",
                    bids=[["100", "2", "1"]],
                    asks=[],
                ),
                line(
                    action="update",
                    ts="1760000015000",
                    bids=[["100.5", "1", "1"]],
                    asks=[],
                ),
                line(
                    action="update",
                    ts="1760000025000",
                    bids=[],
                    asks=[["101", "2", "1"]],
                ),
            ],
            instrument_type="SPOT",
            expected_instrument_id="BTC-USDT",
            start=start,
            end=start + timedelta(seconds=20),
            cadence=timedelta(seconds=10),
        )
    )

    assert len(observations) == 3
    at_0, at_10, at_20 = observations
    assert at_0.observed_at == start
    assert at_0.book.bids[0].quantity == Decimal(1)

    assert at_10.observed_at == start + timedelta(seconds=5)
    assert at_10.book.bids[0].quantity == Decimal(2)

    assert at_20.observed_at == start + timedelta(seconds=15)
    assert at_20.book.bids[0].price == Decimal("100.5")


def test_sampled_replay_does_not_backfill_before_initial_snapshot() -> None:
    start = datetime.fromtimestamp(1760000000, tz=UTC)
    observations = tuple(
        iter_okx_l2_sampled_jsonl(
            [
                line(
                    action="snapshot",
                    ts="1760000015000",
                    bids=[["100", "1", "1"]],
                    asks=[["101", "1", "1"]],
                ),
                line(
                    action="update",
                    ts="1760000025000",
                    bids=[["100", "2", "1"]],
                    asks=[],
                ),
            ],
            instrument_type="SPOT",
            expected_instrument_id="BTC-USDT",
            start=start,
            end=start + timedelta(seconds=20),
            cadence=timedelta(seconds=10),
        )
    )

    assert len(observations) == 1
    assert observations[0].observed_at == start + timedelta(seconds=15)
    assert observations[0].source_line == 1
