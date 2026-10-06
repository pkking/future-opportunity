# 2026-10-06-historical-artifact-promotion: Promote prepared historical artifacts into corpus

Status: COMPLETED
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
  -> push review branch
  -> open PR when repository policy permits
     OR emit a machine-readable PR handoff
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
- Promotion always creates a review branch and never mutates main directly.
- It opens a PR when repository policy permits; otherwise it emits an exact
  machine-readable handoff for a connected GitHub integration/operator.
- The PR branch must run normal CI and Historical Backtest Smoke before merge.
- Raw archives remain excluded.

## Acceptance criteria

- [x] Add a deterministic promotion application/script for a local compact artifact directory.
- [x] Promotion validates manifest provenance before staging.
- [x] Promotion updates corpus-index.json in stable order without duplicate facts.
- [x] Exact re-promotion is idempotent.
- [x] Divergent existing fixture fails closed.
- [x] Add code tests for Funding and Cash promotion paths.
- [x] Add workflow_dispatch promotion workflow that downloads an exact artifact from an exact run.
- [x] Workflow verifies source run/artifact identity against manifest provenance.
- [x] Workflow creates a review branch and either a PR or an exact PR handoff;
  never writes main directly.
- [x] Promotion PR runs normal CI + Historical Backtest Smoke.
- [x] Documentation explains prepare -> promote -> review -> merge.
- [x] Final CI green.

## Implementation slices

- [x] 1. Define promotion result/errors and local staging algorithm.
- [x] 2. Add deterministic corpus-index update + idempotency tests.
- [x] 3. Add exact artifact/run provenance verification.
- [x] 4. Add GitHub Actions promotion workflow with review branch + PR/handoff.
- [x] 5. Document operator workflow and recovery.
- [x] 6. Verify complete CI and archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | passed CI 37433904415 |
| Code | promotion/idempotency/divergence tests | passed CI 37433904415 |
| API | no regression | passed CI 37433904415 |
| Reference E2E | unchanged deterministic targets green | passed CI 37433904415 |
| Historical smoke | existing corpus remains green | passed; PR run 37433749712 green |
| Promotion workflow | exact artifact -> validated branch -> PR/handoff | 9/2 no-op 37433173833 green; 9/3 staging 37433493554 passed through branch push |

## Decision gates

None. Promotion is explicitly user/operator-triggered and review-based.

A future decision would be required before automatic promotion or automatic merge.

## Evidence log

- 2026-10-06: previous corpus-expansion plan completed at 2 pinned days per
  strategy; final CI run 37431649316 passed.
- 2026-10-06: local promotion core implemented for both Funding and Cash compact
  fixtures. It validates commit-ready manifests, exact normalized file sets,
  safe dataset IDs, existing corpus validity, duplicate identities, stable index
  ordering, and full offline corpus replay before leaving staged changes.
- 2026-10-06: promotion tests cover Funding/Cash staging, exact re-promotion,
  manifest-format-only idempotency, strategy/date collision, provenance-run
  mismatch, extra files, and divergent canonical content. CI 37432920903 passed
  after the promotion identity semantics update.
- 2026-10-06: Actions artifact API was verified to expose digest values. The
  promotion workflow now binds the selected compact artifact to an exact source
  run and independently verifies the parent preparation artifact ID + SHA-256
  against derived_from_artifact.
- 2026-10-06: first no-op workflow run 37432507284 correctly exposed that the
  repository's manually reconstructed Funding 2026-09-02 manifest was not the
  authoritative compact artifact manifest. The pinned manifest was repaired to
  the original commit-ready artifact provenance; CI 37432759685 and Historical
  Smoke 37432759626 passed.
- 2026-10-06: a second no-op workflow run 37432817169 exposed that bytewise JSON
  comparison treated formatting as data drift. Idempotency was refined to
  structural JSON equality for manifest plus bytewise equality for canonical
  evidence files. This does not weaken checksum validation.
- 2026-10-06: no-op promotion self-verification run 37433173833 succeeded after
  the identity fix. Exact run/artifact/parent-digest validation passed, the
  staged result was `already_present`, corpus verification/PR creation were
  correctly skipped, and promotion evidence was uploaded.
- 2026-10-06: README and testing contract now document prepare -> promote ->
  review -> merge, explicit no-direct-main/no-auto-merge boundaries, artifact
  identity checks, idempotent recovery, and PR gating requirements.

## Deviations and discoveries

- Repository policy currently disallows pull requests created by
  `GITHUB_TOKEN`, even though the job receives `pull-requests: write`.
  Promotion run 37433493554 therefore validated/staged/replayed the 2026-09-03
  fixture and pushed review branch
  `historical-corpus/okx-btc-usdt-funding-carry-2026-09-03-v1-target-compact-37433493554-1`,
  but GitHub rejected `gh pr create`.
- Increasing repository Actions authority is not required. The safer implementation
  now treats this policy as a review handoff: the workflow records the exact
  branch/title/source evidence in `pr-handoff.json` instead of failing the
  validated promotion. A connected GitHub integration can open the PR.
- The first PR-body implementation used Markdown backticks inside an interpolated
  shell heredoc, causing command substitution. It was replaced with safe
  `printf` construction.
- PR #2 was opened from the exact validated 2026-09-03 review branch via the
  connected GitHub integration. PR-triggered CI run 37433749631 and Historical
  Backtest Smoke run 37433749712 both passed. No auto-merge was enabled.

## Resume from here

Completed. PR #2 remains open for human review/merge; automatic merge is
explicitly outside this plan. Future corpus days use the explicit preparation
and promotion workflows documented in README.md.

## Completion

Final implementation commit: 0a7e2afe0ffb9bc32e2ce6e2667099d6d9da4f4b
CI run: 37434113945 passed all four required gates
Promotion workflow evidence: no-op 37433173833; real 9/3 promotion 37433493554; PR #2 checks 37433749631 / 37433749712 passed
Remaining unassessed items: PR #2 human review/merge only; intentionally outside automatic promotion

- 2026-10-06: final plan/documentation CI run 37434113945 passed Static,
  Code-level, API contract, and E2E strategy acceptance gates.
- 2026-10-06: PR #2 remains intentionally open. Its head commit
  b89fc99c46b682f3c894e35e745ceb97ee79146e passed PR CI run 37433749631 and
  Historical Backtest Smoke run 37433749712. Review/merge is a human action
  outside the promotion automation.
