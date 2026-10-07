# 2026-10-07-funding-promotion-handoff: Freeze exact Funding promotion inputs

Issue: #35
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Version and validate the exact planner handoff inputs for the already-approved Wave 002/003 Funding review waves so later promotion can be invoked without manually reconstructing run/artifact/wave identities.

## Current facts

- Current pinned Funding corpus is 8 distinct days.
- Wave 002 planner run 37596889005 produced `waves/preregistered-review-002-wave-001.json` with 12 Funding items.
- Wave 003 planner run 37600237687 produced `waves/preregistered-review-003-wave-001.json` with 12 Funding items.
- The two study windows are non-overlapping; planner outputs contain 24 distinct Funding dates.
- Both planner artifacts and all 24 compact artifacts are currently unexpired and carry sha256 digests.
- Existing `Promote Planned Historical Wave` workflow is the canonical execution path and requires explicit `workflow_dispatch`.
- This task must not introduce a push fallback or directly mutate historical corpus fixtures.

## Constraints and invariants

- Preserve planner-produced campaign IDs and item ordering exactly.
- Preserve exact planner run IDs, artifact names, artifact IDs, digests and wave-file paths.
- No automatic promotion dispatch.
- No corpus fixture changes.
- No Cash evidence changes.
- No Stage-2 threshold activation.

## Acceptance criteria

- [x] Issue and governance boundary are versioned before implementation.
- [ ] Exact Wave 002 planner handoff is versioned.
- [ ] Exact Wave 003 planner handoff is versioned.
- [ ] Exact 24 compact refs are versioned without edits.
- [ ] Offline validation proves 12 + 12 unique Funding dates and no overlap.
- [ ] Validation checks campaign IDs, planner artifact digests and expected counts.
- [ ] Every currently referenced compact artifact is rechecked as present, unexpired and sha256-addressed.
- [ ] Handoff explicitly targets `Promote Planned Historical Wave`.
- [ ] Full PR CI and Historical Smoke pass.
- [ ] No workflow or corpus mutation is introduced.

## Implementation slices

- [x] 1. Open Issue #35 and create this branch/plan.
- [ ] 2. Commit exact planner-wave snapshots and handoff metadata.
- [ ] 3. Add offline handoff validator/tests.
- [ ] 4. Record live artifact existence/digest preflight.
- [ ] 5. Run full PR gates.
- [ ] 6. Archive/merge this handoff task and stop at explicit promotion dispatch boundary.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Handoff validator | exact two planner waves / 24 refs | pending |
| Artifact preflight | source/planner Actions metadata | pending |
| Static/API/E2E | PR Ruleset | pending |
| Historical smoke | PR workflow | pending |

## Decision gates

The actual promotion `workflow_dispatch` is intentionally outside this task. The connected GitHub integration cannot create workflow-dispatch events, and the repository explicitly prohibits using push fallback for new corpus facts.

## Evidence log

- 2026-10-07: Wave 002 planner artifact 11470314464 / sha256:8f1189786a43d9bf5ef265d99f0a07544357a6f7ab2c097576329d67246ed187 is unexpired.
- 2026-10-07: Wave 003 planner artifact 11472665816 / sha256:8aa8e9b5b3e82a2226b8334f5fdccda870e201ff2b832582a5cc601742645850 is unexpired.
- 2026-10-07: Wave 002 source run 37593545181 exposes 12 unexpired Funding compact artifacts with sha256 digests.
- 2026-10-07: Wave 003 source run 37597427096 exposes 12 unexpired Funding compact artifacts with sha256 digests.

## Deviations and discoveries

None yet.

## Resume from here

Commit exact handoff metadata plus the two planner wave snapshots, then add an offline validator that proves counts, dates, provenance and workflow target without dispatching promotion.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: explicit promotion dispatch and review/merge of resulting corpus PRs
