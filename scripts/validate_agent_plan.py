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
PLAN_LINE = re.compile(r"(?im)^Plan:\s*(docs/exec-plans/active/[a-zA-Z0-9][a-zA-Z0-9_-]*\.md)\s*$")
PLAN_ISSUE = re.compile(r"(?im)^Issue:\s*#([1-9][0-9]*)\s*$")
LEGACY_PRS = {1, 2, 3, 4}
LEGACY_ALLOWED_PREFIX = "tests/fixtures/historical/"
REQUIRED_SECTIONS = (
    "## Objective",
    "## Acceptance criteria",
    "## Implementation slices",
    "## Verification matrix",
    "## Resume from here",
)


class IntegrityError(ValueError):
    """A PR is missing independently inspectable planning evidence."""


def parse_metadata(body: str) -> tuple[int, str]:
    issues = ISSUE_LINE.findall(body)
    plans = PLAN_LINE.findall(body)
    if len(issues) != 1 or len(plans) != 1:
        raise IntegrityError("PR body must contain exactly one 'Issue: #N' and one 'Plan: docs/exec-plans/active/<id>.md' line")
    return int(issues[0]), plans[0]


def validate_plan(body: str, plan_path: str, issue: int, root: Path) -> None:
    # Restrict paths to the canonical active plan directory (including symlinks).
    plan = (root / plan_path).resolve()
    active = (root / "docs/exec-plans/active").resolve()
    if plan.parent != active or not plan.is_file():
        raise IntegrityError("Plan does not exist in active execution plans")
    content = plan.read_text(encoding="utf-8")
    matches = PLAN_ISSUE.findall(content)
    if matches != [str(issue)]:
        raise IntegrityError("Plan must contain exactly one Issue: #N matching the PR")
    if any(section not in content for section in REQUIRED_SECTIONS):
        raise IntegrityError("Plan misses required execution or resume section")
    if not re.search(r"(?m)^Status:\s*(PLANNING|IMPLEMENTING|VERIFYING|PAUSED|BLOCKED_DECISION|BLOCKED_EVIDENCE|READY_FOR_REVIEW)\s*$", content):
        raise IntegrityError("Plan must declare a recognized active status")
    if not re.search(r"(?s)## Resume from here\s*\n\s*\n?\S", content):
        raise IntegrityError("Plan requires a nonempty recovery checkpoint")


def validate_issue(repo: str, issue: int, token: str) -> None:
    if not token:
        raise IntegrityError("GITHUB_TOKEN is required to verify the Issue through GitHub")
    url = f"https://api.github.com/repos/{repo}/issues/{issue}"
    req = Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "future-opportunity-plan-integrity",
    })
    try:
        with urlopen(req, timeout=15) as res:
            obj = json.load(res)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as ex:
        raise IntegrityError(f"Cannot verify Issue #{issue}: {ex}") from ex
    if "pull_request" in obj or obj.get("number") != issue or obj.get("state") != "open":
        raise IntegrityError(f"#{issue} must be an open GitHub Issue, not a PR")


def validate(event: dict, root: Path, changed_files: list[str], *, repo: str, token: str, online: bool = True) -> str:
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        raise IntegrityError("Expected GitHub pull_request event")
    number = pr.get("number", event.get("number"))
    if not isinstance(number, int):
        raise IntegrityError("PR number missing")
    if number in LEGACY_PRS and all(
        path.startswith(LEGACY_ALLOWED_PREFIX) for path in changed_files
    ) and changed_files:
        return f"Legacy historical fixture-only PR #{number}: narrow grandfather exception"
    issue, plan = parse_metadata(pr.get("body") or "")
    validate_plan(pr.get("body") or "", plan, issue, root)
    if online:
        validate_issue(repo, issue, token)
    return f"PR #{number} -> Issue #{issue} -> {plan}: traceable"


def changed_paths() -> list[str]:
    # CI checkout must fetch history; compare GitHub-provided immutable base SHA.
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
            event, Path.cwd(), changed_paths(),
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
