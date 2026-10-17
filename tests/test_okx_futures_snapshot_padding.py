"""Source-scoped empty-tail compatibility for 400-level OKX FUTURES snapshots.

Derived from diagnostic artifact 12094284504 of run 39015453399.
"""
from __future__ import annotations

import io
import json
import tarfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_jsonl,
    iter_okx_l2_sampled_archive,
    iter_okx_l2_sampled_jsonl,
)
from future_opportunity.backtest.model import HistoricalInstrumentMetadata


FUTURE = "BTC-USDT-250926"
AT = datetime(2025, 7, 4, 0, 15, tzinfo=UTC)
EMPTY = ["0", "0.0", "0"]


def metadata(instrument_id: str = FUTURE, kind: str = "FUTURES"):
    return HistoricalInstrumentMetadata(
        instrument_id=instrument_id,
        instrument_family="BTC-USDT",
        instrument_type=kind,
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal(1),
        contract_value_currency="BTC",
        settlement_currency="USDT",
        list_time=None,
        expiry_time=AT + timedelta(days=80),
    )


def book(*, instrument_id: str = FUTURE, action: str = "snapshot",
         ts: datetime = AT, padded: bool = True) -> dict:
    bids = [[str(110798 - i), "1", "1"] for i in range(400)]
    asks = [[str(110799 + i), "2", "2"] for i in range(400)]
    if padded:
        asks[325:] = [EMPTY.copy() for _ in range(75)]
    return {
        "instId": instrument_id,
        "action": action,
        "ts": str(int(ts.timestamp() * 1000)),
        "bids": bids,
        "asks": asks,
    }


def replay_full(event: dict, *, kind: str = "FUTURES"):
    instrument_id = event["instId"]
    m = None if kind == "SPOT" else metadata(instrument_id, kind)
    return list(iter_okx_l2_jsonl(
        [json.dumps(event)], instrument_type=kind,
        expected_instrument_id=instrument_id, metadata=m,
    ))


def replay_sampled(event: dict, *, kind: str = "FUTURES"):
    instrument_id = event["instId"]
    m = None if kind == "SPOT" else metadata(instrument_id, kind)
    return list(iter_okx_l2_sampled_jsonl(
        [json.dumps(event)], instrument_type=kind,
        expected_instrument_id=instrument_id,
        start=AT, end=AT, cadence=timedelta(minutes=15),
        metadata=m,
    ))


@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_real_source_pattern_recovers_325_asks_and_400_bids(replay) -> None:
    event = book()
    observations = replay(event)
    assert len(observations) == 1
    result = observations[0].book
    assert len(result.bids) == 400
    assert len(result.asks) == 325
    assert result.best_bid == Decimal("110798")
    assert result.best_ask == Decimal("110799")
    assert result.bids[0].quantity == Decimal("0.01")
    assert result.asks[0].quantity == Decimal("0.02")
    assert all(level.price > 0 for level in result.asks)


def test_full_and_sampled_archive_emit_identical_canonical_book(tmp_path: Path) -> None:
    payload = (json.dumps(book()) + "\n").encode()
    archive_path = tmp_path / "futureschain.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        member = tarfile.TarInfo(
            "BTC-USDT-250926-L2orderbook-400lv-2025-07-04.data"
        )
        member.size = len(payload)
        tar.addfile(member, io.BytesIO(payload))
    output = list(iter_okx_l2_sampled_archive(
        archive_path,
        instrument_type="FUTURES",
        expected_instrument_id=FUTURE,
        start=AT, end=AT, cadence=timedelta(minutes=15),
        metadata=metadata(),
    ))
    full = replay_full(book())
    assert len(output) == 1
    assert output[0].book == full[0].book
    assert output[0].source_line == full[0].source_line


@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_non_padded_snapshot_replays_unchanged(replay) -> None:
    result = replay(book(padded=False))
    assert len(result) == 1
    assert len(result[0].book.asks) == 400


@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_short_snapshot_cannot_use_padding_exception(replay) -> None:
    event = book()
    event["asks"] = event["asks"][:330]
    with pytest.raises(ValueError, match="historical price must be positive"):
        replay(event)


@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_padding_in_middle_is_rejected(replay) -> None:
    event = book()
    event["asks"][399] = ["111400", "1", "1"]
    with pytest.raises(ValueError, match="not a contiguous suffix"):
        replay(event)


@pytest.mark.parametrize(
    "bad_level",
    [
        ["0", "1", "1"],
        ["0", "0.0", "1"],
        ["0", "0", "0"],
        ["0.00", "0.0", "0"],
        ["-1", "0.0", "0"],
        ["NaN", "0.0", "0"],
    ],
)
@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_price_zero_or_modified_padding_is_not_silently_discarded(
    replay, bad_level,
) -> None:
    event = book()
    event["asks"][325] = bad_level
    with pytest.raises((ValueError, ArithmeticError)):
        replay(event)


@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_all_empty_side_does_not_create_empty_canonical_book(replay) -> None:
    event = book()
    event["asks"] = [EMPTY.copy() for _ in range(400)]
    with pytest.raises(ValueError, match="has no active depth"):
        replay(event)


@pytest.mark.parametrize("kind,instrument_id", [("SPOT", "BTC-USDT"), ("SWAP", "BTC-USDT-SWAP")])
@pytest.mark.parametrize("replay", [replay_full, replay_sampled])
def test_other_instrument_types_must_reject_same_zero_tail(
    replay, kind, instrument_id,
) -> None:
    event = book(instrument_id=instrument_id)
    with pytest.raises(ValueError, match="historical price must be positive"):
        replay(event, kind=kind)


@pytest.mark.parametrize("sampled", [False, True])
def test_update_event_cannot_use_snapshot_padding_exception(sampled: bool) -> None:
    snapshot = book(padded=False)
    update = book(action="update", ts=AT + timedelta(milliseconds=100))
    payload = [json.dumps(snapshot), json.dumps(update)]
    if sampled:
        iterator = iter_okx_l2_sampled_jsonl(
            payload,
            instrument_type="FUTURES", expected_instrument_id=FUTURE,
            start=AT, end=AT + timedelta(milliseconds=150),
            cadence=timedelta(milliseconds=50), metadata=metadata(),
        )
    else:
        iterator = iter_okx_l2_jsonl(
            payload,
            instrument_type="FUTURES", expected_instrument_id=FUTURE,
            metadata=metadata(),
        )
    with pytest.raises(ValueError, match="historical price must be positive"):
        list(iterator)


def test_normal_positive_price_zero_size_update_still_removes_a_level() -> None:
    snapshot = book(padded=False)
    updated = {
        "instId": FUTURE, "action": "update",
        "ts": str(int((AT + timedelta(milliseconds=100)).timestamp() * 1000)),
        "bids": [["110798", "0", "0"]], "asks": [],
    }
    records = list(iter_okx_l2_jsonl(
        [json.dumps(snapshot), json.dumps(updated)],
        instrument_type="FUTURES", expected_instrument_id=FUTURE,
        metadata=metadata(),
    ))
    assert len(records[0].book.bids) == 400
    assert len(records[1].book.bids) == 399
    assert records[1].book.best_bid == Decimal("110797")
