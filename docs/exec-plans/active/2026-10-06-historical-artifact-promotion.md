# 2026-10-06-historical-artifact-promotion: Promote prepared historical artifacts into corpus

Status: PLANNING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Remove the manual download/copy/index-edit step between successful historical
preparation and the versioned offline corpus.

Provide a reviewable promotion path:

```text
successful preparation artifact
  -> explicit promotion dispatch
  -> download exact artifact
  -> validate compact provenance/checksums
  -> stage fixture
  -> update corpus-index.json deterministically
  -> run corpus/historical smoke validation
  -> open PR
```

The workflow MUST NOT push directly to main.

## Non-goals

- Do not auto-promote every successful preparation run.
- Do not change Stage-1/Stage-2 target policy.
- Do not auto-merge promotion PRs.
- Do not lower provenance or compact-depth checks.
- Do not commit raw exchange archives.
- Do not introduce live trading.

## Governing decisions

- AGENTS.md
- ADR-0006 historical dataset provenance.
- ADR-0007 progressive historical acceptance policy.
- tests/e2e/historical-target-policy.json.
- tests/fixtures/historical/corpus-index.json is the versioned corpus source of truth.

## Current facts

- Funding and Cash preparation workflows emit commit-ready compact artifacts.
- Corpus currently contains 2 Funding Carry days and 2 Cash-and-Carry days.
- Preparation artifacts do not count until committed and indexed.
- Manual artifact download/copy/index editing is the remaining scale bottleneck.
- Final previous-plan CI run 37431649316 passed all required gates.

## Constraints and invariants

- Promotion requires an explicit workflow_dispatch with exact source run/artifact.
- Artifact provenance embedded in manifest must agree with promotion inputs.
- pinning_status must be commit_ready.
- dataset_id/strategy/entry_market_date must come from the manifest, not caller duplication.
- Duplicate dataset IDs, duplicate strategy/date entries, duplicate fixture paths,
  or existing divergent fixture content must fail closed.
- Re-running the same promotion on an already indexed identical fixture should be
  idempotent/no-op.
- Promotion creates a branch + PR for review; never direct main mutation.
- The PR branch must run normal CI and Historical Backtest Smoke before merge.
- Raw archives remain excluded.

## Acceptance criteria

- [ ] Add a deterministic promotion application/script for a local compact artifact directory.
- [ ] Promotion validates manifest provenance before staging.
- [ ] Promotion updates corpus-index.json in stable order without duplicate facts.
- [ ] Exact re-promotion is idempotent.
- [ ] Divergent existing fixture fails closed.
- [ ] Add code tests for Funding and Cash promotion paths.
- [ ] Add workflow_dispatch promotion workflow that downloads an exact artifact from an exact run.
- [ ] Workflow verifies source run/artifact identity against manifest provenance.
- [ ] Workflow creates a review branch/PR and never writes main directly.
- [ ] Promotion PR runs normal CI + Historical Backtest Smoke.
- [ ] Documentation explains prepare -> promote -> review -> merge.
- [ ] Final CI green.

## Implementation slices

- [ ] 1. Define promotion result/errors and local staging algorithm.
- [ ] 2. Add deterministic corpus-index update + idempotency tests.
- [ ] 3. Add exact artifact/run provenance verification.
- [ ] 4. Add GitHub Actions promotion workflow with PR creation.
- [ ] 5. Document operator workflow and recovery.
- [ ] 6. Verify complete CI and archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | pending |
| Code | promotion/idempotency/divergence tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged deterministic targets green | pending |
| Historical smoke | existing corpus remains green | pending |
| Promotion workflow | exact artifact -> proposed corpus PR | pending |

## Decision gates

None. Promotion is explicitly user/operator-triggered and review-based.

A future decision would be required before automatic promotion or automatic merge.

## Evidence log

- 2026-10-06: previous corpus-expansion plan completed at 2 pinned days per
  strategy; final CI run 37431649316 passed.

## Deviations and discoveries

None.

## Resume from here

Inspect compact Funding/Cash manifest common fields and corpus validator APIs.
Implement a local deterministic promotion function that stages one verified
compact directory into a repository checkout and updates corpus-index.json.

## Completion

Final implementation commit:
CI run:
Promotion workflow evidence:
Remaining unassessed items:
