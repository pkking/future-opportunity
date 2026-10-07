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

- [x] PR metadata accepts exactly one canonical active or completed execution-plan path.
- [x] Active plans retain current active-state and recovery-checkpoint validation.
- [x] Completed plans require `Status: COMPLETED`.
- [x] Completed plans reject unchecked acceptance criteria or implementation slices.
- [x] Completed plans require concrete final commit, CI run, and remaining-unassessed values.
- [x] Issue validation still requires the referenced Issue to be open during the PR.
- [x] Tests cover valid active/completed paths, incomplete completion, mismatched Issue, and traversal.
- [x] AGENTS.md and execution-plan template document the completion transition.
- [x] Finished plans for Issues #5, #6 and #8 are reconciled and moved to `completed/`.
- [ ] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Reconcile main, Issues and active plans; identify lifecycle gap.
- [x] 2. Extend validator and focused tests.
- [x] 3. Update repository contract/template.
- [x] 4. Reconcile/archive completed #5/#6/#8 plans.
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
- 2026-10-07: validator/tests now distinguish active and completed contracts; AGENTS.md/template document completion PR semantics.
- 2026-10-07: reconciled plans #5/#6/#8 with real merge/CI evidence and moved them to `completed/` on this branch.
- 2026-10-07: corrected current README corpus facts to Funding=8 / Cash=5.
- 2026-10-07: PR #10 first CI found a real validator bug: an empty `Resume from here` section was accepted because the regex consumed the following heading. Kept the failing test and changed validation to inspect the section body explicitly.

## Deviations and discoveries

- README historical corpus counts were stale at 2+2 after PR #3/#4; updated current documentation to the committed 8 Funding / 5 Cash baseline while preserving historical plan snapshots.

## Resume from here

Open the implementation PR for Issue #9, verify all required checks, merge it, close Issues #5/#6, then exercise the new completed-plan path in a completion-only PR for Issue #9.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: pending
