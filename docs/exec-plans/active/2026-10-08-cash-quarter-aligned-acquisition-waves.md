# 2026-10-08-cash-quarter-aligned-acquisition-waves

Issue: #47
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Turn the approved quarter-aligned Cash policy into two immutable, replayable acquisition waves over the already-frozen 25 Stage-2 dates, while preserving pre-registration provenance and keeping acquisition separate from promotion.

## Approved policy

- Entry time: 00:15:00 UTC.
- Entry dates 2026-01-04 through 2026-03-21 use BTC-USDT-260327.
- Q1 expiry: 2026-03-27T08:00:00+00:00.
- Q1 exit: 2026-03-26T00:15:00+00:00.
- Entry dates 2026-03-28 through 2026-06-23 use BTC-USDT-260626.
- Q2 expiry: 2026-06-26T08:00:00+00:00.
- Q2 exit: 2026-06-25T00:15:00+00:00.
- No date replacement is permitted after outcome observation.

## Evidence boundary

- Capacity run: 37714282539; 177/177 source dates ready, 172 ready/unpinned.
- Frozen selection discovery run: 37714773301.
- Selection-control artifact: 11523362784, sha256:d8118eae5d41eebe7b9f5c44c35acca402043eb17682bd57acd7a9b613545f10.
- Corrected discovery succeeded for all 25 frozen dates.
- BTC-USDT-260327 is present on all 12 Q1 frozen dates.
- BTC-USDT-260626 is present on all 25 frozen dates and is the approved Q2 contract.

## Constraints

- Preserve all 25 frozen dates exactly.
- Selection provenance must be fail-closed and deterministically replayable.
- Do not mislabel availability-only selection as the older SHA-seeded contiguous-date sampler.
- Acquisition workflows may prepare artifacts only; no corpus mutation.
- Promotion remains a separately reviewed explicit workflow-dispatch step.

## Acceptance criteria

- [ ] Repository can validate an explicit availability-only pre-registration provenance kind.
- [ ] Existing pre_registered_sample provenance remains fully backward-compatible.
- [ ] Distribution reporting counts the new provenance kind as pre-registered rather than legacy.
- [ ] Q1 manifest contains exactly 12 frozen dates and the approved 260327 contract/exit semantics.
- [ ] Q2 manifest contains exactly 13 frozen dates and the approved 260626 contract/exit semantics.
- [ ] Q1 + Q2 dates equal the frozen 25-day selection exactly, with no overlap or omission.
- [ ] Both manifests carry the same replayable selection provenance source.
- [ ] A workflow_dispatch handoff prepares exactly one named approved wave and no other dates.
- [ ] Tests cover provenance replay/drift, manifest semantics, and workflow no-promotion boundary.
- [ ] Full CI and Historical Smoke pass.

## Implementation slices

- [x] 1. Create governed Issue/branch/plan and inspect acquisition/provenance contracts.
- [ ] 2. Generalize selection provenance for availability-only deterministic selection.
- [ ] 3. Version approved quarter-aligned policy and Q1/Q2 manifests.
- [ ] 4. Add exact wave preparation workflow.
- [ ] 5. Add unit/workflow-contract tests.
- [ ] 6. Run CI/Smoke, archive and merge.
- [ ] 7. Dispatch Q1 and Q2 preparation runs; review prepared evidence before promotion.

## Decision gates

No further product decision is required for contract or holding-period semantics. Manual workflow dispatch may still be required because the connected GitHub toolset cannot start workflow_dispatch runs.

## Resume from here

Implement replayable availability-selection provenance first, then generate exact Q1/Q2 acquisition manifests and workflow handoff. Merge only after final-head CI/Smoke. After merge, trigger both preparation waves and review all 25 compact fixtures before any promotion.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: implementation, preparation runs, and prepared-fixture review