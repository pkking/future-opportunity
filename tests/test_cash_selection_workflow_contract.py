from pathlib import Path


ROOT = Path(__file__).parents[1]
SAMPLED_DISCOVERY = ROOT / ".github/workflows/discover-sampled-cash-corpus.yml"
CASE_PLANNER = ROOT / ".github/workflows/plan-cash-acquisition-cases.yml"
PREPARE = ROOT / ".github/workflows/prepare-cash-historical-fixture.yml"


def test_sampled_cash_discovery_is_read_only_and_exact_artifact_driven() -> None:
    text = SAMPLED_DISCOVERY.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "sampling_run_id:" in text
    assert "sampling_artifact_name:" in text
    assert "build_historical_selection_provenance.py" in text
    assert "sampling.selected_market_dates" in text
    assert "fromJSON(needs.resolve.outputs.selected_dates)" in text
    assert "discover_okx_cash_history.py" in text
    assert "git push" not in text
    assert "gh pr create" not in text


def test_cash_case_planner_consumes_optional_sampled_discovery_control() -> None:
    text = CASE_PLANNER.read_text()

    assert "cash-sampled-discovery-control" in text
    assert "selection_path=" in text
    assert "--selection-provenance" in text
    assert "37488688098" in text
    assert "contents: write" not in text
    assert "git push" not in text


def test_cash_preparation_accepts_optional_selection_provenance_read_only() -> None:
    text = PREPARE.read_text()

    assert "selection_provenance_json:" in text
    assert "CASH_SELECTION_PROVENANCE_JSON" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
