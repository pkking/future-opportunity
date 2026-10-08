# 2026-10-08-cash-quarter-aligned-acquisition-waves

Issue: #47
Status: COMPLETED
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

- [x] Repository can validate an explicit availability-only pre-registration provenance kind.
- [x] Existing pre_registered_sample provenance remains fully backward-compatible.
- [x] Distribution reporting counts the new provenance kind as pre-registered rather than legacy.
- [x] Q1 manifest contains exactly 12 frozen dates and the approved 260327 contract/exit semantics.
- [x] Q2 manifest contains exactly 13 frozen dates and the approved 260626 contract/exit semantics.
- [x] Q1 + Q2 dates equal the frozen 25-day selection exactly, with no overlap or omission.
- [x] Both manifests carry the same replayable selection provenance source.
- [x] A workflow_dispatch handoff prepares exactly one named approved wave and no other dates.
- [x] Tests cover provenance replay/drift, manifest semantics, and workflow no-promotion boundary.
- [x] Full CI and Historical Smoke pass.

## Implementation slices

- [x] 1. Create governed Issue/branch/plan and inspect acquisition/provenance contracts.
- [x] 2. Generalize selection provenance for availability-only deterministic selection.
- [x] 3. Version approved quarter-aligned policy and Q1/Q2 manifests.
- [x] 4. Add exact wave preparation workflow.
- [x] 5. Add unit/workflow-contract tests.
- [x] 6. Run review-head CI/Smoke and archive for final-head validation.
- [x] 7. Stop at the explicit manual workflow-dispatch boundary with immutable Q1/Q2 inputs prepared; preparation runs remain post-merge evidence work.

## Verification matrix

| Gate | Expected |
|---|---|
| Frozen Cash selection | 25 exact dates |
| Availability-selection population | 172 eligible days |
| Availability-selection evidence SHA | 21a48dee14e352c5fbb2488661f45c6fe3e82e74a4759d9eba1347b0bbe6b4b7 |
| Q1 manifest | 12 dates / BTC-USDT-260327 |
| Q2 manifest | 13 dates / BTC-USDT-260626 |
| Q1 + Q2 union | exact frozen 25-day selection |
| Legacy pre_registered_sample | backward compatible |
| New selection classification | pre-registered, explicit availability kind |
| Preparation workflow | workflow_dispatch only |
| Corpus mutation | none |
| Promotion | absent from workflow |
| Required CI | run 37728864055: 5/5 successful |
| Historical Smoke | run 37728864033: successful |

## Decision gates

No further product decision is required for contract or holding-period semantics. Manual workflow dispatch may still be required because the connected GitHub toolset cannot start workflow_dispatch runs.

## Resume from here

PR #48 passed review-head CI/Smoke. Validate the archival head and merge. After merge, manually dispatch q1 and q2 through Prepare Cash Stage-2 Quarter Wave, then review all 25 compact fixtures before any promotion.

## Completion

Final commit: e5193d275d1c579d50ea9961b4d2a038c77013f9
CI run: 37728864055 (all five required jobs successful); Historical Backtest Smoke 37728864033 successful
Remaining unassessed items: post-merge q1/q2 preparation runs and prepared-fixture review before promotion
