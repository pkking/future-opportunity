# 2026-10-06-historical-campaign-planner: Read-only candidate inventory and wave planning

Status: PLANNING
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

- [ ] Extract reusable, read-only compact fixture inspector that enforces
  manifest status, canonical checksums, and run/parent provenance.
- [ ] Versioned candidate inventory input/output with source run/artifact
  identities and validated strategy/date/dataset fields.
- [ ] Deterministic manifest planner partitions candidates into waves of
  at most 31, excludes already-pinned identities and rejects ambiguous
  strategy/date collisions.
- [ ] Readiness forecast reports baseline pinned days and projected counts
  separately; never counts proposed days as pinned.
- [ ] Unit tests for duplicate candidates, conflicting strategy/date,
  pinned exclusions, ordering, split waves, corrupted manifests and no-op.
- [ ] Read-only workflow accepts explicit run IDs, independently confirms
  compact/parent Actions artifact provenance, and uploads candidate wave
  manifests plus machine-readable report.
- [ ] Workflow self-check uses known historical runs, without promotion.
- [ ] README/testing contract explains planner vs promotion boundary.
- [ ] All Static/Code/API/Reference E2E plus workflow self-check green.
- [ ] Plan evidence archived once verified.

## Implementation slices

- [ ] 1. Read-only compact inspector and tests.
- [ ] 2. Pure candidate inventory / deterministic campaign wave planner.
- [ ] 3. CLI + machine-readable reports, with tests.
- [ ] 4. Explicit Actions discovery workflow (read-only), integration proof.
- [ ] 5. Documentation and final CI; archive.

## Decision gates

None. Planning does not weaken manual human approval or write boundaries.

## Evidence log

- 2026-10-06: prior campaign plan archived; PR #3 checks (37435522881,
  37435522957) green; main code workflow self-check 37439004069 green.

## Resume from here

Inspect the existing single-artifact promotion validation boundary. Add a
read-only inspection entrypoint reusing exactly the existing validators.
Do not change Stage-1/Stage-2 policy or campaign write behavior.

## Completion

Final implementation commit:
CI runs:
Planner workflow:
Remaining unassessed items:
