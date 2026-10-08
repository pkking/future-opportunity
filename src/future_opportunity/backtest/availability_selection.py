from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta


POLICY_VERSION = "availability-even-rank-v1"


@dataclass(frozen=True, slots=True)
class AvailabilitySelectionRequest:
    strategy: str
    start_date: str
    end_date: str
    excluded_market_dates: tuple[str, ...]
    sample_size: int
    policy_version: str = POLICY_VERSION

    def __post_init__(self) -> None:
        if self.strategy not in {"funding-carry", "cash-and-carry"}:
            raise ValueError(
                f"unsupported availability-selection strategy: {self.strategy}"
            )
        if self.policy_version != POLICY_VERSION:
            raise ValueError(
                f"unsupported availability-selection policy: {self.policy_version}"
            )
        if type(self.sample_size) is not int or self.sample_size <= 0:
            raise ValueError("availability-selection sample_size must be positive")
        start, end = _window(self.start_date, self.end_date)
        previous: date | None = None
        for raw in self.excluded_market_dates:
            item = date.fromisoformat(raw)
            if item < start or item > end:
                raise ValueError(
                    "availability-selection exclusion is outside the study window"
                )
            if previous is not None and item <= previous:
                raise ValueError(
                    "availability-selection exclusions must be unique and chronological"
                )
            previous = item


@dataclass(frozen=True, slots=True)
class AvailabilitySelectionResult:
    request: AvailabilitySelectionRequest
    eligible_market_dates: tuple[str, ...]
    selected_market_dates: tuple[str, ...]
    evidence_sha256: str

    @property
    def population_size(self) -> int:
        return len(self.eligible_market_dates)


def replay_availability_selection(
    request: AvailabilitySelectionRequest,
) -> AvailabilitySelectionResult:
    start, end = _window(request.start_date, request.end_date)
    excluded = set(request.excluded_market_dates)
    eligible: list[str] = []
    cursor = start
    while cursor <= end:
        value = cursor.isoformat()
        if value not in excluded:
            eligible.append(value)
        cursor += timedelta(days=1)

    if request.sample_size > len(eligible):
        raise ValueError(
            "availability-selection sample_size exceeds eligible population"
        )
    selected = _even_rank(tuple(eligible), request.sample_size)
    payload = {
        "policy_version": request.policy_version,
        "strategy": request.strategy,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "excluded_market_dates": list(request.excluded_market_dates),
        "population_size": len(eligible),
        "requested_sample_size": request.sample_size,
        "selected_market_dates": list(selected),
    }
    digest = hashlib.sha256(
        (
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    return AvailabilitySelectionResult(
        request=request,
        eligible_market_dates=tuple(eligible),
        selected_market_dates=selected,
        evidence_sha256=digest,
    )


def _even_rank(
    dates: tuple[str, ...],
    count: int,
) -> tuple[str, ...]:
    if count == len(dates):
        return dates
    indices = tuple(
        ((2 * index + 1) * len(dates)) // (2 * count)
        for index in range(count)
    )
    selected = tuple(dates[index] for index in indices)
    if len(set(selected)) != count:
        raise AssertionError(
            "availability-selection rank buckets produced duplicate dates"
        )
    return selected


def _window(start_date: str, end_date: str) -> tuple[date, date]:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as error:
        raise ValueError(
            "availability-selection dates must use YYYY-MM-DD"
        ) from error
    if end < start:
        raise ValueError(
            "availability-selection end_date must not precede start_date"
        )
    return start, end
