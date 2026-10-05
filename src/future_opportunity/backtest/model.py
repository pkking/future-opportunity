from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from future_opportunity.domain.market.snapshot import OrderBook


@dataclass(frozen=True, slots=True)
class HistoricalArchiveFile:
    module: str
    instrument_type: str
    instrument_id: str
    instrument_family: str
    date_aggregation: str
    date_range_start: datetime
    date_range_end: datetime
    data_date: datetime
    source_timezone: str
    filename: str
    url: str
    declared_size_mb: Decimal | None = None
    raw_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class HistoricalInstrumentMetadata:
    instrument_id: str
    instrument_family: str
    instrument_type: str
    contract_value: Decimal | None
    contract_multiplier: Decimal | None
    contract_value_currency: str | None
    settlement_currency: str | None
    list_time: datetime | None
    expiry_time: datetime | None


@dataclass(frozen=True, slots=True)
class HistoricalDatasetManifest:
    schema_version: int
    dataset_id: str
    venue: str
    source_endpoint: str
    source_query: tuple[tuple[str, str], ...]
    source_files: tuple[HistoricalArchiveFile, ...]
    instruments: tuple[HistoricalInstrumentMetadata, ...]
    normalizer_version: str
    normalized_sha256: str
    sample_count: int
    observed_start: datetime
    observed_end: datetime

    def __post_init__(self) -> None:
        if self.schema_version <= 0:
            raise ValueError("schema_version must be positive")
        if not self.dataset_id:
            raise ValueError("dataset_id is required")
        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")
        if self.observed_end < self.observed_start:
            raise ValueError("observed_end must not be before observed_start")
        _validate_sha256(self.normalized_sha256)
        for source in self.source_files:
            if source.raw_sha256 is not None:
                _validate_sha256(source.raw_sha256)

    @classmethod
    def from_query(
        cls,
        *,
        schema_version: int,
        dataset_id: str,
        venue: str,
        source_endpoint: str,
        source_query: Mapping[str, str],
        source_files: tuple[HistoricalArchiveFile, ...],
        instruments: tuple[HistoricalInstrumentMetadata, ...],
        normalizer_version: str,
        normalized_sha256: str,
        sample_count: int,
        observed_start: datetime,
        observed_end: datetime,
    ) -> "HistoricalDatasetManifest":
        return cls(
            schema_version=schema_version,
            dataset_id=dataset_id,
            venue=venue,
            source_endpoint=source_endpoint,
            source_query=tuple(sorted(source_query.items())),
            source_files=source_files,
            instruments=instruments,
            normalizer_version=normalizer_version,
            normalized_sha256=normalized_sha256,
            sample_count=sample_count,
            observed_start=observed_start,
            observed_end=observed_end,
        )


def _validate_sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("SHA-256 must contain 64 hexadecimal characters")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("SHA-256 must be hexadecimal") from error


@dataclass(frozen=True, slots=True)
class HistoricalOrderBookObservation:
    instrument_id: str
    action: str
    source_line: int
    observed_at: datetime
    book: OrderBook

    def __post_init__(self) -> None:
        if self.action not in {"snapshot", "update"}:
            raise ValueError(f"unsupported order-book action: {self.action}")
        if self.source_line <= 0:
            raise ValueError("source_line must be positive")


@dataclass(frozen=True, slots=True)
class HistoricalBookPair:
    sampled_at: datetime
    spot: HistoricalOrderBookObservation
    hedge: HistoricalOrderBookObservation
    spot_age_ms: int
    hedge_age_ms: int


@dataclass(frozen=True, slots=True)
class HistoricalAlignmentReport:
    requested_samples: int
    emitted_samples: int
    missing_spot_samples: int
    missing_hedge_samples: int
    stale_spot_samples: int
    stale_hedge_samples: int
    samples: tuple[HistoricalBookPair, ...]

    @property
    def coverage_ratio(self) -> Decimal:
        if self.requested_samples == 0:
            return Decimal(0)
        return Decimal(self.emitted_samples) / Decimal(self.requested_samples)


@dataclass(frozen=True, slots=True)
class HistoricalFundingObservation:
    instrument_id: str
    source_line: int
    funding_time: datetime
    funding_rate: Decimal

    def __post_init__(self) -> None:
        if self.source_line <= 1:
            raise ValueError("funding source_line must refer to a CSV data row")


@dataclass(frozen=True, slots=True)
class HistoricalMarkPriceCandle:
    instrument_id: str
    started_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    confirmed: bool

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise ValueError("mark-price candle instrument_id is required")
        if self.started_at.tzinfo is None:
            raise ValueError("mark-price candle timestamp must be timezone-aware")
        if min(
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
        ) <= 0:
            raise ValueError("mark-price candle prices must be positive")
        if self.low_price > self.high_price:
            raise ValueError("mark-price candle low must not exceed high")
        if not self.low_price <= self.open_price <= self.high_price:
            raise ValueError("mark-price candle open must lie within low/high")
        if not self.low_price <= self.close_price <= self.high_price:
            raise ValueError("mark-price candle close must lie within low/high")


@dataclass(frozen=True, slots=True)
class HistoricalFundingCashFlowBound:
    funding_time: datetime
    funding_rate: Decimal
    mark_price_low: Decimal
    mark_price_high: Decimal
    cash_flow_lower: Decimal
    cash_flow_upper: Decimal
    evidence_complete: bool
    evidence_note: str
