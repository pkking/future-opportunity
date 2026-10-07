"""Verify PR -> Issue -> execution-plan traceability.

GitHub issues and merged PRs are delivery state; plan text is not proof of CI.
Run this on trusted pull_request workflows, never on pull_request_target.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ISSUE_LINE = re.compile(r"(?im)^Issue:\s*#([1-9][0-9]*)\s*$")
PLAN_LINE = re.compile(
    r"(?im)^Plan:\s*"
    r"(docs/exec-plans/(?:active|completed)/"
    r"[a-zA-Z0-9][a-zA-Z0-9_-]*\.md)\s*$"
)
PLAN_ISSUE = re.compile(r"(?im)^Issue:\s*#([1-9][0-9]*)\s*$")
ACTIVE_STATUS = re.compile(
    r"(?m)^Status:\s*"
    r"(PLANNING|IMPLEMENTING|VERIFYING|PAUSED|"
    r"BLOCKED_DECISION|BLOCKED_EVIDENCE|READY_FOR_REVIEW)\s*$"
)
COMPLETED_STATUS = re.compile(r"(?m)^Status:\s*COMPLETED\s*$")
LEGACY_PRS = {1, 2, 3, 4}
LEGACY_ALLOWED_PREFIX = "tests/fixtures/historical/"
REQUIRED_SECTIONS = (
    "## Objective",
    "## Acceptance criteria",
    "## Implementation slices",
    "## Verification matrix",
    "## Resume from here",
    "## Completion",
)


class IntegrityError(ValueError):
    """A PR is missing independently inspectable planning evidence."""


def parse_metadata(body: str) -> tuple[int, str]:
    issues = ISSUE_LINE.findall(body)
    plans = PLAN_LINE.findall(body)
    if len(issues) != 1 or len(plans) != 1:
        raise IntegrityError(
            "PR body must contain exactly one 'Issue: #N' and one canonical "
            "'Plan: docs/exec-plans/{active|completed}/<id>.md' line"
        )
    return int(issues[0]), plans[0]


def _section(content: str, heading: str) -> str:
    start = content.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    end = content.find("\n## ", start)
    return content[start:] if end < 0 else content[start:end]


def _completion_value(completion: str, label: str) -> str:
    match = re.search(rf"(?im)^{re.escape(label)}\s*(.+?)\s*$", completion)
    if not match:
        raise IntegrityError(f"Completed plan requires '{label}'")
    value = match.group(1).strip()
    if not value or value.lower() in {"pending", "tbd", "todo", "unknown"}:
        raise IntegrityError(f"Completed plan requires concrete '{label}' evidence")
    return value


def validate_plan(plan_path: str, issue: int, root: Path) -> str:
    plan = (root / plan_path).resolve()
    active = (root / "docs/exec-plans/active").resolve()
    completed = (root / "docs/exec-plans/completed").resolve()
    if plan.parent not in {active, completed} or not plan.is_file():
        raise IntegrityError("Plan does not exist in a canonical execution-plan directory")

    content = plan.read_text(encoding="utf-8")
    matches = PLAN_ISSUE.findall(content)
    if matches != [str(issue)]:
        raise IntegrityError("Plan must contain exactly one Issue: #N matching the PR")
    if any(section not in content for section in REQUIRED_SECTIONS):
        raise IntegrityError("Plan misses required execution, recovery, or completion section")

    if plan.parent == active:
        if not ACTIVE_STATUS.search(content):
            raise IntegrityError("Active plan must declare a recognized active status")
        if not _section(content, "## Resume from here").strip():
            raise IntegrityError("Active plan requires a nonempty recovery checkpoint")
        return "active"

    if not COMPLETED_STATUS.search(content):
        raise IntegrityError("Completed plan must declare Status: COMPLETED")

    for heading in ("## Acceptance criteria", "## Implementation slices"):
        if re.search(r"(?m)^\s*- \[ \]", _section(content, heading)):
            raise IntegrityError(f"Completed plan has unchecked items in {heading}")

    completion = _section(content, "## Completion")
    _completion_value(completion, "Final commit:")
    _completion_value(completion, "CI run:")
    _completion_value(completion, "Remaining unassessed items:")
    return "completed"


def validate_issue(repo: str, issue: int, token: str) -> None:
    if not token:
        raise IntegrityError("GITHUB_TOKEN is required to verify the Issue through GitHub")
    url = f"https://api.github.com/repos/{repo}/issues/{issue}"
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "future-opportunity-plan-integrity",
        },
    )
    try:
        with urlopen(req, timeout=15) as res:
            obj = json.load(res)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as ex:
        raise IntegrityError(f"Cannot verify Issue #{issue}: {ex}") from ex
    if (
        "pull_request" in obj
        or obj.get("number") != issue
        or obj.get("state") != "open"
    ):
        raise IntegrityError(f"#{issue} must be an open GitHub Issue, not a PR")


def validate(
    event: dict,
    root: Path,
    changed_files: list[str],
    *,
    repo: str,
    token: str,
    online: bool = True,
) -> str:
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise IntegrityError("Expected GitHub pull_request event")
    number = pr.get("number", event.get("number"))
    if not isinstance(number, int):
        raise IntegrityError("PR number missing")
    if (
        number in LEGACY_PRS
        and changed_files
        and all(path.startswith(LEGACY_ALLOWED_PREFIX) for path in changed_files)
    ):
        return (
            f"Legacy historical fixture-only PR #{number}: "
            "narrow grandfather exception"
        )

    issue, plan = parse_metadata(pr.get("body") or "")
    state = validate_plan(plan, issue, root)
    if online:
        validate_issue(repo, issue, token)
    return f"PR #{number} -> Issue #{issue} -> {plan}: {state} and traceable"


def changed_paths() -> list[str]:
    base = os.environ.get("PR_BASE_SHA", "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base):
        raise IntegrityError("PR_BASE_SHA must be an exact 40-hex base SHA")
    cmd = ["git", "diff", "--name-only", f"{base}...HEAD"]
    try:
        return subprocess.check_output(cmd, text=True).splitlines()
    except subprocess.CalledProcessError as ex:
        raise IntegrityError("Unable to compute PR diff; fail closed") from ex


def main() -> int:
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        message = validate(
            event,
            Path.cwd(),
            changed_paths(),
            repo=os.environ["GITHUB_REPOSITORY"],
            token=os.environ.get("GH_TOKEN", ""),
        )
    except (IntegrityError, KeyError, OSError, json.JSONDecodeError) as ex:
        print(f"PLAN INTEGRITY FAILED: {ex}", file=sys.stderr)
        return 1
    print(f"PLAN INTEGRITY OK: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
