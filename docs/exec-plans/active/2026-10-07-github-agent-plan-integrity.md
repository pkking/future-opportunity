# Phase 1: GitHub-native Agent Plan Integrity

Issue: #6
Status: VERIFYING
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
- [x] 3. Add validator, tests, and CI gate.
- [x] 4. Update AGENTS.md and link corpus review plan to Issue #5.
- [x] 5. Validate the PR and record exact CI evidence.
- [x] 6. Verify repository ruleset activation and required checks.

## Verification matrix

| Gate | Expected evidence | Status |
|---|---|---|
| Plan integrity | Issue+Plan traceability on PR | passed on CI 37567111849 |
| Unit | `uv run pytest tests/test_agent_plan_integrity.py` | passed via Code-level tests in CI 37567111849 |
| Static/code/API/E2E | existing `ci.yml` | passed on CI 37567111849 |
| Main ruleset | API configuration | active ruleset 24626996; required checks configured; no bypass actors |

## Decision gates

No product/strategy decisions required. Repository administrator activated the mandatory `main` ruleset.

## Evidence log

- 2026-10-07: GitHub rulesets endpoint returned [] and branch protection GET returned 403 for the connected GitHub App.
- 2026-10-07: Created Issue #5 for corpus review work and Issue #6 for this rollout.
- 2026-10-07: CI 37567111849 passed all five jobs on 816007cc31be641cf2899226c3d01f429ebf659b; Historical Backtest Smoke 37567111785 also passed.
- 2026-10-07: verified active repository Ruleset `main` (ID 24626996) targets main/default branch, requires PRs plus Agent plan integrity, Static and architecture safety, Code-level tests, API contract tests, E2E strategy acceptance; deletion/non-fast-forward blocked; bypass_actors empty; current_user_can_bypass=never.

## Resume from here

Re-run CI after this evidence-only plan update. If the final PR head is green and Ruleset still reports active enforcement, merge PR #7, verify main CI, then move this plan to completed and close Issue #6.

## Completion

Final implementation commit: pending
CI run: pending
Ruleset enforcement: active Ruleset 24626996
Remaining unassessed items: approval/merge
