# 2026-10-07-agent-plan-lifecycle: Close the agent plan lifecycle

Issue: #9
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make plan completion a valid, enforceable GitHub lifecycle transition so finished work can move from `active/` to `completed/` without bypassing the required `Agent plan integrity` check. Reconcile the stale finished plans left by Issues #5, #6 and #8.

## Non-goals

- No strategy, economics, exchange, or live-trading changes.
- No weakening of PR-to-Issue traceability.
- No automatic closure of an Issue before its completion PR merges.

## Current facts

- Main is green at commit `d6d325d59ee266a3a13d055b99c0868573843380`.
- Ruleset `main` requires Agent plan integrity plus Static, Code, API and E2E checks.
- The validator currently accepts only `docs/exec-plans/active/*.md`.
- Issues #5 and #6 remain open even though their implementation is merged and verified.
- Issue #8 is closed, but its completed plan still remains under `active/`.
- Three stale plans therefore disagree with GitHub delivery state.

## Constraints and invariants

- GitHub Issue remains the canonical task identity.
- A completion PR must still reference an open Issue until the PR is merged.
- A completed plan must carry stronger evidence than an active plan: COMPLETED state, no unchecked acceptance/slices, and concrete completion fields.
- Path traversal or arbitrary plan locations remain rejected.
- Existing Ruleset checks must not be weakened.

## Acceptance criteria

- [ ] PR metadata accepts exactly one canonical active or completed execution-plan path.
- [ ] Active plans retain current active-state and recovery-checkpoint validation.
- [ ] Completed plans require `Status: COMPLETED`.
- [ ] Completed plans reject unchecked acceptance criteria or implementation slices.
- [ ] Completed plans require concrete final commit, CI run, and remaining-unassessed values.
- [ ] Issue validation still requires the referenced Issue to be open during the PR.
- [ ] Tests cover valid active/completed paths, incomplete completion, mismatched Issue, and traversal.
- [ ] AGENTS.md and execution-plan template document the completion transition.
- [ ] Finished plans for Issues #5, #6 and #8 are reconciled and moved to `completed/`.
- [ ] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Reconcile main, Issues and active plans; identify lifecycle gap.
- [ ] 2. Extend validator and focused tests.
- [ ] 3. Update repository contract/template.
- [ ] 4. Reconcile/archive completed #5/#6/#8 plans.
- [ ] 5. Run final CI, merge, close #5/#6, then finalize this plan in a completion-only PR.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Plan integrity | `Agent plan integrity` | active/completed transition enforced | pending |
| Focused tests | `uv run pytest tests/test_agent_plan_integrity.py -v` | all pass | pending |
| Static | `Static and architecture safety` | success | pending |
| Code | `Code-level tests` | success | pending |
| API | `API contract tests` | success | pending |
| E2E | `E2E strategy acceptance` | success | pending |

## Decision gates

None. This closes an inconsistency in the already accepted GitHub-native agent workflow.

## Evidence log

- 2026-10-07: startup reconciliation found Issues #5/#6 still open and plans #5/#6/#8 still under `active/` after their implementation/PRs were merged.
- 2026-10-07: identified validator restriction to `active/` as a direct obstacle to self-archival through the required PR gate.

## Deviations and discoveries

None yet.

## Resume from here

Extend `scripts/validate_agent_plan.py` to distinguish active and completed plan contracts, add focused tests, then archive the three stale finished plans in the same PR.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: pending
