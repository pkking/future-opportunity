from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from future_opportunity.backtest.date_range import historical_date_range
from future_opportunity.backtest.selection_provenance import (
    HistoricalSelectionProvenance,
    historical_selection_provenance_payload,
    parse_historical_selection_provenance,
)


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_FUTURE_ID = re.compile(r"^BTC-USDT-(?P<expiry>\d{6})$")


@dataclass(frozen=True, slots=True)
class HistoricalFundingAcquisition:
    source_kind: str
    start_date: str | None
    end_date: str | None
    market_dates: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.source_kind not in {"range", "explicit_dates"}:
            raise ValueError(
                f"unsupported historical Funding source_kind: {self.source_kind}"
            )
        if not self.market_dates:
            raise ValueError(
                "historical Funding acquisition requires market_dates"
            )
        if self.source_kind == "range":
            if self.start_date is None or self.end_date is None:
                raise ValueError(
                    "range Funding acquisition requires start_date/end_date"
                )
        elif self.start_date is not None or self.end_date is not None:
            raise ValueError(
                "explicit Funding acquisition must not carry range boundaries"
            )


@dataclass(frozen=True, slots=True)
class HistoricalCashAcquisitionCase:
    entry_at: str
    exit_at: str
    future_id: str
    expiry_at: str
    entry_market_date: str


@dataclass(frozen=True, slots=True)
class HistoricalAcquisitionManifest:
    schema_version: int
    acquisition_id: str
    planner_campaign_prefix: str
    funding: HistoricalFundingAcquisition | None
    cash_cases: tuple[HistoricalCashAcquisitionCase, ...]
    funding_selection_provenance: HistoricalSelectionProvenance | None = None
    cash_selection_provenance: HistoricalSelectionProvenance | None = None

    @property
    def total_items(self) -> int:
        return (
            (len(self.funding.market_dates) if self.funding is not None else 0)
            + len(self.cash_cases)
        )


def load_historical_acquisition_manifest(
    path: Path,
    *,
    max_funding_days: int = 31,
    max_cash_cases: int = 31,
    max_total_items: int = 31,
) -> HistoricalAcquisitionManifest:
    raw = json.loads(path.read_text())
    return parse_historical_acquisition_manifest(
        raw,
        max_funding_days=max_funding_days,
        max_cash_cases=max_cash_cases,
        max_total_items=max_total_items,
    )


def parse_historical_acquisition_manifest(
    raw: Any,
    *,
    max_funding_days: int = 31,
    max_cash_cases: int = 31,
    max_total_items: int = 31,
) -> HistoricalAcquisitionManifest:
    if not isinstance(raw, dict):
        raise TypeError("historical acquisition manifest must be an object")
    expected = {
        "schema_version",
        "acquisition_id",
        "planner_campaign_prefix",
        "funding",
        "cash_cases",
    }
    allowed = (
        expected,
        expected | {"selection_provenance"},
    )
    if set(raw) not in allowed:
        raise ValueError("historical acquisition manifest fields differ from schema")

    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ValueError("unsupported historical acquisition schema")

    acquisition_id = _safe_id(raw.get("acquisition_id"), "acquisition_id")
    planner_prefix = _safe_id(
        raw.get("planner_campaign_prefix"),
        "planner_campaign_prefix",
    )

    if max_funding_days <= 0:
        raise ValueError("max_funding_days must be positive")
    if max_cash_cases <= 0:
        raise ValueError("max_cash_cases must be positive")
    if max_total_items <= 0:
        raise ValueError("max_total_items must be positive")

    funding = _parse_funding(
        raw.get("funding"),
        max_days=max_funding_days,
    )
    cash_cases = _parse_cash_cases(
        raw.get("cash_cases"),
        max_cases=max_cash_cases,
    )

    total = (
        (len(funding.market_dates) if funding is not None else 0)
        + len(cash_cases)
    )
    if total == 0:
        raise ValueError(
            "historical acquisition requires at least one Funding day or Cash case"
        )
    if total > max_total_items:
        raise ValueError(
            f"historical acquisition contains {total} items; "
            f"maximum is {max_total_items}"
        )

    funding_selection, cash_selection = _parse_selection_provenance(
        raw.get("selection_provenance"),
        funding=funding,
        cash_cases=cash_cases,
    )

    return HistoricalAcquisitionManifest(
        schema_version=1,
        acquisition_id=acquisition_id,
        planner_campaign_prefix=planner_prefix,
        funding=funding,
        cash_cases=cash_cases,
        funding_selection_provenance=funding_selection,
        cash_selection_provenance=cash_selection,
    )


def acquisition_dispatch_payload(
    manifest: HistoricalAcquisitionManifest,
) -> dict[str, Any]:
    """Serialize the exact workflow-dispatch acquisition input schema."""
    return {
        "schema_version": manifest.schema_version,
        "acquisition_id": manifest.acquisition_id,
        "planner_campaign_prefix": manifest.planner_campaign_prefix,
        "funding": (
            _funding_dispatch_payload(manifest.funding)
            if manifest.funding is not None
            else None
        ),
        "cash_cases": [
            {
                "entry_at": case.entry_at,
                "exit_at": case.exit_at,
                "future_id": case.future_id,
                "expiry_at": case.expiry_at,
            }
            for case in manifest.cash_cases
        ],
        **_selection_dispatch_payload(manifest),
    }


