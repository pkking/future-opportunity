# 2026-10-07-preregistered-wave-003-execution: Execute approved Stage-2 evidence Wave 003

Issue: #24
Status: IMPLEMENTING
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
- [ ] Cash discovery/case plan preserves approved business facts and records exclusions without replacement.
- [ ] Acquisition composition preserves Funding and Cash selection provenance.
- [ ] Requested acquisition size is <=26 and <=31.
- [ ] Successful compact artifacts have Actions IDs/digests.
- [ ] Final wave-boundary verification succeeds, or failures/exclusions are recorded without reselection.
- [ ] Automatic campaign planner reconciles the successful source run against current main.
- [ ] Execution-only branch remains unmerged.
- [ ] Readiness impact is recorded, including any further Cash evidence required for ADR-0007 >=30-day minimum.

## Implementation slices

- [x] 1. Close Wave 002 task after completion PR #23.
- [x] 2. Create Issue #24 and this disposable execution branch/plan.
- [x] 3. Apply exact approved Wave 003 values only to push fallbacks in the top-level orchestration workflow.
- [~] 4. Observe deterministic samples and Cash exclusions before acquisition completes; both samples are locked and Cash discovery is in progress.
- [ ] 5. Reconcile all compact artifacts, final wave boundary, and automatic planner output.
- [ ] 6. Archive completed evidence via a main-based completion PR without merging this execution branch.

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

## Resume from here

Source run 37597427096 is in progress. The exact 12 Funding and 14 Cash samples are locked above. Continue observing all 14 Cash discovery jobs, then record the case planner selected/excluded counts without replacement. After acquisition completes, verify compact artifact IDs/digests, wave boundary, and automatic planner output. Do not alter the workflow file or any approved study input.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: Wave 003 evidence and Stage-2 readiness
