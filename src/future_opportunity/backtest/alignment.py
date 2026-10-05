from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

from future_opportunity.backtest.model import (
    HistoricalAlignmentReport,
    HistoricalBookPair,
    HistoricalOrderBookObservation,
)


@dataclass(slots=True)
class _Cursor:
    iterator: Iterator[HistoricalOrderBookObservation]
    next_observation: HistoricalOrderBookObservation | None
    current: HistoricalOrderBookObservation | None = None

    @classmethod
    def create(
        cls,
        observations: Iterable[HistoricalOrderBookObservation],
    ) -> "_Cursor":
        iterator = iter(observations)
        return cls(iterator=iterator, next_observation=next(iterator, None))

    def as_of(
        self,
        sampled_at: datetime,
    ) -> HistoricalOrderBookObservation | None:
        while (
            self.next_observation is not None
            and self.next_observation.observed_at <= sampled_at
        ):
            self.current = self.next_observation
            self.next_observation = next(self.iterator, None)
        return self.current


def align_order_books(
    spot_observations: Iterable[HistoricalOrderBookObservation],
    hedge_observations: Iterable[HistoricalOrderBookObservation],
    *,
    start: datetime,
    end: datetime,
    cadence: timedelta,
    max_staleness: timedelta,
) -> HistoricalAlignmentReport:
    """As-of join asynchronous books at explicit sample times.

    Missing/stale samples are counted rather than silently filled forward.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("alignment timestamps must be timezone-aware")
    if end < start:
        raise ValueError("alignment end must not be before start")
    if cadence <= timedelta(0):
        raise ValueError("alignment cadence must be positive")
    if max_staleness < timedelta(0):
        raise ValueError("max_staleness must be non-negative")

    spot = _Cursor.create(spot_observations)
    hedge = _Cursor.create(hedge_observations)

    requested = 0
    missing_spot = 0
    missing_hedge = 0
    stale_spot = 0
    stale_hedge = 0
    samples: list[HistoricalBookPair] = []

    sampled_at = start
    while sampled_at <= end:
        requested += 1
        spot_observation = spot.as_of(sampled_at)
        hedge_observation = hedge.as_of(sampled_at)

        if spot_observation is None:
            missing_spot += 1
        if hedge_observation is None:
            missing_hedge += 1
        if spot_observation is None or hedge_observation is None:
            sampled_at += cadence
            continue

        spot_age = sampled_at - spot_observation.observed_at
        hedge_age = sampled_at - hedge_observation.observed_at
        spot_is_stale = spot_age > max_staleness
        hedge_is_stale = hedge_age > max_staleness

        if spot_is_stale:
            stale_spot += 1
        if hedge_is_stale:
            stale_hedge += 1
        if spot_is_stale or hedge_is_stale:
            sampled_at += cadence
            continue

        samples.append(
            HistoricalBookPair(
                sampled_at=sampled_at,
                spot=spot_observation,
                hedge=hedge_observation,
                spot_age_ms=int(spot_age.total_seconds() * 1000),
                hedge_age_ms=int(hedge_age.total_seconds() * 1000),
            )
        )
        sampled_at += cadence

    return HistoricalAlignmentReport(
        requested_samples=requested,
        emitted_samples=len(samples),
        missing_spot_samples=missing_spot,
        missing_hedge_samples=missing_hedge,
        stale_spot_samples=stale_spot,
        stale_hedge_samples=stale_hedge,
        samples=tuple(samples),
    )
