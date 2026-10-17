from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).parents[1]
CAMPAIGN = ROOT / ".github/workflows/acquire-historical-campaign.yml"
FIXTURE = ROOT / ".github/workflows/prepare-cash-historical-fixture.yml"
Q2_WAVE = ROOT / ".github/workflows/prepare-cash-2025q2-wave.yml"


def test_q2_bound_propagates_through_only_its_manual_wave():
    campaign = CAMPAIGN.read_text()
    fixture = FIXTURE.read_text()
    q2 = Q2_WAVE.read_text()

    assert "cash_max_raw_mb:" in campaign
    assert "default: 600" in campaign
    assert "max_raw_mb: ${{ inputs.cash_max_raw_mb || 600 }}" in campaign
    assert "max_raw_mb:" in fixture
    assert "default: 600" in fixture
    assert "CASH_HISTORY_MAX_RAW_MB: ${{ inputs.max_raw_mb || 600 }}" in fixture
    assert "600|1024)" in fixture
    assert "unsupported Cash raw archive budget" in fixture
    assert "cash_max_raw_mb: 1024" in q2
    assert "push:" not in campaign
    assert "push:" not in fixture
    assert "workflow_dispatch:" in q2
    assert "APPROVE-CASH-2025Q2-N12-SOURCE-PREPARATION" in q2
    assert "push:" not in q2
    assert "schedule:" not in q2


def test_large_archives_remain_bounded_before_any_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    spec = importlib.util.spec_from_file_location(
        "bounded_q2_cash_source",
        ROOT / "scripts/prepare_okx_cash_and_carry_fixture.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MAX_RAW_MB", 1)
    body = b"x" * (1024 * 1024 + 1)
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=body, request=request),
    ))
    try:
        with pytest.raises(RuntimeError, match="raw archive exceeded 1 MiB"):
            module.download(client, "https://static.okx.com/test.tar.gz", tmp_path / "oversize")
    finally:
        client.close()


def test_small_archives_retain_original_source_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    spec = importlib.util.spec_from_file_location(
        "bounded_cash_fixture",
        ROOT / "scripts/prepare_okx_cash_and_carry_fixture.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "MAX_RAW_MB", 1)
    source = b"immutable official-source bytes"
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=source, request=request),
    ))
    try:
        path = tmp_path / "source.tar.gz"
        digest, size = module.download(
            client, "https://static.okx.com/test.tar.gz", path,
        )
    finally:
        client.close()
    assert path.read_bytes() == source
    assert size == len(source)
    assert digest == hashlib.sha256(source).hexdigest()