def acquisition_manifest_payload(
    manifest: HistoricalAcquisitionManifest,
) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "acquisition_id": manifest.acquisition_id,
        "planner_campaign_prefix": manifest.planner_campaign_prefix,
        "funding": (
            {
                "source_kind": manifest.funding.source_kind,
                "start_date": manifest.funding.start_date,
                "end_date": manifest.funding.end_date,
                "market_dates": list(manifest.funding.market_dates),
            }
            if manifest.funding is not None
            else None
        ),
        "cash_cases": [
            {
                "entry_at": case.entry_at,
                "exit_at": case.exit_at,
                "future_id": case.future_id,
                "expiry_at": case.expiry_at,
                "entry_market_date": case.entry_market_date,
            }
            for case in manifest.cash_cases
        ],
        "selection_provenance": {
            "funding": (
                historical_selection_provenance_payload(
                    manifest.funding_selection_provenance
                )
                if manifest.funding_selection_provenance is not None
                else None
            ),
            "cash": (
                historical_selection_provenance_payload(
                    manifest.cash_selection_provenance
                )
                if manifest.cash_selection_provenance is not None
                else None
            ),
        },
        "total_items": manifest.total_items,
    }


def workflow_funding_dates_json(
    manifest: HistoricalAcquisitionManifest,
) -> str:
    return json.dumps(
        list(manifest.funding.market_dates) if manifest.funding else [],
        separators=(",", ":"),
    )


def workflow_cash_cases_json(
    manifest: HistoricalAcquisitionManifest,
) -> str:
    return json.dumps(
        [
            {
                "entry_at": case.entry_at,
                "exit_at": case.exit_at,
                "future_id": case.future_id,
                "expiry_at": case.expiry_at,
            }
            for case in manifest.cash_cases
        ],
        separators=(",", ":"),
    )


def _parse_selection_provenance(
    raw: Any,
    *,
    funding: HistoricalFundingAcquisition | None,
    cash_cases: tuple[HistoricalCashAcquisitionCase, ...],
) -> tuple[
    HistoricalSelectionProvenance | None,
    HistoricalSelectionProvenance | None,
]:
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        raise TypeError(
            "historical acquisition selection_provenance must be object"
        )
    if set(raw) != {"funding", "cash"}:
        raise ValueError(
            "historical acquisition selection_provenance fields differ "
            "from schema"
        )

    funding_raw = raw.get("funding")
    cash_raw = raw.get("cash")
    funding_selection = (
        parse_historical_selection_provenance(funding_raw)
        if funding_raw is not None
        else None
    )
    cash_selection = (
        parse_historical_selection_provenance(cash_raw)
        if cash_raw is not None
        else None
    )

    if funding_selection is not None:
        if funding_selection.strategy != "funding-carry":
            raise ValueError(
                "Funding selection provenance strategy must be funding-carry"
            )
        if funding is None:
            raise ValueError(
                "Funding selection provenance requires Funding acquisition"
            )
        if funding_selection.selected_market_dates != funding.market_dates:
            raise ValueError(
                "Funding acquisition dates differ from selection provenance"
            )

    if cash_selection is not None:
        if cash_selection.strategy != "cash-and-carry":
            raise ValueError(
                "Cash selection provenance strategy must be cash-and-carry"
            )
        for case in cash_cases:
            if not cash_selection.contains_market_date(
                case.entry_market_date
            ):
                raise ValueError(
                    "Cash acquisition case date is outside selection provenance"
                )

    return funding_selection, cash_selection


def _selection_dispatch_payload(
    manifest: HistoricalAcquisitionManifest,
) -> dict[str, Any]:
    if (
        manifest.funding_selection_provenance is None
        and manifest.cash_selection_provenance is None
    ):
        return {}
    return {
        "selection_provenance": {
            "funding": (
                historical_selection_provenance_payload(
                    manifest.funding_selection_provenance
                )
                if manifest.funding_selection_provenance is not None
                else None
            ),
            "cash": (
                historical_selection_provenance_payload(
                    manifest.cash_selection_provenance
                )
                if manifest.cash_selection_provenance is not None
                else None
            ),
        }
    }


