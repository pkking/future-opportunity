from datetime import UTC, datetime
from decimal import Decimal

import pytest

from future_opportunity.backtest.model import (
    HistoricalArchiveFile,
    HistoricalDatasetManifest,
    HistoricalInstrumentMetadata,
)


def test_historical_manifest_sorts_query_and_validates_checksums() -> None:
    source = HistoricalArchiveFile(
        module="4",
        instrument_type="SPOT",
        instrument_id="BTC-USDT",
        instrument_family="",
        date_aggregation="daily",
        date_range_start=datetime(2026, 1, 1, tzinfo=UTC),
        date_range_end=datetime(2026, 1, 1, tzinfo=UTC),
        data_date=datetime(2026, 1, 1, tzinfo=UTC),
        source_timezone="UTC",
        filename="book.zip",
        url="https://static.okx.com/book.zip",
        declared_size_mb=Decimal("1.0"),
        raw_sha256="a" * 64,
    )
    instrument = HistoricalInstrumentMetadata(
        instrument_id="BTC-USDT-SWAP",
        instrument_family="BTC-USDT",
        instrument_type="SWAP",
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal(1),
        contract_value_currency="BTC",
        settlement_currency="USDT",
        list_time=datetime(2025, 1, 1, tzinfo=UTC),
        expiry_time=None,
    )

    manifest = HistoricalDatasetManifest.from_query(
        schema_version=1,
        dataset_id="okx-btc-reference",
        venue="okx",
        source_endpoint="/api/v5/public/market-data-history",
        source_query={"module": "4", "instType": "SPOT"},
        source_files=(source,),
        instruments=(instrument,),
        normalizer_version="okx-history-v1",
        normalized_sha256="b" * 64,
        sample_count=10,
        observed_start=datetime(2026, 1, 1, tzinfo=UTC),
        observed_end=datetime(2026, 1, 1, 1, tzinfo=UTC),
    )

    assert manifest.source_query == (
        ("instType", "SPOT"),
        ("module", "4"),
    )

    with pytest.raises(ValueError, match="SHA-256"):
        HistoricalDatasetManifest.from_query(
            schema_version=1,
            dataset_id="invalid",
            venue="okx",
            source_endpoint="x",
            source_query={},
            source_files=(source,),
            instruments=(instrument,),
            normalizer_version="v1",
            normalized_sha256="not-a-checksum",
            sample_count=1,
            observed_start=datetime(2026, 1, 1, tzinfo=UTC),
            observed_end=datetime(2026, 1, 1, tzinfo=UTC),
        )
