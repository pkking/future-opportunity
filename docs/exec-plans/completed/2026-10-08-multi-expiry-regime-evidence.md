# 2026-10-08-multi-expiry-regime-evidence

Issue: #65
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Define reproducible, outcome-blind historical expansion planning for Cash additional expiry cohorts and Funding ex-ante market regimes. Preserve ADR-0009 decision-quality policy and do not promote or alter any existing historical cases.

## Baseline

- Main: 9a3261edf14ef97145944f3d283eb8904d5ecda3.
- Cash: 30 pinned days across March/June 2026 expiries; 8 qualified cases share two expiry cohorts.
- Funding: 32 pinned days; zero qualified cases.
- Both strategies approved for Stage-2 decision-quality observability; economics gate disabled.
- Current Cash archival source availability is verified only through June 26, 2026. Other expiry cohorts are not yet verified.
- Existing Funding systematic-stratified sampler is date-stratified, not genuine ex-ante market-regime stratification.

## Invariants

- Select on data availability and ex-ante features only; never on qualified/realized-return outcome.
- Freeze regime thresholds/eligibility before outcome inspection.
- No replacement if a selected source is missing or fails normalization.
- Never treat missing source data as zero-opportunity evidence.
- Cash quarter-aligned expiry/exit policy unchanged unless new explicit approval is obtained.
- No acquisition, promotion, Stage-2 threshold or historical gate changes.

## Acceptance criteria

- [x] Document source feasibility gaps for non-March/June Cash expiries and a verification protocol.
- [x] Implement deterministic pure cohort/date selection with no replacement and explicit unavailable outcomes.
- [x] Implement deterministic pure ex-ante regime-balanced date selection with predefined regime labels and no economic outcomes.
- [x] Reject duplicate dates, unknown regimes, bad availability and insufficient capacity safely.
- [x] Test reproducibility, no-replacement, missing-data denominators and cohort constraints.
- [x] Provide executable next-stage handoff with source verification and publication frontier prerequisites.
- [x] PR #66 linked to Issue #65; review-head CI 37760956472 5/5 success and Smoke 37760956477 success.
- [x] Archive the plan and require fresh final-head CI/Smoke before merge; Issue remains open until main verification.

## Implementation slices

- [x] 1. Read baseline sampling, Cash quarter policy and governance.
- [x] 2. Create Issue #65 and governed branch/plan.
- [x] 3. Implement pure cohort/regime selection and tests.
- [x] 4. Document source evidence and dispatch/approval boundaries.
- [x] 5. Verify review-head CI/Smoke and archive; final-head revalidation and squash merge are required after archive.

## Verification matrix

| Gate | Expected |
|---|---|
| Cash existing expiries | 2026-03-27 and 2026-06-26 |
| Cash new expiry source coverage | unassessed until verified |
| Funding regime indicators | pre-registered, point-in-time only |
| Outcome-dependent selection | forbidden |
| Replacement policy | none |
| Corpus mutation | none |
| Economic gate | disabled |
| CI/Smoke | Review CI 37760956472: 5/5 success; Historical Smoke 37760956477: success |

## Resume from here

Implement pure selection helper and tests, document the prerequisite of verifying official historical archives in new expiry cohorts before any acquisition. Never claim calendar cohort identity proves data availability. PR #66 review-head CI (37760956472) and Historical Smoke (37760956477) passed. Update PR Plan to the completed path, delete active plan and verify 5/5 final-head CI and Historical Smoke. Squash merge exact head SHA; verify main has the new source-feasibility protocol and pure selection code, no corpus changes and economics gate disabled. Close Issue #65 only after that verification.

## Completion

Final commit: b8c489e68cdea78943893f417851bd3f3b65589d
CI run: 37760956472 (5/5 success); Historical Smoke 37760956477 (success)
Remaining unassessed items: final-head validation, merge and main verification; additional Cash expiry data source eligibility remains unassessed.
