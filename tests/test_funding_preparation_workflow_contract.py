from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/prepare-historical-fixture.yml"
CORPUS_WORKFLOW = ROOT / ".github/workflows/prepare-funding-corpus.yml"
CASH_WORKFLOW = ROOT / ".github/workflows/prepare-cash-historical-fixture.yml"
SCRIPT = ROOT / "scripts/prepare_okx_funding_history_fixture.py"


def test_funding_preparation_accepts_optional_selection_provenance_read_only() -> None:
    text = WORKFLOW.read_text()

    assert "selection_provenance_json:" in text
    assert "HISTORICAL_SELECTION_PROVENANCE_JSON" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text


def test_funding_raw_archive_cap_tracks_measured_current_okx_sizes() -> None:
    workflow = WORKFLOW.read_text()
    corpus = CORPUS_WORKFLOW.read_text()
    script = SCRIPT.read_text()
    cash = CASH_WORKFLOW.read_text()

    assert 'HISTORY_MAX_RAW_MB: "1024"' in workflow
    assert 'HISTORY_MAX_RAW_MB: "1024"' in corpus
    assert 'os.getenv("HISTORY_MAX_RAW_MB", "1024")' in script
    assert "raw archive exceeded {MAX_RAW_MB} MiB limit" in script

    # Generic Cash retains the original 600 MiB default; only the
    # separately reviewed Q2 manual wave opts into 1024 MiB. The input
    # remains explicitly bounded: never silently remove the cap.
    assert "max_raw_mb:" in cash
    assert "default: 600" in cash
    assert "CASH_HISTORY_MAX_RAW_MB: ${{ inputs.max_raw_mb || 600 }}" in cash
    assert "600|1024)" in cash
    q2_wave = (ROOT / ".github/workflows/prepare-cash-2025q2-wave.yml").read_text()
    assert "cash_max_raw_mb: 1024" in q2_wave
    assert "push:" not in cash
