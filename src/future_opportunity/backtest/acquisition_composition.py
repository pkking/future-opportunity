from __future__ import annotations

from datetime import datetime
from typing import Any

from future_opportunity.backtest.acquisition import (
    HistoricalAcquisitionManifest,
    parse_historical_acquisition_manifest,
)


_CASE_PLAN_KEYS = {
    "schema_version",
    "evidence_type",
    "template",
    "selected_count",
    "excluded_count",
    "cash_cases",
    "excluded",
    "source_reports",
    "note",
}
_TEMPLATE_KEYS = {
    "future_id",
    "expiry_at",
    "exit_at",
    "entry_time_utc",
}
_CASE_KEYS = {
    "entry_at",
    "entry_market_date",
    "exit_at",
    "expiry_at",
    "future_id",
}


def compose_historical_acquisition(
    *,
    acquisition_id: str,
    planner_campaign_prefix: str,
    funding_start_date: str | None = None,
    funding_end_date: str | None = None,
    cash_case_plan: Any | None = None,
    max_total_items: int = 31,
) -> HistoricalAcquisitionManifest:
    funding = _funding_payload(
        funding_start_date,
        funding_end_date,
    )
    cash_cases = (
        acquisition_cash_cases_from_plan(cash_case_plan)
        if cash_case_plan is not None
        else []
    )

    return parse_historical_acquisition_manifest(
        {
            "schema_version": 1,
            "acquisition_id": acquisition_id,
            "planner_campaign_prefix": planner_campaign_prefix,
            "funding": funding,
            "cash_cases": cash_cases,
        },
        max_total_items=max_total_items,
    )


def acquisition_cash_cases_from_plan(
    raw: Any,
) -> list[dict[str, str]]:
    if not isinstance(raw, dict):
        raise TypeError("Cash case-plan report must be an object")
    if set(raw) != _CASE_PLAN_KEYS:
        raise ValueError("Cash case-plan report fields differ from schema")
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported Cash case-plan report schema")
    if raw.get("evidence_type") != "read_only_cash_acquisition_case_plan":
        raise ValueError("unexpected Cash case-plan evidence_type")

    template = raw.get("template")
    if not isinstance(template, dict) or set(template) != _TEMPLATE_KEYS:
        raise ValueError("Cash case-plan template fields differ from schema")
    template_values = {
        key: _required_string(template, key, "Cash case-plan template")
        for key in _TEMPLATE_KEYS
    }

    cash_cases = raw.get("cash_cases")
    excluded = raw.get("excluded")
    source_reports = raw.get("source_reports")
    note = raw.get("note")
    selected_count = raw.get("selected_count")
    excluded_count = raw.get("excluded_count")

    if not isinstance(cash_cases, list):
        raise TypeError("Cash case-plan cash_cases must be an array")
    if not isinstance(excluded, list):
        raise TypeError("Cash case-plan excluded must be an array")
    if not isinstance(source_reports, list) or not all(
        isinstance(item, str) and item
        for item in source_reports
    ):
        raise ValueError("Cash case-plan source_reports must be non-empty strings")
    if not isinstance(note, str) or not note:
        raise ValueError("Cash case-plan note is required")
    if type(selected_count) is not int or selected_count != len(cash_cases):
        raise ValueError("Cash case-plan selected_count does not match cash_cases")
    if type(excluded_count) is not int or excluded_count != len(excluded):
        raise ValueError("Cash case-plan excluded_count does not match excluded")

    result: list[dict[str, str]] = []
    seen_market_dates: set[str] = set()
    for position, case in enumerate(cash_cases):
        if not isinstance(case, dict) or set(case) != _CASE_KEYS:
            raise ValueError(
                f"Cash case-plan case {position} fields differ from schema"
            )
        values = {
            key: _required_string(
                case,
                key,
                f"Cash case-plan case {position}",
            )
            for key in _CASE_KEYS
        }
        if values["future_id"] != template_values["future_id"]:
            raise ValueError(
                f"Cash case-plan case {position} future_id differs from template"
            )
        if values["expiry_at"] != template_values["expiry_at"]:
            raise ValueError(
                f"Cash case-plan case {position} expiry_at differs from template"
            )
        if values["exit_at"] != template_values["exit_at"]:
            raise ValueError(
                f"Cash case-plan case {position} exit_at differs from template"
            )

        try:
            entry = datetime.fromisoformat(values["entry_at"])
        except ValueError as error:
            raise ValueError(
                f"Cash case-plan case {position} entry_at must use ISO-8601"
            ) from error
        if entry.tzinfo is None:
            raise ValueError(
                f"Cash case-plan case {position} entry_at must be timezone-aware"
            )
        market_date = entry.date().isoformat()
        if market_date != values["entry_market_date"]:
            raise ValueError(
                f"Cash case-plan case {position} entry_market_date drifted"
            )
        if entry.strftime("%H:%M:%S") != template_values["entry_time_utc"]:
            raise ValueError(
                f"Cash case-plan case {position} entry time differs from template"
            )
        if market_date in seen_market_dates:
            raise ValueError(
                f"duplicate Cash case-plan entry market date: {market_date}"
            )
        seen_market_dates.add(market_date)

        result.append(
            {
                "entry_at": values["entry_at"],
                "exit_at": values["exit_at"],
                "future_id": values["future_id"],
                "expiry_at": values["expiry_at"],
            }
        )

    return result


def _funding_payload(
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str] | None:
    if start_date is None and end_date is None:
        return None
    if start_date is None or end_date is None:
        raise ValueError(
            "Funding start_date and end_date must be supplied together"
        )
    return {
        "start_date": start_date,
        "end_date": end_date,
    }


def _required_string(
    raw: dict[str, Any],
    key: str,
    context: str,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} requires {key}")
    return value
