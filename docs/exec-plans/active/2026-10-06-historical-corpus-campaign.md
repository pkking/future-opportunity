# 2026-10-06-historical-corpus-campaign: Batch historical corpus promotion toward Stage 2

Status: PLANNING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Scale Stage-1 corpus growth from isolated one-day promotion PRs to reviewable,
atomic corpus campaigns while preserving per-day provenance and fail-closed
semantics.

Target operator flow:

```text
many successful preparation artifacts
  -> explicit campaign manifest
  -> verify every exact run/artifact independently
  -> atomically stage all compact fixtures
  -> deterministic corpus-index update
  -> corpus/readiness/historical smoke verification
  -> one review branch
  -> one PR or policy-safe PR handoff
```

This reduces review overhead on the path from 2 pinned days per strategy toward
the ADR-0007 minimum of 30 without changing Stage-1 acceptance semantics.

## Non-goals

- No automatic artifact discovery/promotion.
- No automatic PR merge.
- No direct writes to main.
- No Stage-2 distribution thresholds.
- No raw market archives in git.
- No partial campaign commits when one item fails.

## Governing decisions

- AGENTS.md
- ADR-0006 historical dataset provenance
- ADR-0007 progressive historical acceptance policy
- tests/e2e/historical-target-policy.json
- tests/fixtures/historical/corpus-index.json
- completed historical artifact promotion plan

## Current facts

- Main corpus has 2 Funding Carry and 2 Cash-and-Carry pinned market days.
- Single-artifact promotion is validated and idempotent.
- Funding 2026-09-03 is prepared and proposed in PR #2; it is not counted until
  merged.
- PR #2 head b89fc99c46b682f3c894e35e745ceb97ee79146e passed CI 37433749631
  and Historical Backtest Smoke 37433749712.
- Repository policy blocks GITHUB_TOKEN-created PRs. Promotion therefore supports
  review-branch + machine-readable handoff; a connected GitHub integration can
  open the PR without increasing Actions authority.
- Archived promotion plan final main CI gates are green.

## Constraints and invariants

- Campaign input is an explicit ordered list of exact source run/artifact pairs.
- Every compact artifact still validates independently against its parent
  preparation artifact ID/digest and manifest provenance.
- Campaign input must reject duplicate source pairs and duplicate compact names.
- Corpus identity constraints remain one strategy/date fact per strategy.
- Batch staging is atomic: any failed item restores the original index and
  removes all fixture directories newly staged by the campaign.
- Already-present identical items are no-ops and may coexist with new items.
- A campaign with no effective changes is an idempotent no-op.
- Stable index ordering is independent of campaign input order.
- Campaign review branch contains only corpus fixtures/index changes.
- PR creation follows the existing PR-or-handoff policy; no direct main mutation.
- Normal CI + Historical Backtest Smoke remain required before human merge.

## Acceptance criteria

- [ ] Define versioned campaign manifest schema.
- [ ] Add local atomic batch promotion application.
- [ ] Batch promotion supports mixed Funding + Cash compact fixtures.
- [ ] Exact already-present fixtures are idempotent within a batch.
- [ ] One invalid/divergent item rolls back all newly staged items.
- [ ] Campaign order does not affect final corpus index.
- [ ] Add code tests for atomicity, duplicates, mixed strategy, no-op and ordering.
- [ ] Add workflow_dispatch batch promotion workflow.
- [ ] Workflow verifies exact run/artifact/parent digests for every item.
- [ ] Workflow limits batch size to a bounded number.
- [ ] Workflow produces one review branch and one PR/handoff for effective changes.
- [ ] Campaign evidence includes per-item status and resulting readiness counts.
- [ ] Documentation explains prepare-many -> promote-campaign -> review -> merge.
- [ ] Final CI green.

## Implementation slices

- [ ] 1. Campaign manifest model/parser.
- [ ] 2. Atomic local batch staging + rollback.
- [ ] 3. Campaign evidence/readiness output.
- [ ] 4. Exact multi-artifact workflow acquisition/verification.
- [ ] 5. Single review branch + PR/handoff.
- [ ] 6. Documentation and final verification.
- [ ] 7. Archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | pending |
| Code | campaign parsing/atomicity/idempotency tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged deterministic targets green | pending |
| Historical smoke | existing + staged campaign corpus green | pending |
| Campaign workflow | multiple exact artifacts -> one review proposal | pending |

## Decision gates

None for batch promotion itself.

Stage-2 activation, automatic promotion, or automatic merge still require
separate explicit decisions.

## Evidence log

- 2026-10-06: single-artifact promotion completed and archived. Main CI and
  policy-safe promotion self-test were green; PR #2 demonstrates the review path
  with PR-triggered CI + Historical Smoke green.

## Deviations and discoveries

None.

## Resume from here

Implement a versioned campaign manifest parser and an atomic local batch
promotion function by composing the already-verified single-artifact promotion
contract. Prove rollback when a later item fails before adding workflow logic.

## Completion

Final implementation commit:
CI run:
Campaign workflow evidence:
Remaining unassessed items:
