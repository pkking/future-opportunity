from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from future_opportunity.backtest.funding_regime_research import POLICY_VERSION


FUNDING_INSTRUMENT = "BTC-USDT-SWAP"
SPOT_INSTRUMENT = "BTC-USDT"
FUNDING_ENDPOINT = "/api/v5/public/funding-rate-history"
SPOT_ENDPOINT = "/api/v5/market/history-candles"
FUNDING_MIN_AGE = timedelta(hours=1)
FUNDING_MAX_AGE = timedelta(hours=36)
VOLATILITY_RETURNS = 7
MAX_STUDY_DAYS = 31


def _canonical(raw: Any) -> bytes:
    return (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _digest(raw: Any) -> str:
    return hashlib.sha256(_canonical(raw)).hexdigest()


def _moment_ms(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(f"{field} must be a millisecond timestamp string")
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError) as error:
        raise ValueError(f"{field} timestamp is out of range") from error


def _finite(raw: Any, field: str, *, positive: bool = False) -> Decimal:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be a decimal string")
    try:
        value = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(f"{field} must be decimal") from error
    if not value.is_finite() or (positive and value <= 0):
        raise ValueError(f"{field} must be finite" + (" and positive" if positive else ""))
    return value


def _source_rows(payload: Any, name: str) -> list[Any]:
    if not isinstance(payload, dict) or payload.get("code") != "0":
        raise ValueError(f"{name} requires an OKX success response")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError(f"{name} response data must be an array")
    return rows


def _funding_index(payload: dict[str, Any]) -> dict[datetime, dict[str, Any]]:
    rows: dict[datetime, dict[str, Any]] = {}
    for item in _source_rows(payload, "funding"):
        if not isinstance(item, dict) or item.get("instId") != FUNDING_INSTRUMENT:
            raise ValueError("funding record instrument must be BTC-USDT-SWAP")
        if item.get("instType") != "SWAP":
            raise ValueError("funding record instrument type must be SWAP")
        moment = _moment_ms(item.get("fundingTime"), "fundingTime")
        if moment in rows:
            raise ValueError("duplicate funding settlement timestamp")
        # Historical settlement rate, not a predicted next-period quote.
        _finite(item.get("realizedRate"), "realizedRate")
        rows[moment] = item
    return rows


def _spot_index(payload: dict[str, Any]) -> dict[datetime, list[Any]]:
    rows: dict[datetime, list[Any]] = {}
    for item in _source_rows(payload, "spot"):
        if not isinstance(item, list) or len(item) < 9:
            raise ValueError("spot daily candle must contain 9 API fields")
        open_at = _moment_ms(item[0], "spot candle ts")
        if open_at.hour or open_at.minute or open_at.second or open_at.microsecond:
            raise ValueError("spot daily candle must open at UTC midnight")
        if open_at in rows:
            raise ValueError("duplicate spot daily candle timestamp")
        _finite(item[4], "spot candle close", positive=True)
        if item[8] not in ("0", "1"):
            raise ValueError("spot candle confirm must be 0 or 1")
        rows[open_at] = item
    return rows


def _volatility_window(
    spot: dict[datetime, list[Any]], entry: datetime
) -> tuple[Decimal, list[list[Any]]] | None:
    # Seven fully closed UTC daily log returns require eight completed candles.
    opens = [entry - timedelta(days=i) for i in range(8, 0, -1)]
    candles: list[list[Any]] = []
    for opened_at in opens:
        row = spot.get(opened_at)
        if row is None or row[8] != "1":
            return None
        if opened_at + timedelta(days=1) > entry:
            raise ValueError("spot candle close would be after entry")
        candles.append(row)
    prices = [_finite(row[4], "spot close", positive=True) for row in candles]
    returns = [
        (prices[i] / prices[i - 1]).ln()
        for i in range(1, len(prices))
    ]
    mean = sum(returns, Decimal(0)) / Decimal(VOLATILITY_RETURNS)
    variance = sum(((r - mean) ** 2 for r in returns), Decimal(0)) / Decimal(
        VOLATILITY_RETURNS
    )
    return variance.sqrt() * Decimal(10000), candles


def reconstruct_funding_regime_features(
    capture: dict[str, Any],
) -> dict[str, Any]:
    """Derive retrospective, event-time-only Funding regime features.

    API response contents/digests are reproducible, but retrospective retrieval
    does NOT authenticate the historical publication time of the records.
    """
    expected = {
        "schema_version", "captured_at", "start_date", "end_date",
        "seed", "requested_per_regime", "pinned_market_dates",
        "funding_query", "funding_response", "spot_query", "spot_response",
    }
    if not isinstance(capture, dict) or set(capture) != expected:
        raise ValueError("raw Funding capture fields differ from schema")
    if capture["schema_version"] != 1:
        raise ValueError("unsupported Funding raw capture schema")
    captured_at = datetime.fromisoformat(capture["captured_at"])
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must have a timezone")
    start, end = date.fromisoformat(capture["start_date"]), date.fromisoformat(
        capture["end_date"]
    )
    if start > end or (end - start).days >= MAX_STUDY_DAYS:
        raise ValueError("Funding raw study window must be 1..31 days")
    seed = capture["seed"]
    requested = capture["requested_per_regime"]
    if not isinstance(seed, str) or not seed:
        raise ValueError("Funding source study requires fixed nonempty seed")
    if type(requested) is not int or requested < 1:
        raise ValueError("Funding source study requires positive requested_per_regime")
    pinned = capture["pinned_market_dates"]
    if not isinstance(pinned, list) or pinned != sorted(set(pinned)):
        raise ValueError("pinned dates must be unique, sorted")
    for raw_date in pinned:
        parsed = date.fromisoformat(raw_date)
        if parsed < start or parsed > end:
            raise ValueError("pinned date outside raw study window")

    funding_query = capture["funding_query"]
    spot_query = capture["spot_query"]
    if funding_query != {"instId": FUNDING_INSTRUMENT, "limit": "400"}:
        raise ValueError("unexpected official Funding history query")
    if spot_query != {
        "instId": SPOT_INSTRUMENT, "bar": "1Dutc", "limit": "100"
    }:
        raise ValueError("unexpected official SPOT daily query")

    funding = _funding_index(capture["funding_response"])
    spot = _spot_index(capture["spot_response"])
    raw_source = {
        "funding_endpoint": FUNDING_ENDPOINT,
        "funding_query": funding_query,
        "funding_response": capture["funding_response"],
        "spot_endpoint": SPOT_ENDPOINT,
        "spot_query": spot_query,
        "spot_response": capture["spot_response"],
    }
    source_digest = _digest(raw_source)

    observed: list[dict[str, Any]] = []
    missing: list[str] = []
    diagnostics: list[dict[str, Any]] = []
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        entry = datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(
            minutes=15
        )
        eligible_funding = [
            (moment, item)
            for moment, item in funding.items()
            if timedelta(0) <= entry - moment
            and entry - moment >= FUNDING_MIN_AGE
        ]
        recent = max(eligible_funding, key=lambda pair: pair[0]) if eligible_funding else None
        vol = _volatility_window(spot, entry)
        reasons = []
        if recent is None or entry - recent[0] > FUNDING_MAX_AGE:
            reasons.append("missing_or_stale_prior_settled_funding")
        if vol is None:
            reasons.append("missing_or_unconfirmed_8_daily_spot_candles")
        if reasons:
            missing.append(day.isoformat())
            diagnostics.append({"market_date": day.isoformat(), "reasons": reasons})
            continue
        assert recent is not None and vol is not None
        funding_at, funding_row = recent
        volatility_bps, candles = vol
        final_candle_close_at = entry - timedelta(minutes=15)
        observed_at = max(final_candle_close_at, funding_at)
        record = {"funding": funding_row, "spot_daily_candles": candles}
        observed.append(
            {
                "market_date": day.isoformat(),
                "entry_at": entry.isoformat(),
                "features_observed_at": observed_at.isoformat(),
                "funding_observed_at": funding_at.isoformat(),
                "volatility_window_end_at": final_candle_close_at.isoformat(),
                "lagged_funding_rate": funding_row["realizedRate"],
                "trailing_spot_volatility_bps": str(volatility_bps),
                "source_record_id": (
                    f"okx-settled-funding:{int(funding_at.timestamp() * 1000)}:"
                    f"spot-1Dutc:{candles[0][0]}:{candles[-1][0]}"
                ),
                "source_record_sha256": _digest(record),
            }
        )
    planner_input = {
        "schema_version": 1,
        "evidence_type": "funding_pre_entry_regime_features",
        "policy_version": POLICY_VERSION,
        "seed": seed,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "requested_per_regime": requested,
        "source": {
            "provider": "OKX",
            "instrument_id": FUNDING_INSTRUMENT,
            "artifact_digest": "sha256:" + source_digest,
            "observation_contract": "pre_entry_observed_not_outcome",
        },
        "pinned_market_dates": pinned,
        "missing_market_dates": missing,
        "observations": observed,
    }
    return {
        "schema_version": 1,
        "evidence_type": "retrospective_okx_funding_source_reconstruction",
        "status": "research_only",
        "source_authentication_status": "requires_independent_review",
        "point_in_time_publication_verified": False,
        "acquisition_approved": False,
        "promotion_approved": False,
        "source_capture_timestamp": captured_at.astimezone(UTC).isoformat(),
        "source_sha256": source_digest,
        "funding_rows_received": len(funding),
        "spot_daily_candles_received": len(spot),
        "feature_rows_reconstructed": len(observed),
        "missing_days": diagnostics,
        "planner_input": planner_input,
        "note": (
            "Historical public API response is captured now, not at historical entry. "
            "Event timestamp and raw digest establish reproducibility but do not "
            "prove historical publication time or exchange-signed authenticity. "
            "Use only for outcome-blind research, not acquisition."
        ),
    }
