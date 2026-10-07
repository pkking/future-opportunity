"""Focused offline contract tests for GitHub Issue/plan integrity."""
from pathlib import Path

import pytest

import runpy

_contract = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "validate_agent_plan.py"))
IntegrityError = _contract["IntegrityError"]
parse_metadata = _contract["parse_metadata"]
validate = _contract["validate"]


def make_repo(tmp_path: Path, issue: int = 6):
    active = tmp_path / "docs/exec-plans/active"
    active.mkdir(parents=True)
    path = active / "phase1.md"
    path.write_text(
        f"Issue: #{issue}\nStatus: IMPLEMENTING\n"
        "## Objective\nTest\n## Acceptance criteria\n- [ ] test\n"
        "## Implementation slices\n- [ ] slice\n"
        "## Verification matrix\n| gate | state |\n"
        "## Resume from here\nRun next check\n"
    )
    body = f"Issue: #{issue}\nPlan: docs/exec-plans/active/phase1.md"
    event = {"number": 7, "pull_request": {"number": 7, "body": body}}
    return event


def check(event, root, files=None):
    return validate(event, root, files or ["src/example.py"], repo="pkking/future-opportunity", token="", online=False)


def test_valid_plan_and_issue(tmp_path):
    assert "traceable" in check(make_repo(tmp_path), tmp_path)


def test_missing_issue_ref_is_rejected(tmp_path):
    event = make_repo(tmp_path)
    event["pull_request"]["body"] = "Plan: docs/exec-plans/active/phase1.md"
    with pytest.raises(IntegrityError, match="exactly one"):
        check(event, tmp_path)


def test_missing_or_mismatched_plan_issue_is_rejected(tmp_path):
    event = make_repo(tmp_path)
    event["pull_request"]["body"] = "Issue: #8\nPlan: docs/exec-plans/active/phase1.md"
    with pytest.raises(IntegrityError, match="matching"):
        check(event, tmp_path)


def test_closed_plan_path_or_traversal_rejected(tmp_path):
    event = make_repo(tmp_path)
    event["pull_request"]["body"] = "Issue: #6\nPlan: docs/exec-plans/completed/phase1.md"
    with pytest.raises(IntegrityError, match="exactly one"):
        check(event, tmp_path)


def test_missing_checkpoint_rejected(tmp_path):
    event = make_repo(tmp_path)
    p = tmp_path / "docs/exec-plans/active/phase1.md"
    p.write_text(p.read_text().replace("Run next check", ""))
    with pytest.raises(IntegrityError, match="checkpoint"):
        check(event, tmp_path)


def test_legacy_only_historical_data_allowed(tmp_path):
    e = {"pull_request": {"number": 4, "body": ""}}
    assert "grandfather" in validate(e, tmp_path, ["tests/fixtures/historical/2026/test.json"], repo="pkking/future-opportunity", token="", online=False)
    with pytest.raises(IntegrityError, match="exactly one"):
        validate(e, tmp_path, [".github/workflows/ci.yml"], repo="pkking/future-opportunity", token="", online=False)


def test_legacy_empty_diff_cannot_bypass(tmp_path):
    with pytest.raises(IntegrityError):
        validate({"pull_request": {"number": 3, "body": ""}}, tmp_path, [], repo="pkking/future-opportunity", token="", online=False)


def test_duplicate_issue_lines_rejected():
    with pytest.raises(IntegrityError):
        parse_metadata("Issue: #6\nIssue: #7\nPlan: docs/exec-plans/active/phase1.md")
