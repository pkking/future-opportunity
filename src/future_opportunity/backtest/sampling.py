from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


_SUPPORTED_STRATEGIES = {"funding-carry", "cash-and-carry"}
_DEFAULT_POLICY_VERSION = "systematic-stratified-sha256-v1"


@dataclass(frozen=True, slots=True)
class HistoricalSamplingRequest:
    strategy: str
    start_date: str
    end_date: str
    sample_size: int
    seed: str
    policy_version: str = _DEFAULT_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.strategy not in _SUPPORTED_STRATEGIES:
            raise ValueError(
                f"unsupported historical sampling strategy: {self.strategy}"
            )
        if type(self.sample_size) is not int or self.sample_size <= 0:
            raise ValueError("historical sampling sample_size must be positive")
        if not self.seed:
            raise ValueError("historical sampling seed is required")
        if not self.policy_version:
            raise ValueError("historical sampling policy_version is required")
        _parse_window(self.start_date, self.end_date)


@dataclass(frozen=True, slots=True)
class HistoricalSamplingStratum:
    index: int
    population_start_index: int
    population_end_index_exclusive: int
    width: int
    hash_input: str
    sha256: str
    offset: int
    selected_population_index: int
    selected_date: str

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("sampling stratum index must be non-negative")
        if self.population_start_index < 0:
            raise ValueError(
                "sampling stratum population_start_index must be non-negative"
            )
        if self.population_end_index_exclusive <= self.population_start_index:
            raise ValueError("sampling stratum must contain at least one day")
        if (
            self.width
            != self.population_end_index_exclusive
            - self.population_start_index
        ):
            raise ValueError("sampling stratum width disagrees with boundaries")
        if not 0 <= self.offset < self.width:
            raise ValueError("sampling stratum offset is outside the stratum")
        if (
            self.selected_population_index
            != self.population_start_index + self.offset
        ):
            raise ValueError(
                "sampling selected_population_index disagrees with offset"
            )
        _validate_sha256(self.sha256)
        date.fromisoformat(self.selected_date)


@dataclass(frozen=True, slots=True)
class HistoricalSamplingResult:
    schema_version: int
    evidence_type: str
    request: HistoricalSamplingRequest
    population_size: int
    selected_count: int
    selected_dates: tuple[str, ...]
    strata: tuple[HistoricalSamplingStratum, ...]
    replacement_policy: str
    note: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported historical sampling result schema")
        if self.evidence_type != "pre_registered_historical_market_day_sample":
            raise ValueError("unexpected historical sampling evidence_type")
        if self.population_size <= 0:
            raise ValueError("historical sampling population_size must be positive")
        if self.selected_count != len(self.selected_dates):
            raise ValueError(
                "historical sampling selected_count disagrees with selected_dates"
            )
        if self.selected_count != len(self.strata):
            raise ValueError(
                "historical sampling selected_count disagrees with strata"
            )
        if len(set(self.selected_dates)) != len(self.selected_dates):
            raise ValueError("historical sampling selected_dates must be unique")
        if tuple(sorted(self.selected_dates)) != self.selected_dates:
            raise ValueError(
                "historical sampling selected_dates must be chronological"
            )


def sample_historical_market_days(
    request: HistoricalSamplingRequest,
) -> HistoricalSamplingResult:
    start, end = _parse_window(request.start_date, request.end_date)
    population_size = (end - start).days + 1
    selected_count = min(request.sample_size, population_size)

    strata: list[HistoricalSamplingStratum] = []
    selected_dates: list[str] = []
    for index in range(selected_count):
        population_start = (index * population_size) // selected_count
        population_end = ((index + 1) * population_size) // selected_count
        width = population_end - population_start
        if width <= 0:
            raise RuntimeError("sampling produced an empty stratum")

        hash_input = "|".join(
            (
                request.policy_version,
                request.strategy,
                request.seed,
                request.start_date,
                request.end_date,
                str(index),
            )
        )
        digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        offset = int(digest, 16) % width
        selected_population_index = population_start + offset
        selected_date = (
            start + timedelta(days=selected_population_index)
        ).isoformat()

        strata.append(
            HistoricalSamplingStratum(
                index=index,
                population_start_index=population_start,
                population_end_index_exclusive=population_end,
                width=width,
                hash_input=hash_input,
                sha256=digest,
                offset=offset,
                selected_population_index=selected_population_index,
                selected_date=selected_date,
            )
        )
        selected_dates.append(selected_date)

    return HistoricalSamplingResult(
        schema_version=1,
        evidence_type="pre_registered_historical_market_day_sample",
        request=request,
        population_size=population_size,
        selected_count=selected_count,
        selected_dates=tuple(selected_dates),
        strata=tuple(strata),
        replacement_policy="none-v1",
        note=(
            "Date selection is deterministic and outcome-independent. "
            "Source-data unavailability must be recorded as an exclusion; "
            "the draw is not silently replaced after observing results."
        ),
    )


