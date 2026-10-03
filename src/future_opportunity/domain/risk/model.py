from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class InvariantState(StrEnum):
    SATISFIED = "satisfied"
    WARNING = "warning"
    VIOLATED = "violated"


@dataclass(frozen=True, slots=True)
class InvariantResult:
    name: str
    state: InvariantState
    observed: dict[str, Any]
    limit: dict[str, Any]
    explanation: dict[str, Any] | None = None
