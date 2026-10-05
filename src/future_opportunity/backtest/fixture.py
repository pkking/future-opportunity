from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from future_opportunity.application.backtest.funding_carry import (
    HistoricalFundingCarryCase,
)
from future_opportunity.backtest.alignment import align_order_books
from future_opportunity.backtest.canonical import (
    iter_canonical_funding,
    iter_canonical_mark_prices,
    iter_canonical_order_books,
    sha256_file,
)
from future_opportunity.backtest.model import (
    HistoricalAlignmentReport,
    HistoricalFundingObservation,
    HistoricalMarkPriceCandle,
)
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
)


@dataclass(frozen=True, slots=True)
class LoadedFundingHistoryFixture:
    dataset_id: str
    manifest: dict[str, Any]
    alignment: HistoricalAlignmentReport
    funding: tuple[HistoricalFundingObservation, ...]
    mark_prices: tuple[HistoricalMarkPriceCandle, ...]
    root: Path


def load_funding_history_fixture(
    root: Path,
) -> LoadedFundingHistoryFixture:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise TypeError("historical fixture manifest must be an object")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported historical fixture schema")
    if manifest.get("venue") != "okx":
        raise ValueError("funding fixture currently requires OKX provenance")

    normalized = manifest.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("historical fixture is missing normalized components")

    paths: dict[str, Path] = {}
    for key in ("spot_books", "swap_books", "funding", "mark_price"):
        component = normalized.get(key)
        if not isinstance(component, dict):
            raise ValueError(f"historical fixture is missing {key}")
        relative = component.get("path")
        expected_sha = component.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"historical fixture {key} path is invalid")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ValueError(f"historical fixture {key} checksum is invalid")
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(
                f"historical fixture checksum mismatch for {key}: "
                f"{actual_sha} != {expected_sha}"
            )
        paths[key] = path

    history_date = manifest.get("history_date_utc")
    cadence_seconds = manifest.get("cadence_seconds")
    max_staleness_seconds = manifest.get("max_staleness_seconds")
    if not isinstance(history_date, str):
        raise ValueError("historical fixture date is invalid")
    if not isinstance(cadence_seconds, int) or cadence_seconds <= 0:
        raise ValueError("historical fixture cadence is invalid")
    if (
        not isinstance(max_staleness_seconds, int)
        or max_staleness_seconds < 0
    ):
        raise ValueError("historical fixture max staleness is invalid")

    start = datetime.fromisoformat(history_date).replace(tzinfo=UTC)
    cadence = timedelta(seconds=cadence_seconds)
    end = start + timedelta(days=1) - cadence
    alignment = align_order_books(
        iter_canonical_order_books(paths["spot_books"]),
        iter_canonical_order_books(paths["swap_books"]),
        start=start,
        end=end,
        cadence=cadence,
        max_staleness=timedelta(seconds=max_staleness_seconds),
    )

    declared_alignment = manifest.get("alignment")
    if not isinstance(declared_alignment, dict):
        raise ValueError("historical fixture is missing alignment evidence")
    if alignment.requested_samples != declared_alignment.get("requested_samples"):
        raise ValueError("historical fixture requested sample count drifted")
    if alignment.emitted_samples != declared_alignment.get("emitted_samples"):
        raise ValueError("historical fixture emitted sample count drifted")
    if str(alignment.coverage_ratio) != declared_alignment.get("coverage_ratio"):
        raise ValueError("historical fixture alignment coverage drifted")

    funding = tuple(iter_canonical_funding(paths["funding"]))
    mark_prices = tuple(iter_canonical_mark_prices(paths["mark_price"]))
    dataset_id = manifest.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("historical fixture dataset_id is invalid")

    return LoadedFundingHistoryFixture(
        dataset_id=dataset_id,
        manifest=manifest,
        alignment=alignment,
        funding=funding,
        mark_prices=mark_prices,
        root=root,
    )


def build_funding_case(
    fixture: LoadedFundingHistoryFixture,
    *,
    entry_index: int,
    exit_index: int,
) -> HistoricalFundingCarryCase:
    samples = fixture.alignment.samples
    if not 0 <= entry_index < len(samples):
        raise IndexError("entry_index outside aligned historical samples")
    if not 0 <= exit_index < len(samples):
        raise IndexError("exit_index outside aligned historical samples")
    if exit_index <= entry_index:
        raise ValueError("exit_index must be after entry_index")

    entry_pair = samples[entry_index]
    exit_pair = samples[exit_index]
    entry_snapshot = _snapshot(
        fixture,
        sampled_at=entry_pair.sampled_at,
        spot_book=entry_pair.spot.book,
        swap_book=entry_pair.hedge.book,
    )
    exit_snapshot = _snapshot(
        fixture,
        sampled_at=exit_pair.sampled_at,
        spot_book=exit_pair.spot.book,
        swap_book=exit_pair.hedge.book,
    )
    relevant_funding = tuple(
        item
        for item in fixture.funding
        if (
            entry_pair.sampled_at < item.funding_time
            <= exit_pair.sampled_at
        )
    )
    relevant_minutes = {
        item.funding_time.replace(second=0, microsecond=0)
        for item in relevant_funding
    }
    relevant_marks = tuple(
        item
        for item in fixture.mark_prices
        if item.started_at in relevant_minutes
    )

    return HistoricalFundingCarryCase(
        case_id=(
            f"{fixture.dataset_id}:"
            f"{entry_pair.sampled_at.isoformat()}.."
            f"{exit_pair.sampled_at.isoformat()}"
        ),
        entry=entry_snapshot,
        exit=exit_snapshot,
        funding=relevant_funding,
        mark_prices=relevant_marks,
        evidence_ids=(
            fixture.dataset_id,
            f"spot-source-line:{entry_pair.spot.source_line}",
            f"swap-source-line:{entry_pair.hedge.source_line}",
            f"spot-exit-source-line:{exit_pair.spot.source_line}",
            f"swap-exit-source-line:{exit_pair.hedge.source_line}",
        ),
    )


def _snapshot(
    fixture: LoadedFundingHistoryFixture,
    *,
    sampled_at: datetime,
    spot_book,
    swap_book,
) -> FundingCarryMarketSnapshot:
    prior_funding = [
        item
        for item in fixture.funding
        if item.funding_time <= sampled_at
    ]
    future_funding = [
        item
        for item in fixture.funding
        if item.funding_time > sampled_at
    ]
    if not prior_funding:
        raise ValueError(
            "historical snapshot requires at least one prior funding observation"
        )

    last = prior_funding[-1]
    next_time = (
        future_funding[0].funding_time
        if future_funding
        else last.funding_time + timedelta(hours=8)
    )
    history = tuple(
        FundingObservation(
            rate=item.funding_rate,
            funding_time=item.funding_time,
            mark_price=None,
            rate_type="historical",
        )
        for item in prior_funding
    )

    return FundingCarryMarketSnapshot(
        venue="okx",
        base="BTC",
        quote="USDT",
        spot_instrument_id="okx:BTC-USDT:spot",
        perpetual_instrument_id="okx:BTC-USDT-SWAP:perpetual",
        spot_book=spot_book,
        perpetual_book=swap_book,
        mark_price=(
            swap_book.best_bid + swap_book.best_ask
        ) / Decimal(2),
        last_funding_rate=last.funding_rate,
        next_funding_time=next_time,
        funding_history=history,
        observed_at=sampled_at,
    )
