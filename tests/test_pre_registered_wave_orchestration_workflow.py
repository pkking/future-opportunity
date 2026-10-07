from pathlib import Path


ROOT = Path(__file__).parents[1]
ORCHESTRATOR = ROOT / ".github/workflows/prepare-pre-registered-historical-wave.yml"
SAMPLING = ROOT / ".github/workflows/sample-historical-market-days.yml"
DISCOVERY = ROOT / ".github/workflows/discover-sampled-cash-corpus.yml"
CASE_PLAN = ROOT / ".github/workflows/plan-cash-acquisition-cases.yml"
COMPOSER = ROOT / ".github/workflows/compose-historical-acquisition.yml"
ACQUIRE = ROOT / ".github/workflows/acquire-pre-registered-historical-wave.yml"
CAMPAIGN = ROOT / ".github/workflows/plan-historical-campaign.yml"


def test_orchestrator_dispatch_exposes_study_facts_not_intermediate_ids() -> None:
    text = ORCHESTRATOR.read_text()
    dispatch = text.split("jobs:", 1)[0]

    for field in (
        "funding_start_date:",
        "funding_end_date:",
        "funding_sample_size:",
        "funding_seed:",
        "cash_start_date:",
        "cash_end_date:",
        "cash_sample_size:",
        "cash_seed:",
        "policy_version:",
        "cash_future_id:",
        "cash_expiry_at:",
        "cash_exit_at:",
        "cash_entry_time_utc:",
    ):
        assert field in dispatch

    assert "sampling_run_id:" not in dispatch
    assert "sampling_artifact_name:" not in dispatch
    assert "discovery_run_id:" not in dispatch
    assert "cash_case_plan_run_id:" not in dispatch
    assert "cash_case_plan_artifact_name:" not in dispatch


def test_orchestrator_reuses_existing_evidence_stages_in_one_run() -> None:
    text = ORCHESTRATOR.read_text()

    assert "uses: ./.github/workflows/sample-historical-market-days.yml" in text
    assert "uses: ./.github/workflows/discover-sampled-cash-corpus.yml" in text
    assert "uses: ./.github/workflows/plan-cash-acquisition-cases.yml" in text
    assert "uses: ./.github/workflows/acquire-pre-registered-historical-wave.yml" in text

    assert "needs: cash-sample" in text
    assert "needs: cash-discovery" in text
    assert "needs: [funding-sample, cash-plan]" in text
    assert "sampling_run_id: ${{ github.run_id }}" in text
    assert "discovery_run_id: ${{ github.run_id }}" in text
    assert "funding_sample_run_id: ${{ github.run_id }}" in text
    assert "cash_case_plan_run_id: ${{ github.run_id }}" in text

    assert "funding-historical-market-day-sample-{0}" in text
    assert "cash-historical-market-day-sample-{0}" in text
    assert "cash-acquisition-case-plan-{0}" in text


def test_reused_workflows_expose_workflow_call_without_losing_dispatch() -> None:
    for workflow in (SAMPLING, DISCOVERY, CASE_PLAN, ACQUIRE):
        text = workflow.read_text()
        assert "workflow_dispatch:" in text
        assert "workflow_call:" in text

    sampling = SAMPLING.read_text()
    assert "artifact_name:" in sampling
    assert "SAMPLE_ARTIFACT_NAME:" in sampling
    assert "inputs.artifact_name" in sampling
    assert "github.event_name == 'push' && inputs.strategy == ''" in sampling


def test_same_run_evidence_relaxation_is_exactly_current_run_only() -> None:
    discovery = DISCOVERY.read_text()
    assert 'if [ "${SAMPLING_RUN_ID}" = "${GITHUB_RUN_ID}" ]; then' in discovery
    assert 'test "${source_status}" = "in_progress"' in discovery
    assert 'test "${source_status}" = "completed"' in discovery
    assert 'test "${source_conclusion}" = "success"' in discovery

    case_plan = CASE_PLAN.read_text()
    assert 'if [ "${DISCOVERY_RUN_ID}" = "${GITHUB_RUN_ID}" ]; then' in case_plan
    assert 'test "${source_status}" = "in_progress"' in case_plan
    assert 'test "${source_status}" = "completed"' in case_plan
    assert 'test "${source_conclusion}" = "success"' in case_plan
    assert 'test "${control_count}" = 1' in case_plan

    composer = COMPOSER.read_text()
    assert 'if [ "${FUNDING_SAMPLE_RUN_ID}" = "${GITHUB_RUN_ID}" ]; then' in composer
    assert 'if [ "${CASH_PLAN_RUN_ID}" = "${GITHUB_RUN_ID}" ]; then' in composer
    assert composer.count('test "${source_status}" = "in_progress"') >= 2
    assert composer.count('test "${source_status}" = "completed"') >= 2
    assert composer.count('test "${source_conclusion}" = "success"') >= 2


def test_orchestrator_and_reused_workflows_keep_no_write_authority() -> None:
    for workflow in (ORCHESTRATOR, SAMPLING, DISCOVERY, CASE_PLAN, ACQUIRE):
        text = workflow.read_text()
        assert "contents: write" not in text
        assert "pull-requests:" not in text
        assert "git push" not in text
        assert "gh pr create" not in text


def test_campaign_planner_follows_completed_top_level_orchestration() -> None:
    text = CAMPAIGN.read_text()

    assert '- "Prepare Pre-registered Historical Wave"' in text
    assert "github.event.workflow_run.conclusion == 'success'" in text
    assert "historical-acquisition-control" in text


def test_orchestrator_push_selftest_is_small_and_explicit() -> None:
    text = ORCHESTRATOR.read_text()

    assert "orchestrator-selftest-funding-v1" in text
    assert "orchestrator-selftest-cash-v1" in text
    assert "2026-01-01" in text
    assert "2026-06-03" in text
    assert "BTC-USDT-260626" in text
    assert "2026-06-26T08:00:00+00:00" in text
    assert "2026-06-25T00:15:00+00:00" in text
    assert "inputs.funding_sample_size || '1'" in text
    assert "inputs.cash_sample_size || '1'" in text
