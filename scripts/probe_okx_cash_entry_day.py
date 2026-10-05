from __future__ import annotations

import asyncio
import json
import tempfile
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_sampled_archive,
)
from future_opportunity.adapters.persistence.memory import (
    MemoryOpportunityRepository,
)
from future_opportunity.application.discover.cash_and_carry import (
    DiscoverCashAndCarry,
)
from future_opportunity.backtest.alignment import align_order_books
from future_opportunity.backtest.model import HistoricalInstrumentMetadata
from future_opportunity.domain.market.snapshot import CashAndCarryMarketSnapshot
from future_opportunity.domain.strategy.cash_and_carry import (
    CashAndCarryAssumptions,
)


BASE_URL = "https://www.okx.com"
DAY = datetime(2026, 6, 1, tzinfo=UTC)
SAMPLE_START = DAY + timedelta(minutes=15)
SAMPLE_END = DAY + timedelta(hours=23, minutes=45)
CADENCE = timedelta(minutes=15)
MAX_STALENESS = timedelta(seconds=5)
EXPIRY = datetime(2026, 6, 26, 8, tzinfo=UTC)
FUTURE_ID = "BTC-USDT-260626"


def get_json(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> dict[str, Any]:
    for attempt in range(5):
        response = client.get(f"{BASE_URL}{path}", params=params)
        if response.status_code == 429:
            time.sleep(0.75 * (attempt + 1))
            continue
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "0":
            raise RuntimeError(
                f"OKX error {payload.get('code')}: {payload.get('msg')}"
            )
        return payload
    raise RuntimeError("OKX rate limit persisted after retries")


def catalog(
    client: httpx.Client,
    query: OkxHistoricalCatalogQuery,
):
    return parse_okx_history_catalog(
        get_json(client, OKX_HISTORY_ENDPOINT, query.params()),
        query,
    )


def download(client: httpx.Client, url: str, path: Path) -> None:
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with path.open("wb") as output:
            for chunk in response.iter_bytes():
                output.write(chunk)


def future_metadata() -> HistoricalInstrumentMetadata:
    return HistoricalInstrumentMetadata(
        instrument_id=FUTURE_ID,
        instrument_family="BTC-USDT",
        instrument_type="FUTURES",
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal("1"),
        contract_value_currency="BTC",
        settlement_currency="USDT",
        list_time=None,
        expiry_time=EXPIRY,
    )


class HistoricalDayMarketData:
    def __init__(
        self,
        snapshots: tuple[CashAndCarryMarketSnapshot, ...],
    ) -> None:
        self._snapshots = snapshots

    async def snapshots(
        self,
        base: str,
        quote: str = "USDT",
    ) -> tuple[CashAndCarryMarketSnapshot, ...]:
        if base != "BTC" or quote != "USDT":
            return ()
        return self._snapshots

    async def spot_book(self, base: str, quote: str = "USDT"):
        raise NotImplementedError

    async def delivery_settlement(
        self,
        future_instrument_id: str,
        base: str,
        quote: str = "USDT",
    ):
        raise NotImplementedError


async def main() -> None:
    day_ms = int(DAY.timestamp() * 1000)
    spot_query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="SPOT",
        date_aggregation="daily",
        begin_ms=day_ms,
        end_ms=day_ms,
        instrument_ids=("BTC-USDT",),
    )
    future_query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="FUTURES",
        date_aggregation="daily",
        begin_ms=day_ms,
        end_ms=day_ms,
        instrument_families=("BTC-USDT",),
    )

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        spot_sources = catalog(client, spot_query)
        time.sleep(0.5)
        future_sources = catalog(client, future_query)
        spot_source = next(
            item for item in spot_sources if item.instrument_id == "BTC-USDT"
        )
        future_source = next(
            item
            for item in future_sources
            if item.instrument_family == "BTC-USDT"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            spot_raw = root / spot_source.filename
            future_raw = root / future_source.filename
            download(client, spot_source.url, spot_raw)
            download(client, future_source.url, future_raw)

            spot = tuple(
                iter_okx_l2_sampled_archive(
                    spot_raw,
                    instrument_type="SPOT",
                    expected_instrument_id="BTC-USDT",
                    start=SAMPLE_START,
                    end=SAMPLE_END,
                    cadence=CADENCE,
                )
            )
            future = tuple(
                iter_okx_l2_sampled_archive(
                    future_raw,
                    instrument_type="FUTURES",
                    expected_instrument_id=FUTURE_ID,
                    start=SAMPLE_START,
                    end=SAMPLE_END,
                    cadence=CADENCE,
                    metadata=future_metadata(),
                )
            )

    alignment = align_order_books(
        spot,
        future,
        start=SAMPLE_START,
        end=SAMPLE_END,
        cadence=CADENCE,
        max_staleness=MAX_STALENESS,
    )
    snapshots = tuple(
        CashAndCarryMarketSnapshot(
            venue="okx",
            base="BTC",
            quote="USDT",
            spot_instrument_id="okx:BTC-USDT:spot",
            future_instrument_id=f"okx:{FUTURE_ID}:future",
            spot_book=pair.spot.book,
            future_book=pair.hedge.book,
            expiry=EXPIRY,
            observed_at=pair.sampled_at,
        )
        for pair in alignment.samples
    )
    discovered = await DiscoverCashAndCarry(
        HistoricalDayMarketData(snapshots),
        MemoryOpportunityRepository(),
    ).execute(
        "BTC",
        Decimal("10000"),
        CashAndCarryAssumptions(),
    )

    rows = [
        {
            "observed_at": item.snapshot.observed_at.isoformat(),
            "spot_ask": str(item.snapshot.spot_book.best_ask),
            "future_bid": str(item.snapshot.future_book.best_bid),
            "gross_basis_return_on_notional": str(
                item.evaluation.gross_basis_return_on_notional
            ),
            "expected_net_return": str(
                item.evaluation.expected_net_return_to_expiry
            ),
            "annualized_equivalent": str(
                item.evaluation.annualized_equivalent
            ),
            "qualified": item.qualification.qualified,
            "reasons": list(item.qualification.reasons),
            "capacity_10bps": str(item.evaluation.visible_capacity_10bps),
        }
        for item in discovered
    ]
    expected_values = [
        Decimal(row["expected_net_return"])
        for row in rows
    ]
    qualified = [row for row in rows if row["qualified"]]
    best_index = max(
        range(len(rows)),
        key=lambda index: expected_values[index],
    )
    worst_index = min(
        range(len(rows)),
        key=lambda index: expected_values[index],
    )
    fixed_hours = {0, 6, 12, 18}
    representative = [
        row
        for row in rows
        if datetime.fromisoformat(row["observed_at"]).hour in fixed_hours
        and datetime.fromisoformat(row["observed_at"]).minute == 15
    ]

    report = {
        "schema_version": 1,
        "evidence_type": "cash_and_carry_entry_day_scan",
        "dataset": {
            "date": DAY.date().isoformat(),
            "future_instrument_id": FUTURE_ID,
            "expiry": EXPIRY.isoformat(),
            "entry_cadence_seconds": int(CADENCE.total_seconds()),
            "max_staleness_seconds": int(MAX_STALENESS.total_seconds()),
            "spot_source": {
                "filename": spot_source.filename,
                "url": spot_source.url,
            },
            "future_source": {
                "filename": future_source.filename,
                "url": future_source.url,
            },
            "future_metadata_provenance": {
                "type": "official_product_spec",
                "contract_value": "0.01",
                "contract_multiplier": "1",
                "contract_value_currency": "BTC",
            },
        },
        "alignment": {
            "requested_samples": alignment.requested_samples,
            "emitted_samples": alignment.emitted_samples,
            "coverage_ratio": str(alignment.coverage_ratio),
            "stale_spot_samples": alignment.stale_spot_samples,
            "stale_future_samples": alignment.stale_hedge_samples,
        },
        "summary": {
            "sample_count": len(rows),
            "qualified_count": len(qualified),
            "qualification_rate": str(
                Decimal(len(qualified)) / Decimal(len(rows))
                if rows
                else Decimal(0)
            ),
            "mean_expected_net_return": str(
                sum(expected_values, Decimal(0))
                / Decimal(len(expected_values))
            ),
            "median_expected_net_return": str(median(expected_values)),
            "best": rows[best_index],
            "worst": rows[worst_index],
            "fixed_representative_samples": representative,
        },
        "samples": rows,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
