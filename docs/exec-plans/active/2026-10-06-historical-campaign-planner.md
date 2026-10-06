# 2026-10-06-historical-campaign-planner: Read-only candidate inventory and wave planning

Status: VERIFYING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Avoid manually copying dozens of exact preparation run/artifact pairs when
growing the historical corpus from 2 pinned market days per strategy toward
the Stage-2 evidence threshold (30 per strategy, 90 preferred).

Provide a read-only planning flow:

```text
explicit preparation run IDs
 -> enumerate compact artifact names + GitHub artifact digests
 -> independently verify run/parent artifact provenance + compact checksums
 -> inspect strategy/date/dataset identity
 -> subtract already-pinned days and reject collisions
 -> produce deterministic <=31-item campaign manifests + readiness forecast
 -> operator reviews and explicitly dispatches promotion
```

No promotion or PR creation in this plan.

## Governing contracts

- AGENTS.md; docs/design-baseline-v0.1.md; docs/agents/workflow.md;
  docs/agents/testing.md.
- ADR-0006 historical provenance; ADR-0007 Stage-1/Stage-2 boundaries.
- Existing completed historical artifact promotion/campaign plans.
- Versioned tests/fixtures/historical/corpus-index.json is source of truth.
- Existing promotion workflow revalidates every proposed artifact before write.

## Non-goals

- No direct corpus changes, no PR push or merge.
- No automatic discovery of all runs across an organization.
- No auto-promotion of draft campaign manifests.
- No Stage-2 activation or return threshold changes.
- No raw exchange archive download or live trading.

## Current facts

- Main corpus has 2 pinned Funding Carry and 2 pinned Cash-and-Carry days.
- PR #3 proposes Funding 2026-09-03 + Cash 2026-06-03 (CI and historical smoke
  green; not merged). Planner must not claim open PR facts are main-pinned.
- Funding 2026-09-04 has commit-ready artifact from run 37434976457.
- Campaign promotion workflow supports exact run/artifact pairs, max 31 items,
  atomic rollback, PR/handoff and offline CI.
- Repository GitHub-token policy prohibits Actions-created PRs; planner is
  read-only and needs only actions:read/contents:read.

## Acceptance criteria

- [x] Extract reusable, read-only compact fixture inspector that enforces
  manifest status, canonical checksums, and run/parent provenance.
- [x] Versioned candidate inventory input/output with source run/artifact
  identities and validated strategy/date/dataset fields.
- [x] Deterministic manifest planner partitions candidates into waves of
  at most 31, excludes already-pinned identities and rejects ambiguous
  strategy/date collisions.
- [x] Readiness forecast reports baseline pinned days and projected counts
  separately; never counts proposed days as pinned.
- [x] Unit tests for duplicate candidates, conflicting strategy/date,
  pinned exclusions, ordering, split waves, corrupted manifests and no-op.
- [x] Read-only workflow accepts explicit run IDs, independently confirms
  compact/parent Actions artifact provenance, and uploads candidate wave
  manifests plus machine-readable report.
- [x] Workflow self-check uses known historical runs, without promotion.
- [x] README/testing contract explains planner vs promotion boundary.
- [x] All Static/Code/API/Reference E2E plus workflow self-check green.
- [ ] Plan evidence archived once verified.

## Implementation slices

- [x] 1. Read-only compact inspector and tests.
- [x] 2. Pure candidate inventory / deterministic campaign wave planner.
- [x] 3. CLI + machine-readable reports, with tests.
- [x] 4. Explicit Actions discovery workflow (read-only), integration proof.
- [x] 5. Documentation and final CI; archive.

## Decision gates

None. Planning does not weaken manual human approval or write boundaries.

## Evidence log

- 2026-10-06: prior campaign plan archived; PR #3 checks (37435522881,
  37435522957) green; main code workflow self-check 37439004069 green.
- 2026-10-06: source inspector `inspect_historical_compact_fixture` reuses
  strict manifest, provenance and canonical fixture validators without staging
  corpus changes. Read-only symlink and uncommitted status tests were added.
- 2026-10-06: pure deterministic campaign-wave planner supports safe names,
  up to 31 candidates per wave, stable ordering, conflict and duplicate
  detection, and separate pinned/projected readiness counts. One successful
  local CI run for the planning core was 37440572971.
- 2026-10-06: the read-only Actions planner run 37441177683 passed with explicit
  source runs 37327493270 and 37434976457. Artifact
  historical-campaign-planner-37441177683 (ID 11401521198) contains a full
  provenance inventory, a report, and waves/selftest-review-only-wave-001.json.
  It excluded one already-pinned Funding 2026-09-02 fixture and selected one
  Funding 2026-09-04 candidate. Valid current coverage remained Funding 2,
  Cash 2; projection if candidate were merged: Funding 3, Cash 2.
  No corpus files, branches or PRs were modified by the planner.
- 2026-10-06: CLI integration test collection initially failed in CI runs
  37441552559 and 37441641331 because tests imported `scripts` as a package,
  while it is intentionally a command-line scripts directory, not an installed
  module. This was not a market/business semantics failure.
- 2026-10-06: moved reusable candidate inventory parsing into
  `future_opportunity.backtest.campaign_inventory`; retained the CLI as a thin
  wrapper and updated tests to import the installed package. Final CI run
  37441854295 passed Static/Architecture, Code-level, API, and Reference E2E.
- 2026-10-06: README and docs/agents/testing.md now document exact-run
  acquisition, 31-item waves, read-only permission bounds, actual versus
  projected readiness and the limitation that unmerged PRs are not automatically
  deducted. Automatic promotion/merge and Stage-2 activation remain outside
  this plan.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static and architecture safety | CI 37441854295 | passed |
| Code-level tests including inventory CLI | CI 37441854295 | passed |
| API contract | CI 37441854295 | passed |
| Reference strategy E2E | CI 37441854295 | passed |
| Read-only actual Actions run inventory and wave | run 37441177683 / artifact 11401521198 | passed |
| Historical pinned corpus semantics | unchanged Stage-1 policy and main corpus | verified by existing historical smoke 37440900279 |

## Resume from here

All behavior and documentation work is complete. After this plan evidence
commit passes CI, mark COMPLETED and move it to
`docs/exec-plans/completed/2026-10-06-historical-campaign-planner.md`.
PR #3 remains open for human review. Do not automatically promote or merge
any planner-produced wave.

## Completion

Final implementation commit: d497b014120b3e5798fd4b3daf0edf0394bd2cb6
CI runs: 37441854295 (all four gates green)
Planner workflow: 37441177683 (success), artifact 11401521198
Remaining unassessed items: pending PR #3 human review; future Stage-2 policy requires a separate ADR/approval