def _parse_funding(
    raw: Any,
    *,
    max_days: int,
) -> HistoricalFundingAcquisition | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeError("historical acquisition funding must be object or null")

    fields = set(raw)
    if fields == {"start_date", "end_date"}:
        start = raw.get("start_date")
        end = raw.get("end_date")
        if not isinstance(start, str) or not isinstance(end, str):
            raise TypeError("Funding start_date/end_date must be strings")
        dates = historical_date_range(start, end, max_days=max_days)
        return HistoricalFundingAcquisition(
            source_kind="range",
            start_date=dates[0],
            end_date=dates[-1],
            market_dates=dates,
        )

    if fields == {"market_dates"}:
        values = raw.get("market_dates")
        if not isinstance(values, list):
            raise TypeError("Funding market_dates must be an array")
        if not values:
            raise ValueError("Funding market_dates must not be empty")
        if len(values) > max_days:
            raise ValueError(
                f"historical acquisition contains {len(values)} Funding days; "
                f"maximum is {max_days}"
            )

        dates: list[str] = []
        previous: date | None = None
        seen: set[str] = set()
        for position, value in enumerate(values):
            if not isinstance(value, str):
                raise TypeError(
                    f"Funding market_dates[{position}] must be a string"
                )
            try:
                parsed = date.fromisoformat(value)
            except ValueError as error:
                raise ValueError(
                    f"Funding market_dates[{position}] must use YYYY-MM-DD"
                ) from error
            canonical = parsed.isoformat()
            if canonical in seen:
                raise ValueError(
                    f"duplicate Funding market date: {canonical}"
                )
            if previous is not None and parsed <= previous:
                raise ValueError(
                    "Funding market_dates must be strictly chronological"
                )
            seen.add(canonical)
            previous = parsed
            dates.append(canonical)

        return HistoricalFundingAcquisition(
            source_kind="explicit_dates",
            start_date=None,
            end_date=None,
            market_dates=tuple(dates),
        )

    raise ValueError("historical acquisition funding fields differ from schema")


def _funding_dispatch_payload(
    funding: HistoricalFundingAcquisition,
) -> dict[str, Any]:
    if funding.source_kind == "range":
        if funding.start_date is None or funding.end_date is None:
            raise RuntimeError("range Funding acquisition lost boundaries")
        return {
            "start_date": funding.start_date,
            "end_date": funding.end_date,
        }
    if funding.source_kind == "explicit_dates":
        return {
            "market_dates": list(funding.market_dates),
        }
    raise RuntimeError(
        f"unsupported Funding acquisition source_kind: {funding.source_kind}"
    )


def _parse_cash_cases(
    raw: Any,
    *,
    max_cases: int,
) -> tuple[HistoricalCashAcquisitionCase, ...]:
    if not isinstance(raw, list):
        raise TypeError("historical acquisition cash_cases must be an array")
    if len(raw) > max_cases:
        raise ValueError(
            f"historical acquisition contains {len(raw)} Cash cases; "
            f"maximum is {max_cases}"
        )

    result: list[HistoricalCashAcquisitionCase] = []
    seen_dates: set[str] = set()
    seen_cases: set[tuple[str, str, str, str]] = set()
    for position, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TypeError(f"Cash case {position} must be an object")
        expected = {"entry_at", "exit_at", "future_id", "expiry_at"}
        if set(item) != expected:
            raise ValueError(
                f"Cash case {position} fields differ from acquisition schema"
            )

        values: dict[str, str] = {}
        for key in expected:
            value = item.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"Cash case {position} requires {key}")
            values[key] = value

        entry = _utc_datetime(values["entry_at"], f"Cash case {position} entry_at")
        exit_at = _utc_datetime(values["exit_at"], f"Cash case {position} exit_at")
        expiry = _utc_datetime(values["expiry_at"], f"Cash case {position} expiry_at")
        if not entry < exit_at < expiry:
            raise ValueError(
                f"Cash case {position} must satisfy entry_at < exit_at < expiry_at"
            )

        match = _FUTURE_ID.fullmatch(values["future_id"])
        if match is None:
            raise ValueError(
                f"Cash case {position} future_id must be BTC-USDT-YYMMDD"
            )
        future_expiry = datetime.strptime(match.group("expiry"), "%y%m%d").date()
        if future_expiry != expiry.date():
            raise ValueError(
                f"Cash case {position} future_id expiry date differs from expiry_at"
            )
        if expiry.hour != 8 or expiry.minute != 0 or expiry.second != 0:
            raise ValueError(
                f"Cash case {position} expiry_at must be 08:00:00 UTC"
            )

        market_date = entry.date().isoformat()
        if market_date in seen_dates:
            raise ValueError(
                f"duplicate Cash entry market date: {market_date}"
            )
        identity = (
            values["entry_at"],
            values["exit_at"],
            values["future_id"],
            values["expiry_at"],
        )
        if identity in seen_cases:
            raise ValueError(f"duplicate Cash case at position {position}")
        seen_dates.add(market_date)
        seen_cases.add(identity)
        result.append(
            HistoricalCashAcquisitionCase(
                entry_at=entry.isoformat(),
                exit_at=exit_at.isoformat(),
                future_id=values["future_id"],
                expiry_at=expiry.isoformat(),
                entry_market_date=market_date,
            )
        )

    result.sort(key=lambda case: (case.entry_market_date, case.future_id))
    return tuple(result)


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


def _safe_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ValueError(f"historical acquisition {name} must be a safe identifier")
    return value
