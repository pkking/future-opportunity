import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from future_opportunity.backtest.evidence import write_backtest_evidence


@dataclass(frozen=True)
class Example:
    value: Decimal
    items: tuple[str, ...]


def test_backtest_evidence_serializes_decimal_and_dataclass(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "evidence.json"

    write_backtest_evidence(
        {
            "report": Example(
                value=Decimal("0.0123"),
                items=("a", "b"),
            )
        },
        destination,
    )

    payload = json.loads(destination.read_text())
    assert payload == {
        "report": {
            "items": ["a", "b"],
            "value": "0.0123",
        }
    }
