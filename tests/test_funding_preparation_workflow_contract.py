from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/prepare-historical-fixture.yml"


def test_funding_preparation_accepts_optional_selection_provenance_read_only() -> None:
    text = WORKFLOW.read_text()

    assert "selection_provenance_json:" in text
    assert "HISTORICAL_SELECTION_PROVENANCE_JSON" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
