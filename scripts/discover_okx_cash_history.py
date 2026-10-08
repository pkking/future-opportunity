from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.backtest.cash_discovery import (
    find_delivery_evidence,
    future_ids_from_archive_members,
)


BASE_URL = "https://www.okx.com"
DELIVERY_PATH = "/api/v5/public/delivery-exercise-history"
MAX_RAW_MB = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("market_date")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


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


def download(
    client: httpx.Client,
    url: str,
    path: Path,
) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    limit = MAX_RAW_MB * 1024 * 1024
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with path.open("wb") as output:
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > limit:
                    raise RuntimeError(
                        f"future archive exceeded {MAX_RAW_MB} MiB"
                    )
                digest.update(chunk)
                output.write(chunk)
    return digest.hexdigest(), total


def source_view(source) -> dict[str, Any]:
    result = asdict(source)
    for key, value in tuple(result.items()):
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = str(value)
    return result


def delivery_view(
    payload: dict[str, Any],
    *,
    future_id: str,
) -> dict[str, Any]:
    delivery = find_delivery_evidence(payload, future_id=future_id)
    if delivery is None:
        return {
            "status": "unassessed",
            "endpoint": f"{BASE_URL}{DELIVERY_PATH}",
            "reason": (
                "public delivery history response did not contain "
                "the discovered historical future"
            ),
        }
    return {
        "status": "verified",
        "endpoint": f"{BASE_URL}{DELIVERY_PATH}",
        "delivered_at": delivery.delivered_at.isoformat(),
        "settlement_price": str(delivery.settlement_price),
    }


def product_spec_provenance() -> dict[str, str]:
    return {
        "status": "verified_product_rule",
        "official_doc": "https://www.okx.com/help/expiry-futures",
        "contract_value": "0.01",
        "contract_multiplier": "1",
        "contract_value_currency": "BTC",
        "settlement_currency": "USDT",
        "note": (
            "product-level BTCUSDT expiry-futures specification; "
            "not a reconstructed historical instrument row"
        ),
    }


def main() -> None:
    args = parse_args()
    day = datetime.fromisoformat(args.market_date).replace(tzinfo=UTC)
    canonical_date = day.date().isoformat()
    day_ms = int(day.timestamp() * 1000)

    query = OkxHistoricalCatalogQuery(
        module="4",
        instrument_type="FUTURES",
        date_aggregation="daily",
        begin_ms=day_ms,
        end_ms=day_ms,
        instrument_families=("BTC-USDT",),
    )

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        catalog_payload = get_json(
            client,
            OKX_HISTORY_ENDPOINT,
            query.params(),
        )
        files = parse_okx_history_catalog(catalog_payload, query)
        candidates = [
            item
            for item in files
            if item.instrument_family == "BTC-USDT"
        ]
        if len(candidates) != 1:
            report = {
                "schema_version": 1,
                "market_date": canonical_date,
                "status": "no_unique_future_chain_archive",
                "query": query.params(),
                "candidate_count": len(candidates),
                "candidates": [source_view(item) for item in candidates],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n"
            )
            return

        source = candidates[0]
        with tempfile.TemporaryDirectory() as temporary:
            raw_path = Path(temporary) / source.filename
            raw_sha, raw_bytes = download(client, source.url, raw_path)
            with tarfile.open(raw_path, "r:gz") as archive:
                members = tuple(
                    sorted(
                        item.name
                        for item in archive.getmembers()
                        if item.isfile() and item.name.endswith(".data")
                    )
                )
            future_ids = future_ids_from_archive_members(
                members,
                expected_market_date=canonical_date,
            )

        delivery_payload = get_json(
            client,
            DELIVERY_PATH,
            {
                "instType": "FUTURES",
                "instFamily": "BTC-USDT",
            },
        )

    catalog = {
        "endpoint": f"{BASE_URL}{OKX_HISTORY_ENDPOINT}",
        "query": query.params(),
        "source": source_view(source),
        "raw_sha256": raw_sha,
        "downloaded_bytes": raw_bytes,
        "archive_members": list(members),
    }

    if len(future_ids) > 1:
        report = {
            "schema_version": 1,
            "market_date": canonical_date,
            "status": "multiple_future_contracts",
            "catalog": catalog,
            "future_candidates": [
                {
                    "instrument_id": future_id,
                    "delivery_evidence": delivery_view(
                        delivery_payload,
                        future_id=future_id,
                    ),
                    "product_spec_provenance": product_spec_provenance(),
                }
                for future_id in future_ids
            ],
            "note": (
                "The historical future-chain archive contains multiple expiry "
                "contracts. Discovery intentionally does not choose a contract "
                "or holding period."
            ),
        }
    else:
        future_id = future_ids[0]
        report = {
            "schema_version": 1,
            "market_date": canonical_date,
            "status": "future_discovered",
            "catalog": {
                **catalog,
                "archive_member": members[0],
            },
            "future": {
                "instrument_id": future_id,
                "delivery_evidence": delivery_view(
                    delivery_payload,
                    future_id=future_id,
                ),
                "product_spec_provenance": product_spec_provenance(),
            },
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
