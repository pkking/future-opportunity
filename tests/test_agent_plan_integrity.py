"""Focused offline contract tests for GitHub Issue/plan integrity."""
from pathlib import Path
import runpy

import pytest

_contract = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_agent_plan.py")
)
IntegrityError = _contract["IntegrityError"]
parse_metadata = _contract["parse_metadata"]
validate = _contract["validate"]


def _write_plan(
    tmp_path: Path,
    *,
    issue: int = 9,
    state: str = "active",
    status: str = "IMPLEMENTING",
    unchecked: bool = True,
    completion_pending: bool = True,
) -> str:
    directory = tmp_path / "docs/exec-plans" / state
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "phase2.md"
    box = " " if unchecked else "x"
    final = "pending" if completion_pending else "abc123"
    ci = "pending" if completion_pending else "https://github.com/example/run/1"
    remaining = "pending" if completion_pending else "none"
    path.write_text(
        f"Issue: #{issue}\n"
        f"Status: {status}\n"
        "## Objective\nTest\n"
        "## Acceptance criteria\n"
        f"- [{box}] criterion\n"
        "## Implementation slices\n"
        f"- [{box}] slice\n"
        "## Verification matrix\n| gate | state |\n"
        "## Resume from here\nContinue safely\n"
        "## Completion\n"
        f"Final commit: {final}\n"
        f"CI run: {ci}\n"
        f"Remaining unassessed items: {remaining}\n",
        encoding="utf-8",
    )
    return f"docs/exec-plans/{state}/phase2.md"


def make_event(tmp_path: Path, *, issue: int = 9, plan: str | None = None):
    plan = plan or _write_plan(tmp_path, issue=issue)
    body = f"Issue: #{issue}\nPlan: {plan}"
    return {"number": 10, "pull_request": {"number": 10, "body": body}}


def check(event, root, files=None):
    return validate(
        event,
        root,
        files or ["src/example.py"],
        repo="pkking/future-opportunity",
        token="",
        online=False,
    )


def test_valid_active_plan(tmp_path):
    assert "active and traceable" in check(make_event(tmp_path), tmp_path)


def test_valid_completed_plan(tmp_path):
    plan = _write_plan(
        tmp_path,
        state="completed",
        status="COMPLETED",
        unchecked=False,
        completion_pending=False,
    )
    event = make_event(tmp_path, plan=plan)
    assert "completed and traceable" in check(event, tmp_path)


def test_completed_plan_rejects_active_status(tmp_path):
    plan = _write_plan(
        tmp_path,
        state="completed",
        status="VERIFYING",
        unchecked=False,
        completion_pending=False,
    )
    with pytest.raises(IntegrityError, match="Status: COMPLETED"):
        check(make_event(tmp_path, plan=plan), tmp_path)


def test_completed_plan_rejects_unchecked_work(tmp_path):
    plan = _write_plan(
        tmp_path,
        state="completed",
        status="COMPLETED",
        unchecked=True,
        completion_pending=False,
    )
    with pytest.raises(IntegrityError, match="unchecked items"):
        check(make_event(tmp_path, plan=plan), tmp_path)


def test_completed_plan_rejects_pending_evidence(tmp_path):
    plan = _write_plan(
        tmp_path,
        state="completed",
        status="COMPLETED",
        unchecked=False,
        completion_pending=True,
    )
    with pytest.raises(IntegrityError, match="concrete"):
        check(make_event(tmp_path, plan=plan), tmp_path)


def test_missing_issue_ref_is_rejected(tmp_path):
    event = make_event(tmp_path)
    event["pull_request"]["body"] = (
        "Plan: docs/exec-plans/active/phase2.md"
    )
    with pytest.raises(IntegrityError, match="exactly one"):
        check(event, tmp_path)


def test_mismatched_plan_issue_is_rejected(tmp_path):
    event = make_event(tmp_path)
    event["pull_request"]["body"] = (
        "Issue: #8\nPlan: docs/exec-plans/active/phase2.md"
    )
    with pytest.raises(IntegrityError, match="matching"):
        check(event, tmp_path)


def test_noncanonical_or_traversal_plan_rejected(tmp_path):
    _write_plan(tmp_path)
    event = make_event(tmp_path)
    event["pull_request"]["body"] = (
        "Issue: #9\nPlan: docs/exec-plans/active/../active/phase2.md"
    )
    with pytest.raises(IntegrityError, match="exactly one"):
        check(event, tmp_path)


def test_missing_active_checkpoint_rejected(tmp_path):
    event = make_event(tmp_path)
    p = tmp_path / "docs/exec-plans/active/phase2.md"
    p.write_text(
        p.read_text(encoding="utf-8").replace("Continue safely", ""),
        encoding="utf-8",
    )
    with pytest.raises(IntegrityError, match="checkpoint"):
        check(event, tmp_path)


def test_legacy_only_historical_data_allowed(tmp_path):
    event = {"pull_request": {"number": 4, "body": ""}}
    assert "grandfather" in validate(
        event,
        tmp_path,
        ["tests/fixtures/historical/2026/test.json"],
        repo="pkking/future-opportunity",
        token="",
        online=False,
    )
    with pytest.raises(IntegrityError, match="exactly one"):
        validate(
            event,
            tmp_path,
            [".github/workflows/ci.yml"],
            repo="pkking/future-opportunity",
            token="",
            online=False,
        )


def test_legacy_empty_diff_cannot_bypass(tmp_path):
    with pytest.raises(IntegrityError):
        validate(
            {"pull_request": {"number": 3, "body": ""}},
            tmp_path,
            [],
            repo="pkking/future-opportunity",
            token="",
            online=False,
        )


def test_duplicate_issue_lines_rejected():
    with pytest.raises(IntegrityError):
        parse_metadata(
            "Issue: #6\nIssue: #7\n"
            "Plan: docs/exec-plans/active/phase2.md"
        )
