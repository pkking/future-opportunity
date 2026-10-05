from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from future_opportunity.adapters.historical.okx_funding import (
    iter_okx_funding_archive,
    iter_okx_funding_csv,
)


CSV = """instrument_name,funding_rate,funding_time
BTC-USDT-SWAP,0.0000744588100483,1788192000000
BTC-USDT-SWAP,-0.0000135375417752,1788220800000
"""


def test_okx_funding_csv_normalizes_verified_schema() -> None:
    observations = tuple(
        iter_okx_funding_csv(
            io.StringIO(CSV),
            expected_instrument_id="BTC-USDT-SWAP",
        )
    )

    assert len(observations) == 2
    assert observations[0].source_line == 2
    assert observations[0].funding_rate == Decimal("0.0000744588100483")
    assert observations[0].funding_time == datetime.fromtimestamp(
        1788192000,
        tz=UTC,
    )
    assert observations[1].funding_rate < 0


def test_okx_funding_csv_fails_closed_on_header_drift() -> None:
    with pytest.raises(ValueError, match="unexpected OKX funding CSV header"):
        tuple(
            iter_okx_funding_csv(
                io.StringIO(
                    "instrument_name,funding_rate,mark_price,funding_time\n"
                ),
                expected_instrument_id="BTC-USDT-SWAP",
            )
        )


def test_okx_funding_csv_requires_expected_instrument_and_time_order() -> None:
    with pytest.raises(ValueError, match="instrument mismatch"):
        tuple(
            iter_okx_funding_csv(
                io.StringIO(
                    "instrument_name,funding_rate,funding_time\n"
                    "ETH-USDT-SWAP,0.1,1788192000000\n"
                ),
                expected_instrument_id="BTC-USDT-SWAP",
            )
        )

    with pytest.raises(ValueError, match="strictly increasing"):
        tuple(
            iter_okx_funding_csv(
                io.StringIO(
                    "instrument_name,funding_rate,funding_time\n"
                    "BTC-USDT-SWAP,0.1,1788192000000\n"
                    "BTC-USDT-SWAP,0.2,1788192000000\n"
                ),
                expected_instrument_id="BTC-USDT-SWAP",
            )
        )


def test_okx_funding_archive_reads_exactly_one_csv_member(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "funding.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "BTC-USDT-SWAP-fundingrates-2026-09.csv",
            CSV,
        )

    observations = tuple(
        iter_okx_funding_archive(
            archive_path,
            expected_instrument_id="BTC-USDT-SWAP",
        )
    )

    assert len(observations) == 2
