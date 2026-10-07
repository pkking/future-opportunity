from __future__ import annotations

import calendar
from datetime import date
from typing import Any

from future_opportunity.backtest.cash_source_coverage import (
    CASH_WAVE_002_DATES,
    CASH_WAVE_003_DATES,
)


CASH_ALTERNATE_HISTORY_DATES = CASH_WAVE_002_DATES + CASH_WAVE_003_DATES
CASH_APPROVED_FUTURE_ID = "BTC-USDT-260925"
CASH_SPOT_ID = "BTC-USDT"
CASH_ENTRY_TIME_UTC = "00:15:00"


def subtract_calendar_months(value: date, months: int) -> date:
    if months < 0:
        raise ValueError("months must be non-negative")
    year = value.year
    month = value.month - months
    while month <= 0:
        year -= 1
        month += 12
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def trade_retention_eligible(
    market_date: str,
    *,
    probe_date: date,
    retention_months: int = 3,
) -> bool:
    candidate = date.fromisoformat(market_date)
    return candidate >= subtract_calendar_months(probe_date, retention_months)


def classify_alternate_observation(
    observation: dict[str, Any],
) -> str:
    if observation.get("source") == "trades" and not observation.get(
        "retention_eligible",
        True,
    ):
        return "retention_excluded"
    if str(observation.get("okx_code", "")) != "0":
        return "api_error"
    if int(observation.get("target_window_count", 0)) > 0:
        return "target_covered"
    if int(observation.get("returned_count", 0)) > 0:
        return "returned_outside_target"
    return "no_data"


def summarize_alternate_history_coverage(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_dates = set(CASH_ALTERNATE_HISTORY_DATES)
    by_key: dict[str, dict[str, int]] = {}
    seen: set[tuple[str, str, str]] = set()

    for observation in observations:
        source = str(observation["source"])
        instrument_role = str(observation["instrument_role"])
        market_date = str(observation["market_date"])
        if source not in {"candles", "trades"}:
            raise ValueError(f"unsupported alternate source: {source}")
        if instrument_role not in {"future", "spot"}:
            raise ValueError(
                f"unsupported instrument role: {instrument_role}"
            )
        if market_date not in expected_dates:
            raise ValueError(f"unexpected alternate-history date: {market_date}")
        identity = (source, instrument_role, market_date)
        if identity in seen:
            raise ValueError(f"duplicate alternate-history observation: {identity}")
        seen.add(identity)

        state = classify_alternate_observation(observation)
        key = f"{source}:{instrument_role}"
        summary = by_key.setdefault(
            key,
            {
                "total": 0,
                "target_covered": 0,
                "retention_excluded": 0,
                "api_error": 0,
                "returned_outside_target": 0,
                "no_data": 0,
            },
        )
        summary["total"] += 1
        summary[state] += 1

    required = {
        ("candles", role, market_date)
        for role in ("future", "spot")
        for market_date in CASH_ALTERNATE_HISTORY_DATES
    }
    missing_candles = sorted(required - seen)
    if missing_candles:
        raise ValueError(
            f"missing required candlestick observations: {missing_candles}"
        )

    trade_seen = {
        item for item in seen if item[0] == "trades"
    }
    for source, role, market_date in trade_seen:
        if source != "trades" or role not in {"future", "spot"}:
            raise AssertionError("invalid trade observation identity")
        if market_date not in expected_dates:
            raise AssertionError("unexpected trade observation date")

    return {
        "date_count": len(expected_dates),
        "observation_count": len(observations),
        "coverage": by_key,
    }
