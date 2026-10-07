# Phase 1: GitHub-native Agent Plan Integrity

Issue: #6
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make GitHub Issues the durable task identity, preserve the repository-local execution plan as the resume checkpoint, and enforce PR-to-Issue-to-Plan traceability in CI.

## Non-goals

- No automatic PR merge, automatic trading, or strategy policy changes.
- No claims that PR traceability proves semantic acceptance.
- No weakening of existing code/API/E2E gates.

## Current facts

- Main currently has no repository rulesets according to the accessible API.
- Branch-protection endpoint returns 403 to the connected integration.
- PR #1-#4 predate this contract; only historical fixture-only changes may take a narrowly scoped legacy exception.
- Existing active corpus review plan was linked to Issue #5 in this rollout.

## Acceptance criteria

- [ ] A PR validator rejects missing/mismatched Issue/Plan links.
- [ ] GitHub API verifies the referenced issue is open and is not a PR.
- [ ] Existing historical-fixture-only PRs (#1-#4) remain reviewable without allowing arbitrary workflow/code changes.
- [ ] CI runs the gate on pull_request for new changes.
- [ ] Unit tests cover valid, malformed, missing, and legacy cases.
- [ ] Root AGENTS.md requires canonical PR/Issue/Plan traceability.
- [ ] Ruleset enforcement is verified or explicitly reported as requiring repository admin access.
- [ ] Main-branch CI and historical smoke remain unchanged.

## Implementation slices

- [x] 1. Open tracking Issues #5 and #6.
- [x] 2. Create isolated feature branch.
- [ ] 3. Add validator, tests, and CI gate.
- [ ] 4. Update AGENTS.md and link corpus review plan to Issue #5.
- [ ] 5. Validate the PR and record exact CI evidence.
- [ ] 6. Verify repository ruleset; leave unresolved permission blocker explicit.

## Verification matrix

| Gate | Expected evidence | Status |
|---|---|---|
| Plan integrity | Issue+Plan traceability on PR | pending |
| Unit | `uv run pytest tests/test_agent_plan_integrity.py` | pending |
| Static/code/API/E2E | existing `ci.yml` | pending |
| Main ruleset | API configuration or explicit permission limitation | blocked: connector lacks administration permission |

## Decision gates

No product/strategy decisions required. Enabling mandatory repository rules requires an administrator with GitHub Actions/Repository Settings access.

## Evidence log

- 2026-10-07: GitHub rulesets endpoint returned [] and branch protection GET returned 403 for the connected GitHub App.
- 2026-10-07: Created Issue #5 for corpus review work and Issue #6 for this rollout.

## Resume from here

After the PR workflow runs, inspect its Plan Integrity check, fix all failing tests, and request administrator activation of the main branch ruleset; do not claim enforcement before verification.

## Completion

Final implementation commit: pending
CI run: pending
Ruleset enforcement: pending (requires administrator)
Remaining unassessed items: approval/merge
