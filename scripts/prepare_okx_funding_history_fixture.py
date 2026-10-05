from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.adapters.historical.okx_funding import (
    iter_okx_funding_archive,
)
from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_sampled_archive,
)
from future_opportunity.backtest.alignment import align_order_books
from future_opportunity.backtest.canonical import (
    iter_canonical_order_books,
    write_canonical_funding,
    write_canonical_order_books,
)
from future_opportunity.backtest.model import HistoricalInstrumentMetadata


BASE_URL = "https://www.okx.com"
INSTRUMENTS_PATH = "/api/v5/public/instruments"
OUTPUT = Path(
    os.getenv(
        "HISTORICAL_FIXTURE_DIR",
        "artifacts/historical-fixture",
    )
)
HISTORY_DATE = os.getenv("HISTORY_DATE", "2026-09-01")
CADENCE_SECONDS = int(os.getenv("HISTORY_CADENCE_SECONDS", "900"))
MAX_STALENESS_SECONDS = int(os.getenv("HISTORY_MAX_STALENESS_SECONDS", "5"))
MAX_RAW_MB = int(os.getenv("HISTORY_MAX_RAW_MB", "600"))


def _request_json(
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


def _catalog(
    client: httpx.Client,
    query: OkxHistoricalCatalogQuery,
):
    payload = _request_json(client, OKX_HISTORY_ENDPOINT, query.params())
    return parse_okx_history_catalog(payload, query)


def _source_file(
    files,
    *,
    instrument_id: str = "",
    instrument_family: str = "",
):
    matches = [
        item
        for item in files
        if (
            (not instrument_id or item.instrument_id == instrument_id)
            and (
                not instrument_family
                or item.instrument_family == instrument_family
            )
        )
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one historical source file, "
            f"got {len(matches)} for {instrument_id or instrument_family}"
        )
    return matches[0]


def _download(
    client: httpx.Client,
    url: str,
    destination: Path,
) -> tuple[str, int]:
    import hashlib

    digest = hashlib.sha256()
    total = 0
    hard_limit = MAX_RAW_MB * 1024 * 1024

    with client.stream("GET", url) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > hard_limit:
                    raise RuntimeError(
                        f"raw archive exceeded {MAX_RAW_MB} MiB limit"
                    )
                digest.update(chunk)
                output.write(chunk)
    return digest.hexdigest(), total


def _parse_ms(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def _swap_metadata(
    client: httpx.Client,
) -> HistoricalInstrumentMetadata:
    payload = _request_json(
        client,
        INSTRUMENTS_PATH,
        {"instType": "SWAP", "instFamily": "BTC-USDT"},
    )
    rows = [
        row
        for row in payload.get("data", [])
        if row.get("instId") == "BTC-USDT-SWAP"
    ]
    if len(rows) != 1:
        raise RuntimeError("unable to resolve BTC-USDT-SWAP metadata")
    row = rows[0]
    for required in ("ctVal", "ctMult", "ctValCcy", "settleCcy"):
        if not row.get(required):
            raise RuntimeError(
                f"BTC-USDT-SWAP metadata is missing {required}"
            )
    return HistoricalInstrumentMetadata(
        instrument_id="BTC-USDT-SWAP",
        instrument_family="BTC-USDT",
        instrument_type="SWAP",
        contract_value=Decimal(str(row["ctVal"])),
        contract_multiplier=Decimal(str(row["ctMult"])),
        contract_value_currency=str(row["ctValCcy"]),
        settlement_currency=str(row["settleCcy"]),
        list_time=_parse_ms(str(row.get("listTime", ""))),
        expiry_time=_parse_ms(str(row.get("expTime", ""))),
    )


def _source_view(source, raw_sha256: str, downloaded_bytes: int) -> dict[str, Any]:
    view = asdict(source)
    for key in ("date_range_start", "date_range_end", "data_date"):
        view[key] = view[key].isoformat()
    view["raw_sha256"] = raw_sha256
    view["downloaded_bytes"] = downloaded_bytes
    return view


def main() -> None:
    day = datetime.fromisoformat(HISTORY_DATE).replace(tzinfo=UTC)
    day_end = day + timedelta(days=1)
    sample_end = day_end - timedelta(seconds=CADENCE_SECONDS)
    cadence = timedelta(seconds=CADENCE_SECONDS)
    max_staleness = timedelta(seconds=MAX_STALENESS_SECONDS)
    daily_ms = int(day.timestamp() * 1000)
    month = day.replace(day=1)
    monthly_ms = int(month.timestamp() * 1000)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    spot_query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="SPOT",
        date_aggregation="daily",
        begin_ms=daily_ms,
        end_ms=daily_ms,
        instrument_ids=("BTC-USDT",),
    )
    swap_query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="SWAP",
        date_aggregation="daily",
        begin_ms=daily_ms,
        end_ms=daily_ms,
        instrument_families=("BTC-USDT",),
    )
    funding_query = OkxHistoricalCatalogQuery(
        module="3",
        instrument_type="SWAP",
        date_aggregation="monthly",
        begin_ms=monthly_ms,
        end_ms=monthly_ms,
        instrument_families=("BTC-USDT",),
    )

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        spot_source = _source_file(
            _catalog(client, spot_query),
            instrument_id="BTC-USDT",
        )
        time.sleep(0.5)
        swap_source = _source_file(
            _catalog(client, swap_query),
            instrument_family="BTC-USDT",
        )
        time.sleep(0.5)
        funding_source = _source_file(
            _catalog(client, funding_query),
            instrument_family="BTC-USDT",
        )
        time.sleep(0.5)
        swap_metadata = _swap_metadata(client)

        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            spot_raw = temp / spot_source.filename
            swap_raw = temp / swap_source.filename
            funding_raw = temp / funding_source.filename

            spot_sha, spot_bytes = _download(
                client,
                spot_source.url,
                spot_raw,
            )
            swap_sha, swap_bytes = _download(
                client,
                swap_source.url,
                swap_raw,
            )
            funding_sha, funding_bytes = _download(
                client,
                funding_source.url,
                funding_raw,
            )

            spot_path = OUTPUT / "btc-usdt-spot-books.jsonl"
            swap_path = OUTPUT / "btc-usdt-swap-books.jsonl"
            funding_path = OUTPUT / "btc-usdt-swap-funding.jsonl"

            spot_summary = write_canonical_order_books(
                iter_okx_l2_sampled_archive(
                    spot_raw,
                    instrument_type="SPOT",
                    expected_instrument_id="BTC-USDT",
                    start=day,
                    end=sample_end,
                    cadence=cadence,
                ),
                spot_path,
            )
            swap_summary = write_canonical_order_books(
                iter_okx_l2_sampled_archive(
                    swap_raw,
                    instrument_type="SWAP",
                    expected_instrument_id="BTC-USDT-SWAP",
                    start=day,
                    end=sample_end,
                    cadence=cadence,
                    metadata=swap_metadata,
                ),
                swap_path,
            )
            funding_summary = write_canonical_funding(
                (
                    observation
                    for observation in iter_okx_funding_archive(
                        funding_raw,
                        expected_instrument_id="BTC-USDT-SWAP",
                    )
                    if day <= observation.funding_time < day_end
                ),
                funding_path,
            )

    alignment = align_order_books(
        iter_canonical_order_books(spot_path),
        iter_canonical_order_books(swap_path),
        start=day,
        end=sample_end,
        cadence=cadence,
        max_staleness=max_staleness,
    )

    manifest = {
        "schema_version": 1,
        "dataset_id": f"okx-btc-usdt-funding-carry-{HISTORY_DATE}-v1",
        "venue": "okx",
        "base": "BTC",
        "quote": "USDT",
        "history_date_utc": HISTORY_DATE,
        "cadence_seconds": CADENCE_SECONDS,
        "max_staleness_seconds": MAX_STALENESS_SECONDS,
        "source_endpoint": f"{BASE_URL}{OKX_HISTORY_ENDPOINT}",
        "sources": {
            "spot_l2": {
                "query": spot_query.params(),
                "file": _source_view(
                    spot_source,
                    spot_sha,
                    spot_bytes,
                ),
            },
            "swap_l2": {
                "query": swap_query.params(),
                "file": _source_view(
                    swap_source,
                    swap_sha,
                    swap_bytes,
                ),
            },
            "funding": {
                "query": funding_query.params(),
                "file": _source_view(
                    funding_source,
                    funding_sha,
                    funding_bytes,
                ),
            },
        },
        "instrument_metadata": {
            key: (
                value.isoformat()
                if isinstance(value, datetime)
                else str(value)
                if isinstance(value, Decimal)
                else value
            )
            for key, value in asdict(swap_metadata).items()
        },
        "normalized": {
            "spot_books": {
                "path": spot_path.name,
                "sha256": spot_summary.sha256,
                "sample_count": spot_summary.sample_count,
                "observed_start": spot_summary.observed_start.isoformat(),
                "observed_end": spot_summary.observed_end.isoformat(),
            },
            "swap_books": {
                "path": swap_path.name,
                "sha256": swap_summary.sha256,
                "sample_count": swap_summary.sample_count,
                "observed_start": swap_summary.observed_start.isoformat(),
                "observed_end": swap_summary.observed_end.isoformat(),
            },
            "funding": {
                "path": funding_path.name,
                "sha256": funding_summary.sha256,
                "sample_count": funding_summary.sample_count,
                "observed_start": funding_summary.observed_start.isoformat(),
                "observed_end": funding_summary.observed_end.isoformat(),
            },
        },
        "alignment": {
            "requested_samples": alignment.requested_samples,
            "emitted_samples": alignment.emitted_samples,
            "coverage_ratio": str(alignment.coverage_ratio),
            "missing_spot_samples": alignment.missing_spot_samples,
            "missing_hedge_samples": alignment.missing_hedge_samples,
            "stale_spot_samples": alignment.stale_spot_samples,
            "stale_hedge_samples": alignment.stale_hedge_samples,
        },
        "evidence_limits": {
            "funding_mark_price": "unassessed",
            "reason": (
                "official funding archive contains funding rate/time only; "
                "mark-price evidence must be pinned separately"
            ),
        },
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
