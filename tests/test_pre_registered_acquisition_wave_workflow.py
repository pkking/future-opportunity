from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPOSER = ROOT / ".github/workflows/compose-historical-acquisition.yml"
ACQUIRE = ROOT / ".github/workflows/acquire-historical-campaign.yml"
WAVE = ROOT / ".github/workflows/acquire-pre-registered-historical-wave.yml"


def test_composer_exposes_reusable_canonical_acquisition_output() -> None:
    text = COMPOSER.read_text()

    assert "workflow_call:" in text
    assert "acquisition_json:" in text
    assert "jobs.compose.outputs.acquisition_json" in text
    assert "steps.compose.outputs.acquisition_json" in text
    assert "jq -c ." in text


def test_acquisition_campaign_is_reusable_and_remains_corpus_read_only() -> None:
    text = ACQUIRE.read_text()

    assert "workflow_call:" in text
    assert "acquisition_json:" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "tests/fixtures/historical" not in text
    assert "selection_provenance_json:" in text


def test_pre_registered_wave_reuses_reviewed_evidence_without_reselection() -> None:
    text = WAVE.read_text()

    assert "uses: ./.github/workflows/compose-historical-acquisition.yml" in text
    assert "uses: ./.github/workflows/acquire-historical-campaign.yml" in text
    assert "37482498880" in text
    assert "historical-market-day-sample-37482498880" in text
    assert "37490008931" in text
    assert "cash-acquisition-case-plan-37490008931" in text
    assert ".funding.market_dates | length" in text
    assert ".cash_cases | length" in text
    assert 'expected_funding_count: 5' in text
    assert 'expected_cash_count: 3' in text
    assert "corpus_mutation: false" in text


def test_pre_registered_wave_has_no_corpus_or_review_write_authority() -> None:
    text = WAVE.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "tests/fixtures/historical" not in text
