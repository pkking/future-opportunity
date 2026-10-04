from pathlib import Path


def test_agent_contract_map_is_complete() -> None:
    required = (
        Path("AGENTS.md"),
        Path("docs/agents/workflow.md"),
        Path("docs/agents/testing.md"),
        Path("docs/exec-plans/TEMPLATE.md"),
        Path("docs/exec-plans/active/README.md"),
        Path("docs/exec-plans/completed/README.md"),
        Path("tests/e2e/AGENTS.md"),
        Path("tests/e2e/strategy-targets.json"),
        Path("tests/e2e/fixtures/reference-scenarios.json"),
    )
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []


def test_root_agents_file_points_to_execution_and_evidence_sources() -> None:
    contract = Path("AGENTS.md").read_text()

    for required_reference in (
        "docs/design-baseline-v0.1.md",
        "docs/v0-implementation-status.md",
        "docs/agents/workflow.md",
        "docs/agents/testing.md",
        "docs/exec-plans/active/",
        "tests/e2e/strategy-targets.json",
    ):
        assert required_reference in contract

    for mandatory_concept in (
        "Plan before editing",
        "Resume from here",
        "UNASSESSED",
        "E2E strategy acceptance",
        "Definition of done",
    ):
        assert mandatory_concept in contract


def test_ci_has_explicit_observable_gates() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()

    for gate in (
        "Static and architecture safety",
        "Code-level tests",
        "API contract tests",
        "E2E strategy acceptance",
    ):
        assert gate in workflow

    assert "E2E_EVIDENCE_PATH" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "if: always()" in workflow


def test_active_work_has_resume_checkpoint_when_present() -> None:
    plans = [
        path
        for path in Path("docs/exec-plans/active").glob("*.md")
        if path.name != "README.md"
    ]

    for plan in plans:
        text = plan.read_text()
        assert "## Resume from here" in text
        assert "Status:" in text
