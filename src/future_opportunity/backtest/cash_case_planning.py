from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
import re
from typing import Any

from future_opportunity.backtest.acquisition import (
    HistoricalCashAcquisitionCase,
)


_FUTURE_ID = re.compile(r"^BTC-USDT-(?P<expiry>\d{6})$")
_TIME = re.compile(r"^(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d):(?P<second>[0-5]\d)$")


@dataclass(frozen=True, slots=True)
class CashAcquisitionTemplate:
    future_id: str
    expiry_at: str
    exit_at: str
    entry_time_utc: str

    def __post_init__(self) -> None:
        future = _FUTURE_ID.fullmatch(self.future_id)
        if future is None:
            raise ValueError("Cash template future_id must be BTC-USDT-YYMMDD")

        expiry = _utc_datetime(self.expiry_at, "Cash template expiry_at")
        exit_at = _utc_datetime(self.exit_at, "Cash template exit_at")
        if not exit_at < expiry:
            raise ValueError("Cash template exit_at must be before expiry_at")
        if expiry.hour != 8 or expiry.minute != 0 or expiry.second != 0:
            raise ValueError("Cash template expiry_at must be 08:00:00 UTC")
        suffix_date = datetime.strptime(
            future.group("expiry"),
            "%y%m%d",
        ).date()
        if suffix_date != expiry.date():
            raise ValueError(
                "Cash template future_id expiry date differs from expiry_at"
            )
        _entry_time(self.entry_time_utc)


@dataclass(frozen=True, slots=True)
class CashDiscoveryFact:
    market_date: str
    status: str
    future_id: str | None


@dataclass(frozen=True, slots=True)
class ExcludedCashDiscovery:
    market_date: str
    reason: str
    discovered_future_id: str | None = None


@dataclass(frozen=True, slots=True)
class CashAcquisitionCasePlan:
    selected: tuple[HistoricalCashAcquisitionCase, ...]
    excluded: tuple[ExcludedCashDiscovery, ...]
    template: CashAcquisitionTemplate

    @property
    def selected_count(self) -> int:
        return len(self.selected)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)


def parse_cash_discovery_report(raw: Any) -> CashDiscoveryFact:
    if not isinstance(raw, dict):
        raise TypeError("Cash discovery report must be an object")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported Cash discovery report schema")

    market_date = raw.get("market_date")
    if not isinstance(market_date, str):
        raise ValueError("Cash discovery report requires market_date")
    try:
        canonical_date = date.fromisoformat(market_date).isoformat()
    except ValueError as error:
        raise ValueError(
            "Cash discovery market_date must use YYYY-MM-DD"
        ) from error

    status = raw.get("status")
    if status == "future_discovered":
        future = raw.get("future")
        if not isinstance(future, dict):
            raise ValueError(
                "future_discovered report requires future evidence"
            )
        future_id = future.get("instrument_id")
        if not isinstance(future_id, str) or not future_id:
            raise ValueError(
                "future_discovered report requires future instrument_id"
            )
        if _FUTURE_ID.fullmatch(future_id) is None:
            raise ValueError(
                "discovered Cash future_id must be BTC-USDT-YYMMDD"
            )
        return CashDiscoveryFact(
            market_date=canonical_date,
            status=status,
            future_id=future_id,
        )

    if status == "no_unique_future_chain_archive":
        return CashDiscoveryFact(
            market_date=canonical_date,
            status=status,
            future_id=None,
        )

    raise ValueError(f"unsupported Cash discovery status: {status}")


def plan_cash_acquisition_cases(
    reports: tuple[Any, ...],
    *,
    template: CashAcquisitionTemplate,
    max_cases: int = 31,
) -> CashAcquisitionCasePlan:
    if max_cases <= 0:
        raise ValueError("max_cases must be positive")

    facts = tuple(parse_cash_discovery_report(report) for report in reports)
    seen_dates: set[str] = set()
    for fact in facts:
        if fact.market_date in seen_dates:
            raise ValueError(
                f"duplicate Cash discovery market date: {fact.market_date}"
            )
        seen_dates.add(fact.market_date)

    expiry = _utc_datetime(template.expiry_at, "Cash template expiry_at")
    exit_at = _utc_datetime(template.exit_at, "Cash template exit_at")
    entry_clock = _entry_time(template.entry_time_utc)

    selected: list[HistoricalCashAcquisitionCase] = []
    excluded: list[ExcludedCashDiscovery] = []
    for fact in sorted(facts, key=lambda item: item.market_date):
        if fact.status != "future_discovered":
            excluded.append(
                ExcludedCashDiscovery(
                    market_date=fact.market_date,
                    reason=fact.status,
                )
            )
            continue

        if fact.future_id != template.future_id:
            excluded.append(
                ExcludedCashDiscovery(
                    market_date=fact.market_date,
                    reason="future_id_mismatch",
                    discovered_future_id=fact.future_id,
                )
            )
            continue

        market_day = date.fromisoformat(fact.market_date)
        entry_at = datetime.combine(
            market_day,
            entry_clock,
            tzinfo=UTC,
        )
        if not entry_at < exit_at:
            excluded.append(
                ExcludedCashDiscovery(
                    market_date=fact.market_date,
                    reason="entry_not_before_explicit_exit",
                    discovered_future_id=fact.future_id,
                )
            )
            continue
        if not entry_at < expiry:
            excluded.append(
                ExcludedCashDiscovery(
                    market_date=fact.market_date,
                    reason="entry_not_before_expiry",
                    discovered_future_id=fact.future_id,
                )
            )
            continue

        selected.append(
            HistoricalCashAcquisitionCase(
                entry_at=entry_at.isoformat(),
                exit_at=exit_at.isoformat(),
                future_id=template.future_id,
                expiry_at=expiry.isoformat(),
                entry_market_date=fact.market_date,
            )
        )

    if len(selected) > max_cases:
        raise ValueError(
            f"Cash case plan selected {len(selected)} cases; "
            f"maximum is {max_cases}"
        )

    return CashAcquisitionCasePlan(
        selected=tuple(selected),
        excluded=tuple(excluded),
        template=template,
    )


def _utc_datetime(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{name} must use ISO-8601") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{name} must use UTC")
    return parsed.astimezone(UTC)


def _entry_time(value: str) -> time:
    match = _TIME.fullmatch(value)
    if match is None:
        raise ValueError("Cash template entry_time_utc must use HH:MM:SS")
    return time(
        hour=int(match.group("hour")),
        minute=int(match.group("minute")),
        second=int(match.group("second")),
    )
