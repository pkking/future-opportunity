# 2026-10-06-historical-corpus-campaign: Batch historical corpus promotion toward Stage 2

Status: COMPLETED
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

- [x] Define versioned campaign manifest schema.
- [x] Add local atomic batch promotion application.
- [x] Batch promotion supports mixed Funding + Cash compact fixtures.
- [x] Exact already-present fixtures are idempotent within a batch.
- [x] One invalid/divergent item rolls back all newly staged items.
- [x] Campaign order does not affect final corpus index.
- [x] Add code tests for atomicity, duplicates, mixed strategy, no-op and ordering.
- [x] Add workflow_dispatch batch promotion workflow.
- [x] Workflow verifies exact run/artifact/parent digests for every item.
- [x] Workflow limits batch size to a bounded number.
- [x] Workflow produces one review branch and one PR/handoff for effective changes.
- [x] Campaign evidence includes per-item status and resulting readiness counts.
- [x] Documentation explains prepare-many -> promote-campaign -> review -> merge.
- [x] Final CI green.

## Implementation slices

- [x] 1. Campaign manifest model/parser.
- [x] 2. Atomic local batch staging + rollback.
- [x] 3. Campaign evidence/readiness output.
- [x] 4. Exact multi-artifact workflow acquisition/verification.
- [x] 5. Single review branch + PR/handoff.
- [x] 6. Documentation and final verification.
- [x] 7. Archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | passed PR CI 37435522881 |
| Code | campaign parsing/atomicity/idempotency tests | passed PR CI 37435522881 |
| API | no regression | passed PR CI 37435522881 |
| Reference E2E | unchanged deterministic targets green | passed PR CI 37435522881 |
| Historical smoke | existing + staged campaign corpus green | passed PR run 37435522957 |
| Campaign workflow | multiple exact artifacts -> one review proposal | passed run 37435411557; PR #3 open |

## Decision gates

None for batch promotion itself.

Stage-2 activation, automatic promotion, or automatic merge still require
separate explicit decisions.

## Evidence log

- 2026-10-06: single-artifact promotion completed and archived. Main CI and
  policy-safe promotion self-test were green; PR #2 demonstrates the review path
  with PR-triggered CI + Historical Smoke green.
- 2026-10-06: versioned campaign schema implemented with safe campaign/artifact
  identifiers, exact run/artifact pairs, duplicate rejection, and max 31 items.
- 2026-10-06: local campaign promotion composes the verified single-artifact
  promotion primitive and adds whole-campaign rollback. Mixed Funding+Cash,
  no-op, ordering, duplicate input, and later-item failure rollback are covered
  by code tests. CI 37434628064 passed.
- 2026-10-06: campaign promotion evidence includes per-item promotion status and
  post-staging ADR-0007 readiness counts. CLI re-verifies resolved acquisition
  items against the operator campaign manifest.
- 2026-10-06: multi-artifact workflow run 37434868861 succeeded with the pinned
  Funding 2026-09-02 and Cash 2026-06-02 artifacts from two different source
  runs. Exact compact + parent artifact digests were verified independently and
  the campaign correctly resolved to an all-idempotent no-op.
- 2026-10-06: Cash discovery run 37434982233 verified that 2026-06-03 official
  futureschain history contains BTC-USDT-260626. Funding 2026-09-04 and Cash
  2026-06-03 preparation runs were started as the first real changed mixed
  campaign inputs.

- 2026-10-06: changed mixed campaign run 37435411557 completed successfully. Both
  exact source artifact pairs were verified, the corpus was atomically staged,
  the offline validation passed, and one review branch was pushed. Artifact
  11398725802 contains campaign acquisition and promotion evidence.
- 2026-10-06: GitHub integration created review PR #3
  https://github.com/pkking/future-opportunity/pull/3 from that exact branch.
  The branch contains Funding Carry 2026-09-03 and Cash-and-Carry 2026-06-03;
  its readiness is 3/30 per strategy (3/90 preferred). Main remains at 2/30
  per strategy until review/merge.
- 2026-10-06: PR #3 head 0aa69001c9a940417ed379e49d49824171e77149
  passed CI 37435522881 (Static, Code, API, Reference E2E) and Historical
  Smoke 37435522957. No automated merge occurred.
- 2026-10-06: README.md and docs/agents/testing.md document campaign input,
  atomic rollback, evidence boundaries, PR handoff, and manual merge.

## Deviations and discoveries

None.

## Resume from here

The campaign implementation and real two-item review path are verified.
Completed. PR #3 remains open for human review and is intentionally not
auto-merged. Main corpus stays at 2+2 until the reviewed campaign is merged.

## Completion

Final implementation commit: 3f65f5859bbcc7629bb99206178847f00391bf96
CI run: final plan-only main CI 37438952457 (success); PR CI 37435522881 (success); PR Historical Smoke 37435522957 (success)
Campaign workflow evidence: run 37435411557 / artifact 11398725802 / PR #3
Remaining unassessed items: PR #3 human review/merge; Stage-2 distribution targets intentionally not approved
