from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from future_opportunity.backtest.model import HistoricalFundingObservation


_EXPECTED_HEADER = (
    "instrument_name",
    "funding_rate",
    "funding_time",
)


def iter_okx_funding_archive(
    path: Path,
    *,
    expected_instrument_id: str,
) -> Iterator[HistoricalFundingObservation]:
    """Stream a verified OKX module-3 ZIP/CSV archive with strict schema checks."""
    if not path.is_file():
        raise FileNotFoundError(path)
    if not expected_instrument_id:
        raise ValueError("expected_instrument_id is required")
    if not zipfile.is_zipfile(path):
        raise ValueError("OKX funding archive must be a ZIP file")

    with zipfile.ZipFile(path) as archive:
        members = [
            item
            for item in archive.infolist()
            if not item.is_dir() and item.filename.endswith(".csv")
        ]
        if len(members) != 1:
            raise ValueError(
                "OKX funding archive must contain exactly one CSV member"
            )

        source = archive.open(members[0])
        with source, io.TextIOWrapper(source, encoding="utf-8-sig", newline="") as text:
            yield from iter_okx_funding_csv(
                text,
                expected_instrument_id=expected_instrument_id,
            )


def iter_okx_funding_csv(
    lines: Iterator[str] | io.TextIOBase,
    *,
    expected_instrument_id: str,
) -> Iterator[HistoricalFundingObservation]:
    reader = csv.reader(lines)
    try:
        header = tuple(next(reader))
    except StopIteration as error:
        raise ValueError("OKX funding CSV is empty") from error

    if header != _EXPECTED_HEADER:
        raise ValueError(
            "unexpected OKX funding CSV header: "
            + ",".join(header)
        )

    previous_time: datetime | None = None
    for source_line, row in enumerate(reader, start=2):
        if len(row) != 3:
            raise ValueError(
                f"OKX funding row must contain 3 columns at line {source_line}"
            )
        instrument_id, raw_rate, raw_time = row
        if instrument_id != expected_instrument_id:
            raise ValueError(
                "funding instrument mismatch at line "
                f"{source_line}: {instrument_id} != {expected_instrument_id}"
            )

        try:
            rate = Decimal(raw_rate)
        except InvalidOperation as error:
            raise ValueError(
                f"invalid funding_rate at line {source_line}"
            ) from error

        if not raw_time.isdigit():
            raise ValueError(
                f"invalid funding_time at line {source_line}"
            )
        funding_time = datetime.fromtimestamp(
            int(raw_time) / 1000,
            tz=UTC,
        )
        if previous_time is not None and funding_time <= previous_time:
            raise ValueError(
                "funding timestamps must be strictly increasing "
                f"(line {source_line})"
            )
        previous_time = funding_time

        yield HistoricalFundingObservation(
            instrument_id=instrument_id,
            source_line=source_line,
            funding_time=funding_time,
            funding_rate=rate,
        )
