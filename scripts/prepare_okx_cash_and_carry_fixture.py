from __future__ import annotations

import hashlib
import json
import os
import tarfile
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
from future_opportunity.adapters.historical.okx_l2 import (
    iter_okx_l2_sampled_archive,
)
from future_opportunity.backtest.canonical import write_canonical_order_books
from future_opportunity.backtest.model import HistoricalInstrumentMetadata


BASE_URL = "https://www.okx.com"
OUTPUT = Path(
    os.getenv(
        "CASH_HISTORICAL_FIXTURE_DIR",
        "artifacts/cash-historical-fixture",
    )
)
def env_datetime(name: str, default: str) -> datetime:
    raw = os.getenv(name, default)
    value = datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


ENTRY_AT = env_datetime(
    "CASH_ENTRY_AT",
    "2026-06-01T00:15:00+00:00",
)
EXIT_AT = env_datetime(
    "CASH_EXIT_AT",
    "2026-06-25T00:15:00+00:00",
)
EXPIRY = env_datetime(
    "CASH_EXPIRY_AT",
    "2026-06-26T08:00:00+00:00",
)
RAW_FUTURE_ID = os.getenv("CASH_FUTURE_ID", "BTC-USDT-260626")
MAX_RAW_MB = int(os.getenv("CASH_HISTORY_MAX_RAW_MB", "600"))
MAX_STALENESS_MS = int(os.getenv("CASH_HISTORY_MAX_STALENESS_MS", "5000"))


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


def source_file(
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
            "expected one historical file, got "
            f"{len(matches)} for {instrument_id or instrument_family}"
        )
    return matches[0]


def download(
    client: httpx.Client,
    url: str,
    destination: Path,
) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    limit = MAX_RAW_MB * 1024 * 1024
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > limit:
                    raise RuntimeError(
                        f"raw archive exceeded {MAX_RAW_MB} MiB"
                    )
                digest.update(chunk)
                output.write(chunk)
    return digest.hexdigest(), total


def archive_member(path: Path) -> str:
    with tarfile.open(path, "r:gz") as archive:
        members = [
            item.name
            for item in archive.getmembers()
            if item.isfile() and item.name.endswith(".data")
        ]
    if len(members) != 1:
        raise RuntimeError(
            "historical L2 archive must contain exactly one .data member"
        )
    return members[0]


def source_view(
    source,
    *,
    raw_sha256: str,
    downloaded_bytes: int,
    member: str,
) -> dict[str, Any]:
    view = asdict(source)
    for key, value in tuple(view.items()):
        if isinstance(value, datetime):
            view[key] = value.isoformat()
        elif isinstance(value, Decimal):
            view[key] = str(value)
    view["raw_sha256"] = raw_sha256
    view["downloaded_bytes"] = downloaded_bytes
    view["archive_member"] = member
    return view


def query_for(
    sample_at: datetime,
    *,
    instrument_type: str,
) -> OkxHistoricalCatalogQuery:
    day_ms = int(
        sample_at.replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
        * 1000
    )
    if instrument_type == "SPOT":
        return OkxHistoricalCatalogQuery(
            module="4",
            instrument_type="SPOT",
            date_aggregation="daily",
            begin_ms=day_ms,
            end_ms=day_ms,
            instrument_ids=("BTC-USDT",),
        )
    return OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="FUTURES",
        date_aggregation="daily",
        begin_ms=day_ms,
        end_ms=day_ms,
        instrument_families=("BTC-USDT",),
    )


def future_metadata() -> HistoricalInstrumentMetadata:
    return HistoricalInstrumentMetadata(
        instrument_id=RAW_FUTURE_ID,
        instrument_family="BTC-USDT",
        instrument_type="FUTURES",
        contract_value=Decimal("0.01"),
        contract_multiplier=Decimal("1"),
        contract_value_currency="BTC",
        settlement_currency="USDT",
        list_time=None,
        expiry_time=EXPIRY,
    )


