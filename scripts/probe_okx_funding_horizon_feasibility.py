from __future__ import annotations

import json
import tempfile
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx

from future_opportunity.adapters.historical.okx_catalog import (
    OKX_HISTORY_ENDPOINT,
    OkxHistoricalCatalogQuery,
    parse_okx_history_catalog,
)
from future_opportunity.adapters.historical.okx_funding import (
    iter_okx_funding_archive,
)
from future_opportunity.domain.market.snapshot import (
    FundingCarryMarketSnapshot,
    FundingObservation,
    OrderBook,
    OrderBookLevel,
)
from future_opportunity.domain.strategy.funding_carry import (
    FundingCarryAssumptions,
    evaluate_funding_carry,
)


BASE_URL = "https://www.okx.com"


def get_json(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> dict:
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


def download(client: httpx.Client, url: str, path: Path) -> None:
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with path.open("wb") as output:
            for chunk in response.iter_bytes():
                output.write(chunk)


def optimistic_snapshot(
    observed_at: datetime,
    funding_history: tuple[FundingObservation, ...],
) -> FundingCarryMarketSnapshot:
    book = OrderBook(
        bids=(
            OrderBookLevel(
                price=Decimal("100"),
                quantity=Decimal("1000000000"),
            ),
        ),
        asks=(
            OrderBookLevel(
                price=Decimal("100"),
                quantity=Decimal("1000000000"),
            ),
        ),
        observed_at=observed_at,
    )
    prior = tuple(
        item for item in funding_history if item.funding_time <= observed_at
    )
    future = tuple(
        item for item in funding_history if item.funding_time > observed_at
    )
    if not prior:
        raise RuntimeError("no prior funding observations")
    return FundingCarryMarketSnapshot(
        venue="okx",
        base="BTC",
        quote="USDT",
        spot_instrument_id="probe:spot",
        perpetual_instrument_id="probe:perp",
        spot_book=book,
        perpetual_book=book,
        mark_price=Decimal("100"),
        last_funding_rate=prior[-1].rate,
        next_funding_time=(
            future[0].funding_time
            if future
            else prior[-1].funding_time
        ),
        funding_history=prior,
        observed_at=observed_at,
    )


def main() -> None:
    august = datetime(2026, 8, 1, tzinfo=UTC)
    september = datetime(2026, 9, 1, tzinfo=UTC)
    query = OkxHistoricalCatalogQuery(
        module="3",
        instrument_type="SWAP",
        date_aggregation="monthly",
        begin_ms=int(august.timestamp() * 1000),
        end_ms=int(september.timestamp() * 1000),
        instrument_families=("BTC-USDT",),
    )

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        payload = get_json(client, OKX_HISTORY_ENDPOINT, query.params())
        sources = parse_okx_history_catalog(payload, query)
        if len(sources) != 2:
            raise RuntimeError(
                f"expected two funding archives, got {len(sources)}"
            )

        observations = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source in sources:
                archive = root / source.filename
                download(client, source.url, archive)
                observations.extend(
                    iter_okx_funding_archive(
                        archive,
                        expected_instrument_id="BTC-USDT-SWAP",
                    )
                )

    observations.sort(key=lambda item: item.funding_time)
    history = tuple(
        FundingObservation(
            rate=item.funding_rate,
            funding_time=item.funding_time,
            rate_type="historical",
        )
        for item in observations
    )

    scenarios = (
        (
            "sep01-7d",
            datetime(2026, 9, 1, 0, 15, tzinfo=UTC),
            7,
        ),
        (
            "sep08-22d",
            datetime(2026, 9, 8, 0, 15, tzinfo=UTC),
            22,
        ),
        (
            "sep01-29d",
            datetime(2026, 9, 1, 0, 15, tzinfo=UTC),
            29,
        ),
    )
    result = {
        "schema_version": 1,
        "evidence_type": "funding_horizon_optimistic_feasibility",
        "meaning": (
            "Uses real official funding history and the production Funding Carry "
            "economics formula with zero slippage/infinite liquidity. Net return "
            "is therefore an optimistic upper bound before real L2 impact."
        ),
        "query": query.params(),
        "source_files": [
            {
                "filename": item.filename,
                "url": item.url,
                "data_date": item.data_date.isoformat(),
            }
            for item in sources
        ],
        "scenarios": {},
    }
    for name, entry, horizon_days in scenarios:
        evaluation = evaluate_funding_carry(
            optimistic_snapshot(entry, history),
            Decimal("10000"),
            FundingCarryAssumptions(horizon_days=horizon_days),
        )
        result["scenarios"][name] = {
            "entry_at": entry.isoformat(),
            "horizon_days": horizon_days,
            "expected_funding_rate_per_period": str(
                evaluation.expected_funding_rate_per_period
            ),
            "funding_periods_per_day": str(
                evaluation.funding_periods_per_day
            ),
            "gross_return_horizon": str(
                evaluation.gross_return_horizon
            ),
            "round_trip_fee_return": str(
                evaluation.assumed_round_trip_fee_return
            ),
            "slippage_return": str(
                evaluation.estimated_round_trip_slippage_return
            ),
            "optimistic_net_return": str(
                evaluation.expected_net_return_horizon
            ),
            "annualized_equivalent": str(
                evaluation.annualized_equivalent
            ),
            "positive_funding_ratio_7d": str(
                evaluation.positive_funding_ratio_7d
            ),
        }

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
