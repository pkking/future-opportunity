"""Regression guard: creating evidence Release tags must not launch path-based push CI.

GitHub deliberately ignores push.paths on tag pushes, so any workflow
whose on.push uses paths with no tag/branch restriction will fire for
funding-vps-YYYY-MM-DD (and diagnostic) Release tags.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOWS = ROOT / ".github/workflows"


def _push_keys(source: str) -> str | None:
    match = re.search(r"(?m)^  push:\s*\n", source)
    if match is None:
        return None
    rest = source[match.end():]
    # Stop at next 'on' event or top-level YAML key. Do not confuse
    # jobs/steps or unrelated workflow_dispatch inputs with push filters.
    boundary = re.search(r"(?m)^(?:  [a-zA-Z_-]+:|[a-zA-Z_-]+:)", rest)
    return rest[:boundary.start()] if boundary else rest


def _path_filter(body: str) -> bool:
    return re.search(r"(?m)^    paths(?:-ignore)?:", body) is not None


def _branch_only_or_explicit_tag_selection(body: str) -> bool:
    return re.search(
        r"(?m)^    (?:branches|branches-ignore|tags|tags-ignore):", body
    ) is not None


def test_all_path_based_push_workflows_exclude_release_tags():
    found = 0
    guarded = 0
    bad = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        config = _push_keys(path.read_text())
        if config is None or not _path_filter(config):
            continue
        found += 1
        if not _branch_only_or_explicit_tag_selection(config):
            bad.append(path.name)
        elif re.search(r"(?m)^    tags-ignore:", config):
            assert re.search(
                r"(?m)^    tags-ignore: \['\*\*'\]", config
            ), f"{path.name} must exclude ALL tags"
            guarded += 1
    assert not bad, (
        "GitHub ignores push.paths filters for tag pushes: "
        + ", ".join(bad)
    )
    assert found >= 30, "policy guard unexpectedly lost most historical workflows"
    assert guarded >= 30, "expected native tag exclusions are absent"


def test_tag_event_filter_does_not_modify_branch_ci_semantics():
    ci = (WORKFLOWS / "ci.yml").read_text()
    assert "  push:\n    branches: [main]" in ci
    assert "  pull_request:" in ci
    sample = (WORKFLOWS / "prepare-funding-historical-batch.yml").read_text()
    assert "  workflow_dispatch:" in sample
    assert "  push:\n    tags-ignore: ['**']\n    paths:" in sample


def test_helper_rejects_unfiltered_path_push_but_accepts_guarded_versions():
    raw = "on:\n  workflow_dispatch:\n  push:\n    paths:\n      - scripts/foo.py\n"
    parsed = _push_keys(raw)
    assert parsed is not None and _path_filter(parsed)
    assert not _branch_only_or_explicit_tag_selection(parsed)
    fixed = raw.replace("  push:\n", "  push:\n    tags-ignore: ['**']\n")
    fixed_config = _push_keys(fixed)
    assert fixed_config is not None and _branch_only_or_explicit_tag_selection(fixed_config)
    main_only = "on:\n  push:\n    branches: [main]\n    paths:\n      - foo.py\n"
    main_config = _push_keys(main_only)
    assert main_config is not None and _branch_only_or_explicit_tag_selection(main_config)


def test_release_audit_and_original_market_capture_are_unmodified():
    text = (WORKFLOWS / "audit-funding-vps-github-release.yml").read_text()
    assert "  release:\n    types: [published]" in text
    assert "    if: startsWith(github.event.release.tag_name, 'funding-vps-')" in text
    assert "permissions:\n  contents: read" in text
    assert "  push:" not in text
    capture = (WORKFLOWS / "capture-funding-preentry-scheduled.yml").read_text()
    assert "  schedule:" in capture and "37 23 * * *" in capture
    assert "  push:" not in capture
