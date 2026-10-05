from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx

from future_opportunity.backtest.model import HistoricalArchiveFile


OKX_HISTORY_ENDPOINT = "/api/v5/public/market-data-history"
UTC_PLUS_8 = timezone(timedelta(hours=8))


@dataclass(frozen=True, slots=True)
class OkxHistoricalCatalogQuery:
    module: str
    instrument_type: str
    date_aggregation: str
    begin_ms: int
    end_ms: int
    instrument_ids: tuple[str, ...] = ()
    instrument_families: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.module not in {"1", "2", "3", "4", "5", "6", "11"}:
            raise ValueError(f"unsupported OKX history module: {self.module}")
        if self.instrument_type not in {"SPOT", "FUTURES", "SWAP", "OPTION"}:
            raise ValueError(
                f"unsupported OKX instrument type: {self.instrument_type}"
            )
        if self.date_aggregation not in {"daily", "monthly"}:
            raise ValueError(
                f"unsupported OKX date aggregation: {self.date_aggregation}"
            )
        if self.end_ms < self.begin_ms:
            raise ValueError("end_ms must not be before begin_ms")

        if self.instrument_type == "SPOT":
            if not self.instrument_ids:
                raise ValueError("SPOT history requires instrument_ids")
            if self.instrument_families:
                raise ValueError(
                    "SPOT history must not use instrument_families"
                )
        else:
            if not self.instrument_families:
                raise ValueError(
                    "derivative history requires instrument_families"
                )
            if self.instrument_ids:
                raise ValueError(
                    "derivative history must not use instrument_ids"
                )

        selection = (
            self.instrument_ids
            if self.instrument_type == "SPOT"
            else self.instrument_families
        )
        if len(selection) > 10:
            raise ValueError("OKX historical catalog supports at most 10 selectors")

        if self.module == "6" and self.date_aggregation == "monthly":
            raise ValueError("OKX module 6 does not support monthly aggregation")
        if (
            self.module == "3"
            and self.date_aggregation == "daily"
            and self.instrument_type != "SPOT"
            and self.instrument_families != ("ANY",)
        ):
            raise ValueError(
                "OKX funding history for a specific derivative family "
                "requires monthly aggregation"
            )

    def params(self) -> dict[str, str]:
        result = {
            "module": self.module,
            "instType": self.instrument_type,
            "dateAggrType": self.date_aggregation,
            "begin": str(self.begin_ms),
            "end": str(self.end_ms),
        }
        if self.instrument_type == "SPOT":
            result["instIdList"] = ",".join(self.instrument_ids)
        else:
            result["instFamilyList"] = ",".join(self.instrument_families)
        return result

    @property
    def source_timezone(self) -> str:
        return "UTC" if self.module in {"4", "5", "6"} else "UTC+08:00"


class OkxHistoricalCatalogClient:
    def __init__(
        self,
        base_url: str = "https://www.okx.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def files(
        self,
        query: OkxHistoricalCatalogQuery,
    ) -> tuple[HistoricalArchiveFile, ...]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}{OKX_HISTORY_ENDPOINT}",
                params=query.params(),
            )
            response.raise_for_status()
            payload = response.json()
        return parse_okx_history_catalog(payload, query)


def parse_okx_history_catalog(
    payload: dict[str, Any],
    query: OkxHistoricalCatalogQuery,
) -> tuple[HistoricalArchiveFile, ...]:
    if payload.get("code") != "0":
        raise ValueError(
            f"OKX historical catalog error: "
            f"{payload.get('code')} {payload.get('msg')}"
        )

    data = payload.get("data")
    if not isinstance(data, list):
        raise TypeError("unexpected OKX historical catalog response")

    files: list[HistoricalArchiveFile] = []
    for group in data:
        if not isinstance(group, dict):
            raise TypeError("unexpected OKX historical catalog group")
        aggregation = group.get("dateAggrType")
        if aggregation != query.date_aggregation:
            raise ValueError(
                "catalog aggregation differs from requested aggregation"
            )
        details = group.get("details", [])
        if not isinstance(details, list):
            raise TypeError("unexpected OKX historical catalog details")

        for detail in details:
            if not isinstance(detail, dict):
                raise TypeError("unexpected OKX historical catalog detail")
            instrument_type = str(detail.get("instType", ""))
            if instrument_type != query.instrument_type:
                raise ValueError(
                    "catalog instrument type differs from requested type"
                )

            raw_files = detail.get("groupDetails", [])
            if not isinstance(raw_files, list):
                raise TypeError(
                    "unexpected OKX historical catalog file details"
                )

            for raw in raw_files:
                if not isinstance(raw, dict):
                    raise TypeError(
                        "unexpected OKX historical catalog file entry"
                    )
                timestamp = raw.get("dataTs", raw.get("dateTs"))
                if timestamp in (None, ""):
                    raise ValueError(
                        "historical file is missing dataTs/dateTs"
                    )
                filename = str(raw.get("filename", ""))
                url = str(raw.get("url", ""))
                if not filename or not url:
                    raise ValueError(
                        "historical file is missing filename or url"
                    )

                files.append(
                    HistoricalArchiveFile(
                        module=query.module,
                        instrument_type=instrument_type,
                        instrument_id=str(detail.get("instId", "")),
                        instrument_family=str(
                            detail.get("instFamily", "")
                        ),
                        date_aggregation=str(aggregation),
                        date_range_start=_catalog_datetime(
                            detail.get("dateRangeStart"),
                            query,
                        ),
                        date_range_end=_catalog_datetime(
                            detail.get("dateRangeEnd"),
                            query,
                        ),
                        data_date=_catalog_datetime(timestamp, query),
                        source_timezone=query.source_timezone,
                        filename=filename,
                        url=url,
                        declared_size_mb=_optional_decimal(
                            raw.get("sizeMB")
                        ),
                    )
                )

    return tuple(
        sorted(
            files,
            key=lambda item: (
                item.instrument_id,
                item.instrument_family,
                item.data_date,
                item.filename,
            ),
        )
    )


def _catalog_datetime(
    value: object,
    query: OkxHistoricalCatalogQuery,
) -> datetime:
    if value in (None, ""):
        raise ValueError("historical catalog timestamp is missing")
    milliseconds = int(str(value))
    source_tz = UTC if query.source_timezone == "UTC" else UTC_PLUS_8
    return datetime.fromtimestamp(milliseconds / 1000, tz=source_tz)


def _optional_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))
