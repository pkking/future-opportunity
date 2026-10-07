# 2026-10-07-preregistered-wave-003-execution: Execute approved Stage-2 evidence Wave 003

Issue: #24
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Execute the operator-approved Wave 003 study from Issue #18 Option A after Wave 002 reconciliation, without changing the pre-registered design in response to Wave 002 outcomes.

Approved immutable inputs:

- acquisition_id: `preregistered-wave-003`
- planner_campaign_prefix: `preregistered-review-003`
- policy_version: `systematic-stratified-sha256-v1`
- Funding window: `2026-05-01 .. 2026-08-31`
- Funding sample_size: `12`
- Funding seed: `stage2-funding-wave-003-v1`
- Cash window: `2026-08-01 .. 2026-09-23`
- Cash sample_size: `14`
- Cash seed: `stage2-cash-wave-003-v1`
- Cash future_id: `BTC-USDT-260925`
- Cash expiry_at: `2026-09-25T08:00:00+00:00`
- Cash exit_at: `2026-09-24T00:15:00+00:00`
- Cash entry_time_utc: `00:15:00`

Maximum requested preparation items if no Cash exclusions: 26.

## Current facts

- Issue #18 approved Option A for both Wave 002 and Wave 003.
- Wave 002 source run 37593545181 succeeded and is archived by PR #23.
- Wave 002 produced 12 Funding compacts and 0 Cash compacts; all 14 Cash dates were explicit `no_unique_future_chain_archive` exclusions without replacement.
- Current committed pinned corpus remains Funding=8 / Cash=5; Wave 002 artifacts are review-only and are not automatically promoted.
- Connected GitHub capability cannot invoke workflow_dispatch, so this wave uses a disposable non-main branch and exact push fallbacks.
- Execution-only workflow changes must never merge to main.

## Constraints

- Do not change approved windows, sample sizes, seeds, policy, future, expiry, exit, or entry facts.
- Do not replace source-data exclusions.
- Do not select based on return, qualification, basis, funding rate, or any observed outcome.
- Keep acquisition <=31 total items.
- Record Actions IDs/digests for successful evidence.
- Planner reconciliation is read-only against the current main corpus.

## Acceptance criteria

- [x] Approved Wave 003 parameters are versioned before acquisition starts.
- [x] Funding sample contains exactly 12 deterministic selected dates.
- [x] Cash sample contains exactly 14 deterministic selected dates.
- [x] Cash discovery/case plan preserves approved business facts and records exclusions without replacement.
- [x] Acquisition composition preserves Funding and Cash selection provenance.
- [x] Requested acquisition size is <=26 and <=31.
- [x] Successful compact artifacts have Actions IDs/digests.
- [x] Final wave-boundary verification succeeds, or failures/exclusions are recorded without reselection.
- [x] Automatic campaign planner reconciles the successful source run against current main.
- [x] Execution-only branch remains unmerged.
- [x] Readiness impact is recorded, including any further Cash evidence required for ADR-0007 >=30-day minimum.

## Implementation slices

- [x] 1. Close Wave 002 task after completion PR #23.
- [x] 2. Create Issue #24 and this disposable execution branch/plan.
- [x] 3. Apply exact approved Wave 003 values only to push fallbacks in the top-level orchestration workflow.
- [x] 4. Observe deterministic samples and Cash exclusions before acquisition completes; all 14 Cash dates were explicit source-data exclusions with no replacement.
- [x] 5. Reconcile all compact artifacts, final wave boundary, and automatic planner output.
- [x] 6. Archive completed evidence via a main-based completion PR without merging this execution branch.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Approved study identity | Issue #18 Option A + Issue #24 + this plan | passed |
| Funding sample | run 37597427096; 12 deterministic dates with approved Wave 003 seed/window | passed |
| Cash sample | run 37597427096; 14 deterministic dates with approved Wave 003 seed/window | passed |
| Cash discovery/case plan | 14/14 discovery reports candidate_count=0 / no_unique_future_chain_archive; planner selected=0 excluded=14 | exclusion evidence recorded |
| Acquisition composition | source run 37597427096; 12 Funding + 0 Cash; exact selection provenance retained | passed |
| Compact preparation | 12/12 Funding compact artifacts with Actions IDs/digests; no failures | passed |
| Wave boundary | artifact 11472925140 / sha256:4754605e7a8e26328a29a2c7670d436fb7026816199695c434957560ab98cb68 | passed |
| Campaign planner | run 37600237687; artifact 11472665816 / sha256:8aa8e9b5b3e82a2226b8334f5fdccda870e201ff2b832582a5cc601742645850; selected=12 | passed |