def prepare_component(
    client: httpx.Client,
    temporary: Path,
    *,
    name: str,
    sample_at: datetime,
    instrument_type: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    query = query_for(sample_at, instrument_type=instrument_type)
    files = catalog(client, query)
    if instrument_type == "SPOT":
        source = source_file(files, instrument_id="BTC-USDT")
        expected_id = "BTC-USDT"
        metadata = None
    else:
        source = source_file(files, instrument_family="BTC-USDT")
        expected_id = RAW_FUTURE_ID
        metadata = future_metadata()

    raw_path = temporary / source.filename
    raw_sha, raw_bytes = download(client, source.url, raw_path)
    member = archive_member(raw_path)
    if instrument_type == "FUTURES" and RAW_FUTURE_ID not in member:
        raise RuntimeError(
            f"future chain member does not contain {RAW_FUTURE_ID}: {member}"
        )

    output_path = OUTPUT / f"{name}.jsonl"
    summary = write_canonical_order_books(
        iter_okx_l2_sampled_archive(
            raw_path,
            instrument_type=instrument_type,
            expected_instrument_id=expected_id,
            start=sample_at,
            end=sample_at,
            cadence=timedelta(minutes=15),
            metadata=metadata,
        ),
        output_path,
    )
    if summary.sample_count != 1:
        raise RuntimeError(
            f"{name} expected exactly one sampled book, "
            f"got {summary.sample_count}"
        )

    from future_opportunity.backtest.canonical import iter_canonical_order_books

    observation = tuple(iter_canonical_order_books(output_path))[0]
    age_ms = int(
        (sample_at - observation.observed_at).total_seconds() * 1000
    )
    if age_ms < 0 or age_ms > MAX_STALENESS_MS:
        raise RuntimeError(
            f"{name} age {age_ms}ms exceeds {MAX_STALENESS_MS}ms"
        )

    normalized = {
        "path": output_path.name,
        "sha256": summary.sha256,
        "source_line": observation.source_line,
        "observed_at": observation.observed_at.isoformat(),
        "sample_at": sample_at.isoformat(),
        "age_ms": age_ms,
        "best_bid": str(observation.book.best_bid),
        "best_ask": str(observation.book.best_ask),
    }
    provenance = {
        "query": query.params(),
        "file": source_view(
            source,
            raw_sha256=raw_sha,
            downloaded_bytes=raw_bytes,
            member=member,
        ),
    }
    return normalized, provenance


def main() -> None:
    if not RAW_FUTURE_ID.startswith("BTC-USDT-"):
        raise ValueError("CASH_FUTURE_ID must identify a BTC-USDT expiry future")
    if not ENTRY_AT < EXIT_AT < EXPIRY:
        raise ValueError(
            "Cash historical times must satisfy entry < exit < expiry"
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary = Path(temp_dir)
            components = {}
            sources = {}
            for name, sample_at, instrument_type in (
                ("entry_spot", ENTRY_AT, "SPOT"),
                ("entry_future", ENTRY_AT, "FUTURES"),
                ("exit_spot", EXIT_AT, "SPOT"),
                ("exit_future", EXIT_AT, "FUTURES"),
            ):
                normalized, provenance = prepare_component(
                    client,
                    temporary,
                    name=name,
                    sample_at=sample_at,
                    instrument_type=instrument_type,
                )
                components[name] = normalized
                sources[name] = provenance
                time.sleep(0.5)

    manifest = {
        "schema_version": 1,
        "strategy": "cash-and-carry",
        "close_mode": "pre-expiry",
        "dataset_id": (
            "okx-btc-usdt-cash-and-carry-"
            f"{ENTRY_AT.date().isoformat()}-{RAW_FUTURE_ID}-v1"
        ),
        "entry_market_date": ENTRY_AT.date().isoformat(),
        "venue": "okx",
        "base": "BTC",
        "quote": "USDT",
        "sample_times": {
            "entry": ENTRY_AT.isoformat(),
            "exit": EXIT_AT.isoformat(),
        },
        "max_staleness_ms": MAX_STALENESS_MS,
        "instrument": {
            "future_instrument_id": RAW_FUTURE_ID,
            "expiry": EXPIRY.isoformat(),
            "metadata_provenance": {
                "type": "official_product_spec",
                "official_doc": "https://www.okx.com/help/expiry-futures",
                "contract_value": "0.01",
                "contract_multiplier": "1",
                "contract_value_currency": "BTC",
                "settlement_currency": "USDT",
                "delivery_rule": "Friday 08:00 UTC",
                "input_contract": {
                    "future_instrument_id": RAW_FUTURE_ID,
                    "expiry": EXPIRY.isoformat(),
                },
                "note": (
                    "Contract value/multiplier are documented BTCUSDT "
                    "expiry-futures product specifications. The concrete "
                    "historical future ID and expiry are explicit preparation "
                    "inputs, not reconstructed from the current-instrument API."
                ),
            },
        },
        "sources": sources,
        "normalized": components,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
