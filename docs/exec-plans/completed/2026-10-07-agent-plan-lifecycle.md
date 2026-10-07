# 2026-10-07-agent-plan-lifecycle: Close the agent plan lifecycle

Issue: #9
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make plan completion a valid, enforceable GitHub lifecycle transition so finished work can move from `active/` to `completed/` without bypassing the required `Agent plan integrity` check. Reconcile stale finished plans left by Issues #5, #6 and #8.

## Non-goals

- No strategy, economics, exchange, or live-trading changes.
- No weakening of PR-to-Issue traceability.
- No automatic Issue closure before its completion PR merges.

## Current facts

- The lifecycle implementation merged via PR #10 as `1fa08351ca72ebe2997ce0680832c90284c043f5`.
- Main CI 37573086977 passed after that merge.
- Ruleset `main` continues to require Agent plan integrity, Static, Code, API and E2E checks.
- Issues #5, #6 and #8 are closed and their plans are under `completed/`.
- This completion-only PR is the final proof that a task can archive its own plan while its Issue remains open for validation.

## Constraints and invariants

- GitHub Issue remains the canonical task identity.
- Completion PR validation still requires the Issue to be open.
- Completed plans require COMPLETED state, no unchecked acceptance/slices and concrete completion evidence.
- Path traversal and arbitrary plan locations remain rejected.
- Ruleset checks remain mandatory.

## Acceptance criteria

- [x] PR metadata accepts exactly one canonical active or completed execution-plan path.
- [x] Active plans retain active-state and recovery-checkpoint validation.
- [x] Completed plans require `Status: COMPLETED`.
- [x] Completed plans reject unchecked acceptance criteria or implementation slices.
- [x] Completed plans require concrete final commit, CI run and remaining-unassessed values.
- [x] Issue validation still requires the referenced Issue to be open during the PR.
- [x] Tests cover valid active/completed paths, incomplete completion, mismatched Issue and traversal.
- [x] AGENTS.md and the execution-plan template document the completion transition.
- [x] Finished plans for Issues #5, #6 and #8 are reconciled and moved to `completed/`.
- [x] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Reconcile main, Issues and active plans; identify lifecycle gap.
- [x] 2. Extend validator and focused tests.
- [x] 3. Update repository contract/template.
- [x] 4. Reconcile/archive completed #5/#6/#8 plans.
- [x] 5. Run final CI, merge implementation, close #5/#6 and finalize this plan in a completion-only PR.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR #10 CI 37572995629 | passed |
| Focused tests | Code-level tests in 37572995629 | passed |
| Static | 37572995629 | passed |
| Code | 37572995629 | passed |
| API | 37572995629 | passed |
| E2E | 37572995629 / artifact 11461915924 | passed |
| Historical smoke | 37572995630 | passed |
| Main integration | 37573086977 | passed |

## Decision gates

None. This closes an inconsistency in the already accepted GitHub-native agent workflow.

## Evidence log

- 2026-10-07: startup reconciliation found Issues #5/#6 still open and plans #5/#6/#8 still under `active/`.
- 2026-10-07: identified the validator's active-only path restriction as an obstacle to self-archival.
- 2026-10-07: validator/tests were extended to distinguish active and completed contracts; AGENTS.md/template were updated.
- 2026-10-07: completed plans #5/#6/#8 were reconciled with real merge/CI evidence and archived.
- 2026-10-07: README corpus facts were reconciled to Funding=8 / Cash=5.
- 2026-10-07: first PR #10 CI found the empty-resume-section regex bug; the test remained strict and the validator was fixed to inspect section content.
- 2026-10-07: final PR #10 CI 37572995629 and Historical Smoke 37572995630 passed.
- 2026-10-07: PR #10 merged as 1fa08351ca72ebe2997ce0680832c90284c043f5; main CI 37573086977 passed.
- 2026-10-07: Issues #5 and #6 were closed after the archival implementation merged.

## Deviations and discoveries

- The first lifecycle implementation exposed a real checkpoint-validation bug, which was fixed without weakening the test.
- Current README sample counts had drifted from repository facts and were corrected while historical execution plans remained immutable snapshots.

## Resume from here

Completed. New non-trivial work should start from an open GitHub Issue and active plan; the final completion PR may reference the completed plan and the Issue is closed only after that PR merges.

## Completion

Final commit: 1fa08351ca72ebe2997ce0680832c90284c043f5
CI run: https://github.com/pkking/future-opportunity/actions/runs/37573086977
E2E artifact: strategy-e2e-evidence artifact 11461915924, sha256:2f14dfcd31045ee1be237c80144f39eee003522e56419dc2b813cece2073b6fb
Remaining unassessed items: none for the agent execution-plan lifecycle
