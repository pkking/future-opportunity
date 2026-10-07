# 2026-10-07-pending-corpus-review: Audit pending corpus PR compatibility

Issue: #5
Status: PLANNING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make simultaneous review-only corpus campaigns safe to reason about when
multiple open PRs modify `tests/fixtures/historical/corpus-index.json`.

Produce a read-only, machine-verifiable report:

```text
main versioned corpus index
+ full index snapshots from open corpus PR heads
 -> independently identify proposed entry-market-day additions
 -> reject baseline deletions/identity drift
 -> detect duplicate and conflicting strategy/date across proposals
 -> separate pinned counts from PR-only projected union
 -> flag shared-index reconciliation after the first merge
```

This work does not merge or mutate PRs, does not automatically approve Stage 2,
and does not change strategy economics or return targets.

## Current facts

- Main: Funding Carry 2 pinned days, Cash-and-Carry 2 pinned days.
- Open PR #3 proposes Funding 2026-09-03 and Cash 2026-06-03.
- Open PR #4 proposes five January Funding dates and two June Cash dates.
- New strategy/date facts in #3 and #4 are currently disjoint.
- PR #3 CI + Historical Smoke: passed 37558106807 not applicable (PR #4);
  PR #3 checks were previously green. PR #4 checks 37558106807 and
  37558106798 passed.
- PR heads are based on different historical main commits and both modify
  corpus-index.json. GitHub mergeability must be re-read after each merge;
  disjoint strategy/date does not prove conflict-free git auto-merge.
- ADR-0007 Stage 1 still gates provenance/replay semantics only. Unmerged PRs
  must never count toward `minimum_ready_now`.

## Governing contracts

- AGENTS.md
- docs/design-baseline-v0.1.md
- docs/agents/workflow.md
- docs/agents/testing.md
- ADR-0007
- tests/e2e/historical-target-policy.json
- Existing read-only corpus/campaign planning and corpus index contracts.

## Acceptance criteria

- [ ] Parse remote full corpus-index snapshots without assuming remote fixture
      bytes have been locally downloaded or verified.
- [ ] Reject malformed, duplicate, unsupported strategy/date, and
      unsafe/ambiguous fixture identifiers.
- [ ] Reject proposals that remove or alter any current pinned baseline entry.
- [ ] Report per-PR added days separately from pinned main counts.
- [ ] Detect overlaps by strategy/date between pending PRs and distinguish
      exact identity overlap from differing dataset collisions.
- [ ] Combined projected counts deduplicate overlapping identities.
- [ ] Pending proposals are explicitly unverified by this index-only analysis;
      PR CI/Historical Smoke are separate evidentiary requirements.
- [ ] Warn that two or more PRs editing shared corpus index require
      reconciliation/revalidation after the first merge.
- [ ] Provide read-only CLI with deterministic JSON evidence.
- [ ] Provide read-only Actions workflow to inspect open corpus PRs and archive
      the report, without making GitHub writes.
- [ ] Include unit/CLI/workflow-contract tests covering the actual 2+2,
      1+1, 5+2 projection.
- [ ] README/testing guidance documents merge-safe review and Stage-1 policy.
- [ ] Complete Static, Code, API, Reference E2E, and historical smoke checks.

## Implementation slices

- [ ] 1. Pure index-snapshot reconciliation model and tests.
- [ ] 2. JSON evidence CLI and targeted tests.
- [ ] 3. Read-only GitHub PR snapshot inspection workflow and contract tests.
- [ ] 4. Capture real #3/#4 review evidence and document operator steps.
- [ ] 5. Verify final CI, record outcomes, archive.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static / architecture | `uv run ruff check .` via CI | pending |
| Code tests | pure reconciliation, CLI, workflow contract | pending |
| API contract | CI API gate | pending |
| E2E | deterministic reference strategy acceptance | pending |
| Historical smoke | unchanged Stage-1 pinned corpus | pending |
| Review report | read-only Actions artifact for #3 and #4 | pending |

## Decisions

None: read-only metadata reconciliation does not affect product or approval
semantics. Human PR review/merge remains required.

## Evidence log

- 2026-10-07: inspected exact `main`, PR #3 and PR #4 corpus index snapshots.
  Main has Funding 2 / Cash 2. PR #3 adds 1+1, PR #4 adds 5+2.
  Across the proposals, no new strategy/date overlaps were observed.
  The combined *unmerged* theoretical count is Funding 8 / Cash 5.
  A previous connector PR metadata shortcut reported false mergeability;
  the GitHub raw PR endpoint reported PR #3 `clean` and PR #4
  `unknown` at inspection time. Do not infer final mergeability.
- 2026-10-07: newest main push CI 37558281980 succeeded.

## Resume from here

Before resuming implementation, reconcile this stale checkpoint with commits 6a2d1b5, 135af09, b61d834, e320ffd and CI run 37559011055. Do not repeat already merged work or conclude completion from commit subjects alone.

Implement pure reconciliation of versioned corpus index snapshots with strict
identity validation, then add code tests before any workflow. Keep open PR
proposal counts separate from pinned baseline readiness.

## Completion

Final implementation commit:
CI run:
Read-only review artifact:
Remaining unassessed items:
