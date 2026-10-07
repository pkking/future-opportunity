# 2026-10-07-pending-corpus-review: Audit pending corpus PR compatibility

Issue: #5
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make simultaneous review-only corpus campaigns safe to reason about when multiple open PRs modify the historical corpus index, without treating unmerged proposals as pinned readiness.

## Non-goals

- No automatic merge or corpus mutation.
- No Stage-2 activation or economics threshold change.
- No inference of PR mergeability from strategy/date disjointness alone.

## Current facts

- The read-only reconciliation model, CLI and GitHub Actions workflow are merged on main.
- PR #3 and PR #4 were subsequently reconciled against current main, revalidated, and merged in sequence.
- Current main has no open PRs after those merges.
- Pending proposals never counted as pinned readiness before merge.

## Acceptance criteria

- [x] Parse remote full corpus-index snapshots without assuming remote fixture bytes are locally verified.
- [x] Reject malformed, duplicate, unsupported strategy/date, and unsafe fixture identities.
- [x] Reject proposals that remove or alter current pinned baseline entries.
- [x] Report per-PR added days separately from pinned main counts.
- [x] Detect exact overlaps and conflicting strategy/date identities.
- [x] Deduplicate projected union counts.
- [x] Keep pending proposals explicitly separate from PR CI/Historical Smoke evidence.
- [x] Flag shared-index reconciliation after the first merge.
- [x] Provide deterministic read-only JSON CLI evidence.
- [x] Provide read-only Actions inspection workflow with uploaded evidence.
- [x] Cover the observed 2+2 baseline, 1+1 PR #3 and 5+2 PR #4 projection.
- [x] Document merge-safe review and Stage-1 semantics.
- [x] Complete Static, Code, API, Reference E2E and historical verification.

## Implementation slices

- [x] 1. Pure index-snapshot reconciliation model and tests.
- [x] 2. JSON evidence CLI and targeted tests.
- [x] 3. Read-only GitHub PR snapshot inspection workflow and contract tests.
- [x] 4. Capture real #3/#4 review evidence and use it during sequential reconciliation.
- [x] 5. Verify final CI and archive.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static / architecture | CI 37559011055 | passed |
| Code tests | CI 37559011055 | passed |
| API contract | CI 37559011055 | passed |
| E2E | CI 37559011055 | passed |
| Read-only PR review workflow | Actions 37558964679 | passed |
| Sequential corpus integration | PR #3/#4 final checks and main CI | passed |

## Decision gates

None. Human PR merge and Stage-2 policy remain separate decisions.

## Evidence log

- 2026-10-07: implementation commits 6a2d1b5, 135af09, b61d834, bf86302 and e320ffd established the reconciliation model, CLI, workflow and contract tests.
- 2026-10-07: main CI 37559011055 passed at e320ffdd22857e532813a27a917d2f69d4acca81.
- 2026-10-07: read-only pending-PR review workflow 37558964679 succeeded while PR #3/#4 were open.
- 2026-10-07: PR #3 was rebased/reconciled and merged as 416b47d97fc99ab7ce10dabfdbcb51ccb97795cb; main CI 37571404933 and Historical Smoke 37571404909 passed.
- 2026-10-07: PR #4 was then reconciled on that new baseline and merged as d6d325d59ee266a3a13d055b99c0868573843380; main CI 37571708476 and Historical Smoke 37571708501 passed.

## Deviations and discoveries

The original active checkpoint became stale because implementation had already landed. GitHub-native Plan Integrity work exposed and corrected that drift.

## Resume from here

Completed. For any future concurrent corpus PRs, run the read-only pending-PR review and reconcile every surviving PR after the first shared-index merge.

## Completion

Final commit: e320ffdd22857e532813a27a917d2f69d4acca81
CI run: https://github.com/pkking/future-opportunity/actions/runs/37559011055
Read-only review: https://github.com/pkking/future-opportunity/actions/runs/37558964679
Remaining unassessed items: none for the pending-PR compatibility capability