## Decision gates

No study-design decision remains for Wave 003. Any missing source data is an exclusion, not a prompt to modify or replace the sample.

## Evidence log

- 2026-10-07: Wave 002 reconciliation completed; PR #23 merged and Issue #19 closed.
- 2026-10-07: Issue #24 opened for the already-approved Wave 003 execution.
- 2026-10-07: execution branch `study/preregistered-wave-003-execution` created from main cdf030c2efcc599080b8a059a9d034770875308e.
- 2026-10-07: exact Wave 003 push-fallback trigger committed as 8c2914b42c65d5f8201a02fa0f81b4be47616f49; source run 37597427096 started.
- 2026-10-07: Funding deterministic sample selected 12 dates: 2026-05-05, 05-16, 05-29, 06-02, 06-15, 06-23, 07-04, 07-12, 07-25, 08-08, 08-19, 08-29.
- 2026-10-07: Cash deterministic sample selected 14 dates: 2026-08-02, 08-04, 08-10, 08-12, 08-16, 08-21, 08-26, 08-28, 08-31, 09-06, 09-09, 09-14, 09-18, 09-20.
- Both sampling records explicitly use policy `systematic-stratified-sha256-v1`, the approved Wave 003 seeds/windows, and replacement_policy `none-v1`.
- 2026-10-07: all 14 Cash discovery jobs completed successfully as evidence-generation jobs, but every sampled date returned `candidate_count=0` and `status=no_unique_future_chain_archive`.
- 2026-10-07: Cash case planner preserved the approved `BTC-USDT-260925` / expiry `2026-09-25T08:00:00+00:00` / exit `2026-09-24T00:15:00+00:00` / entry `00:15:00` facts and produced selected_count=0 / excluded_count=14. No date was replaced.
- 2026-10-07: source run 37597427096 completed successfully. All 12 Funding dates produced compact artifacts with Actions IDs/digests; no preparation job failed.
- 2026-10-07: wave-boundary artifact `pre-registered-acquisition-wave-37597427096` is artifact 11472925140 with digest `sha256:4754605e7a8e26328a29a2c7670d436fb7026816199695c434957560ab98cb68`.
- 2026-10-07: automatic planner run 37600237687 completed successfully. It resolved source run 37597427096, Funding expected=12, Cash expected=0, planner prefix `preregistered-review-003`, selected_count=12, excluded_pinned_count=0, and generated `waves/preregistered-review-003-wave-001.json`.
- 2026-10-07: planner baseline is current main pinned corpus Funding=8/Cash=5 and projects Funding=20/Cash=5 if Wave 003 alone is promoted. Planner artifact 11472665816 digest is `sha256:8aa8e9b5b3e82a2226b8334f5fdccda870e201ff2b832582a5cc601742645850`.
- 2026-10-07: Wave 002 and Wave 003 Funding windows are non-overlapping and each contains 12 selected Funding days; if both review waves are independently approved/promoted, Funding can reach 32 distinct pinned days from the current 8-day baseline. Cash remains at 5 because both waves produced only source-data exclusions. Cash historical evidence acquisition is therefore the binding readiness problem.

## Resume from here

Wave 003 is complete and reconciled. Archive this completed plan through a main-based completion PR without merging the disposable execution branch. Then close Issue #24. Next work should treat the repeated Cash `no_unique_future_chain_archive` result as a historical-data acquisition/source-coverage problem, not as permission to change sampling or strategy targets.

## Completion

Final commit: 8c2914b42c65d5f8201a02fa0f81b4be47616f49
CI run: https://github.com/pkking/future-opportunity/actions/runs/37597427096
E2E artifact: Wave boundary artifact 11472925140 and planner artifact 11472665816
Source run: 37597427096 (success)
Wave artifact: 11472925140 / sha256:4754605e7a8e26328a29a2c7670d436fb7026816199695c434957560ab98cb68
Planner run: 37600237687 (success)
Planner artifact: 11472665816 / sha256:8aa8e9b5b3e82a2226b8334f5fdccda870e201ff2b832582a5cc601742645850
Remaining unassessed items: review/promotion of Wave 002 and Wave 003 Funding evidence; Cash historical source coverage needed to reach >=30 pinned Cash days; Stage-2 target design
