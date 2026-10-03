from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InstrumentType(StrEnum):
    SPOT = "spot"
    PERPETUAL = "perpetual"
    FUTURE = "future"


@dataclass(frozen=True, slots=True)
class InstrumentRef:
    venue: str
    base: str
    quote: str
    type: InstrumentType
    settlement: str | None = None
    expiry: str | None = None
