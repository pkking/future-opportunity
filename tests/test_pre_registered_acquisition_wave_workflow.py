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


def test_pre_registered_wave_keeps_first_wave_defaults_without_reselection() -> None:
    text = WAVE.read_text()

    assert "uses: ./.github/workflows/compose-historical-acquisition.yml" in text
    assert "uses: ./.github/workflows/acquire-historical-campaign.yml" in text
    assert "37482498880" in text
    assert "historical-market-day-sample-37482498880" in text
    assert "37490008931" in text
    assert "cash-acquisition-case-plan-37490008931" in text
    assert "corpus_mutation: false" in text


def test_pre_registered_wave_derives_dynamic_boundary_from_canonical_manifest() -> None:
    text = WAVE.read_text()

    assert "id: boundary" in text
    assert "expected_funding=\"$(jq 'length'" in text
    assert "expected_cash=\"$(jq 'length'" in text
    assert "expected_total=$((expected_funding + expected_cash))" in text
    assert 'test "${expected_total}" -ge 1' in text
    assert 'test "${expected_total}" -le 31' in text
    assert "expected_funding_count=${expected_funding}" in text
    assert "expected_cash_count=${expected_cash}" in text
    assert "expected_total_count=${expected_total}" in text
    assert "expected_funding_count: $expected_funding_count" in text
    assert "expected_cash_count: $expected_cash_count" in text
    assert "expected_total_count: $expected_total_count" in text

    assert "expected_funding_count: 5" not in text
    assert "expected_cash_count: 3" not in text


def test_pre_registered_wave_requires_provenance_only_for_nonempty_side() -> None:
    text = WAVE.read_text()

    assert 'if [ "${expected_funding}" -gt 0 ]; then' in text
    assert ".selection_provenance.funding.strategy" in text
    assert 'if [ "${expected_cash}" -gt 0 ]; then' in text
    assert ".selection_provenance.cash.strategy" in text


def test_pre_registered_wave_has_no_corpus_or_review_write_authority() -> None:
    text = WAVE.read_text()

    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull-requests:" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "tests/fixtures/historical" not in text


def test_pre_registered_wave_artifact_identity_uses_derived_expected_counts() -> None:
    text = WAVE.read_text()

    assert "actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100" in text
    assert "compact-artifact-names.txt" in text
    assert "steps.boundary.outputs.expected_funding_count" in text
    assert "steps.boundary.outputs.expected_cash_count" in text
    assert "steps.boundary.outputs.expected_total_count" in text

    assert 'test "${total}" = "${EXPECTED_TOTAL_COUNT}"' in text
    assert 'test "${unique}" = "${EXPECTED_TOTAL_COUNT}"' in text
    assert 'test "${funding}" = "${EXPECTED_FUNDING_COUNT}"' in text
    assert 'test "${cash}" = "${EXPECTED_CASH_COUNT}"' in text

    assert 'test "${total}" = "8"' not in text
    assert 'test "${unique}" = "8"' not in text
    assert 'test "${funding}" = "5"' not in text
    assert 'test "${cash}" = "3"' not in text

    assert (
        "grep -c '^okx-btc-funding-compact-' "
        "artifacts/pre-registered-wave/compact-artifact-names.txt || true"
    ) in text
    assert (
        "grep -c '^okx-btc-cash-and-carry-compact-' "
        "artifacts/pre-registered-wave/compact-artifact-names.txt || true"
    ) in text
    assert "identity_contract_satisfied" in text
    assert "$total == $expected_total" in text
    assert "$funding == $expected_funding" in text
    assert "$cash == $expected_cash" in text
