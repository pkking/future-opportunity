from datetime import UTC, datetime, timedelta
from decimal import Decimal

from future_opportunity.backtest.alignment import align_order_books
from future_opportunity.backtest.model import HistoricalOrderBookObservation
from future_opportunity.domain.market.snapshot import OrderBook, OrderBookLevel


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def observation(
    instrument_id: str,
    *,
    seconds: int,
    source_line: int,
) -> HistoricalOrderBookObservation:
    observed_at = BASE + timedelta(seconds=seconds)
    return HistoricalOrderBookObservation(
        instrument_id=instrument_id,
        action="snapshot" if source_line == 1 else "update",
        source_line=source_line,
        observed_at=observed_at,
        book=OrderBook(
            bids=(OrderBookLevel(price=Decimal(100), quantity=Decimal(10)),),
            asks=(OrderBookLevel(price=Decimal(101), quantity=Decimal(10)),),
            observed_at=observed_at,
        ),
    )


def test_alignment_uses_latest_prior_book_and_records_age() -> None:
    report = align_order_books(
        (
            observation("spot", seconds=0, source_line=1),
            observation("spot", seconds=50, source_line=2),
        ),
        (
            observation("hedge", seconds=10, source_line=1),
            observation("hedge", seconds=60, source_line=2),
        ),
        start=BASE,
        end=BASE + timedelta(seconds=60),
        cadence=timedelta(seconds=30),
        max_staleness=timedelta(seconds=30),
    )

    assert report.requested_samples == 3
    assert report.emitted_samples == 2
    assert report.missing_hedge_samples == 1
    assert report.coverage_ratio == Decimal(2) / Decimal(3)

    at_30, at_60 = report.samples
    assert at_30.spot.source_line == 1
    assert at_30.hedge.source_line == 1
    assert at_30.spot_age_ms == 30_000
    assert at_30.hedge_age_ms == 20_000

    assert at_60.spot.source_line == 2
    assert at_60.hedge.source_line == 2
    assert at_60.spot_age_ms == 10_000
    assert at_60.hedge_age_ms == 0


def test_alignment_drops_stale_samples_instead_of_unbounded_fill_forward() -> None:
    report = align_order_books(
        (observation("spot", seconds=0, source_line=1),),
        (observation("hedge", seconds=0, source_line=1),),
        start=BASE,
        end=BASE + timedelta(seconds=60),
        cadence=timedelta(seconds=30),
        max_staleness=timedelta(seconds=10),
    )

    assert report.requested_samples == 3
    assert report.emitted_samples == 1
    assert report.stale_spot_samples == 2
    assert report.stale_hedge_samples == 2
    assert report.coverage_ratio == Decimal(1) / Decimal(3)
