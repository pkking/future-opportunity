from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import pytest


_EVIDENCE: list[dict[str, object]] = []


@pytest.fixture
def evidence_recorder() -> Callable[[dict[str, object]], None]:
    def record(item: dict[str, object]) -> None:
        _EVIDENCE.append(item)

    return record


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    destination = os.getenv("E2E_EVIDENCE_PATH")
    if not destination:
        return

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "git_sha": os.getenv("GITHUB_SHA"),
                "pytest_exitstatus": exitstatus,
                "scenarios": _EVIDENCE,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