def historical_sampling_payload(
    result: HistoricalSamplingResult,
) -> dict[str, object]:
    return {
        "schema_version": result.schema_version,
        "evidence_type": result.evidence_type,
        "request": {
            "strategy": result.request.strategy,
            "start_date": result.request.start_date,
            "end_date": result.request.end_date,
            "sample_size": result.request.sample_size,
            "seed": result.request.seed,
            "policy_version": result.request.policy_version,
        },
        "population_size": result.population_size,
        "selected_count": result.selected_count,
        "selected_dates": list(result.selected_dates),
        "strata": [
            {
                "index": item.index,
                "population_start_index": item.population_start_index,
                "population_end_index_exclusive": (
                    item.population_end_index_exclusive
                ),
                "width": item.width,
                "hash_input": item.hash_input,
                "sha256": item.sha256,
                "offset": item.offset,
                "selected_population_index": item.selected_population_index,
                "selected_date": item.selected_date,
            }
            for item in result.strata
        ],
        "replacement_policy": result.replacement_policy,
        "note": result.note,
    }


def historical_sampling_json(
    result: HistoricalSamplingResult,
) -> str:
    return (
        json.dumps(
            historical_sampling_payload(result),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def parse_historical_sampling_evidence(
    raw: Any,
) -> HistoricalSamplingResult:
    if not isinstance(raw, dict):
        raise TypeError("historical sampling evidence must be an object")

    expected_keys = {
        "schema_version",
        "evidence_type",
        "request",
        "population_size",
        "selected_count",
        "selected_dates",
        "strata",
        "replacement_policy",
        "note",
    }
    if set(raw) != expected_keys:
        raise ValueError("historical sampling evidence fields differ from schema")

    request_raw = raw.get("request")
    if not isinstance(request_raw, dict):
        raise TypeError("historical sampling request must be an object")
    request_keys = {
        "strategy",
        "start_date",
        "end_date",
        "sample_size",
        "seed",
        "policy_version",
    }
    if set(request_raw) != request_keys:
        raise ValueError("historical sampling request fields differ from schema")

    request = HistoricalSamplingRequest(
        strategy=_required_string(request_raw, "strategy"),
        start_date=_required_string(request_raw, "start_date"),
        end_date=_required_string(request_raw, "end_date"),
        sample_size=_required_int(request_raw, "sample_size"),
        seed=_required_string(request_raw, "seed"),
        policy_version=_required_string(request_raw, "policy_version"),
    )
    expected = sample_historical_market_days(request)
    expected_payload = historical_sampling_payload(expected)
    if raw != expected_payload:
        raise ValueError(
            "historical sampling evidence does not match deterministic replay"
        )
    return expected


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"historical sampling request requires {key}")
    return value


def _required_int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if type(value) is not int:
        raise TypeError(f"historical sampling request {key} must be integer")
    return value


def _parse_window(start_date: str, end_date: str) -> tuple[date, date]:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as error:
        raise ValueError(
            "historical sampling dates must use YYYY-MM-DD"
        ) from error
    if end < start:
        raise ValueError(
            "historical sampling end_date must not be before start_date"
        )
    return start, end


def _validate_sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("SHA-256 must contain 64 hexadecimal characters")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("SHA-256 must be hexadecimal") from error
