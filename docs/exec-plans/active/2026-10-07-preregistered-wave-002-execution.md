# 2026-10-07-preregistered-wave-002-execution: Execute approved Stage-2 evidence Wave 002

Issue: #19
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Execute the operator-approved Wave 002 study from Issue #18 without changing the approved study design after outcomes are observed.

Approved inputs:

- acquisition_id: `preregistered-wave-002`
- planner_campaign_prefix: `preregistered-review-002`
- policy_version: `systematic-stratified-sha256-v1`
- Funding window: `2026-02-01 .. 2026-04-30`
- Funding sample_size: `12`
- Funding seed: `stage2-funding-wave-002-v1`
- Cash window: `2026-07-01 .. 2026-07-31`
- Cash sample_size: `14`
- Cash seed: `stage2-cash-wave-002-v1`
- Cash future_id: `BTC-USDT-260925`
- Cash expiry_at: `2026-09-25T08:00:00+00:00`
- Cash exit_at: `2026-09-24T00:15:00+00:00`
- Cash entry_time_utc: `00:15:00`

Maximum requested preparation items if no Cash exclusions: 26.

## Non-goals

- No Wave 003 execution before Wave 002 is reconciled.
- No replacement of excluded/missing dates.
- No reselection based on qualification, return, basis, funding rate or any outcome.
- No automatic corpus merge or Stage-2 target design.
- No merge of execution-only fallback overrides to main.

## Current facts

- Decision Issue #18 approved Option A.
- Current pinned corpus is Funding=8 / Cash=5.
- Top-level orchestration and workflow_run campaign planning are verified on main.
- Connected GitHub capability cannot invoke workflow_dispatch.
- Therefore this execution uses a dedicated non-main branch and exact push-fallback values as an equivalent audited trigger.
- The execution branch must remain disposable and must not be merged.

## Constraints and invariants

- Exact approved parameters above are immutable for this wave.
- Sampling is deterministic and outcome-independent.
- Missing/disqualified source data remains an exclusion; no replacement sampling.
- Cash future/expiry/exit facts are explicit operator-approved business facts.
- Acquisition remains <=31 total items.
- All source and compact artifacts require Actions identity/digest evidence.
- Current main corpus remains authoritative pinned baseline for planner reconciliation.
- Execution-only workflow parameter overrides must not reach main.

## Acceptance criteria

- [x] Approved parameters are versioned before triggering acquisition.
- [x] Funding sample evidence contains exactly 12 deterministic selected dates.
- [x] Cash sample evidence contains exactly 14 deterministic selected dates.
- [x] Sampled Cash discovery preserves exact sample provenance.
- [x] Cash case plan uses BTC-USDT-260925 / approved expiry/exit/entry facts.
- [x] Acquisition composition preserves Funding + Cash selection provenance.
- [x] Requested acquisition size is <=26 and <=31 cap.
- [x] All successful compact artifacts have Actions IDs/digests for baseline attempt.
- [ ] Final wave-boundary verification succeeds, or failures/exclusions are recorded without reselection.
- [ ] Campaign planner reconciles source run against current main corpus.
- [ ] Execution-only branch is not merged to main.
- [ ] Wave 002 evidence is sufficient to decide whether to proceed unchanged to Wave 003.

## Implementation slices

- [x] 1. Record operator approval and create Issue #19.
- [x] 2. Create disposable Wave 002 execution branch and this immutable plan.
- [x] 3. Apply exact approved values only to push fallbacks on the execution branch.
- [x] 4. Observe deterministic sampling and Cash planning before long-running acquisition completes.
- [~] 5. Retry exact Funding sample under merged 1024 MiB cap; 11/12 Funding compacts are complete, with only 2026-04-20 still running; then reconcile final artifacts/planner.
- [ ] 6. Record evidence; restore/close disposable execution branch state without merging it.
- [ ] 7. Decide Wave 003 execution from evidence only, without changing Wave 002 sample.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Approved study identity | Issue #18 Option A + Issue #19 + this plan | passed |
| Funding sample | run 37591051064 artifact 11468786836; 12 dates | passed |
| Cash sample | run 37591051064 artifact 11468706304; 14 dates | passed |
| Cash discovery/case plan | 14 discovery jobs success; case planner selected=0 excluded=14 | exclusion evidence recorded |
| Acquisition manifest | run 37591051064 artifact 11468691763; 12 Funding + 0 Cash | passed |
| Compact preparation | retry run 37593545181: 11/12 Funding compact artifacts complete with Actions digests; 2026-04-20 still running; no retry failures observed | in progress |
| Wave boundary | pre-registered-acquisition-wave artifact | pending |
| Campaign planner | workflow_run planner evidence | pending |

## Decision gates

No further study-design decision is allowed inside Wave 002. Any source-data exclusion is recorded as-is. Wave 003 starts only after Wave 002 reconciliation.

## Evidence log

- 2026-10-07: operator selected Option A.
- 2026-10-07: Issue #18 updated with approval; Issue #19 opened for Wave 002 execution.
- 2026-10-07: execution branch `study/preregistered-wave-002-execution` created from current main.
- 2026-10-07: exact approved fallback values committed as 1284763cf23c6b8d4676b40f5dc080ae44fc0f5b; canonical source run 37591051064 started.
- 2026-10-07: Funding deterministic sample selected 12 dates: 2026-02-07, 02-14, 02-16, 02-23, 03-05, 03-10, 03-22, 03-28, 04-03, 04-08, 04-20, 04-27.
- 2026-10-07: Cash deterministic sample selected 14 dates: 2026-07-02, 07-03, 07-05, 07-07, 07-10, 07-12, 07-15, 07-17, 07-18, 07-21, 07-23, 07-25, 07-27, 07-31.
- 2026-10-07: all 14 Cash discovery jobs completed successfully as evidence-generation jobs, but each report had candidate_count=0/status=no_unique_future_chain_archive. Case planner retained the approved BTC-USDT-260925 template and excluded all 14 without replacement.

## Deviations and discoveries

- All 14 approved Cash dates returned discovery status `no_unique_future_chain_archive` with candidate_count=0. The case planner therefore produced selected_count=0 / excluded_count=14. Per pre-registration policy, no dates were replaced and the approved future/exit facts were not changed.
- Wave 002 acquisition continues with the 12 approved Funding dates only; Cash selection provenance remains embedded in acquisition evidence even though no Cash cases were eligible.
- Baseline source run 37591051064 completed with conclusion=failure solely because Funding 2026-02-07, 02-23, 03-05 and 03-10 exceeded the old 600 MiB raw cap. The other eight Funding dates succeeded and produced compact artifacts with Actions digests.
- Read-only catalog diagnostic 37591909278 measured max SWAP 800.48 MB; Issue #20/PR #21 raised the Funding cap to 1024 MiB and merged as d47c83abf48919a95859ae571a05398eee2303ff. Main CI and Funding self-tests passed.
- 2026-10-07: exact-study retry run 37593545181 started from execution commit c39f2d295c913d8b899904df8c69c39c11e0b0b0 with only the merged 1024 MiB cap change plus the same approved Wave 002 fallbacks. At checkpoint, 11/12 Funding compact artifacts exist with valid Actions digests; the four baseline cap failures now succeed. Only Funding 2026-04-20 remains in progress; no retry job has failed.

## Resume from here

Retry run 37593545181 is in progress with the exact approved sample. 11/12 Funding compact artifacts are complete and all four former 600 MiB cap failures now succeed; only 2026-04-20 remains running and there are no retry failures. Do not touch the workflow file or alter study inputs. Once run 37593545181 completes, verify all 12 compact artifact IDs/digests, the final wave-boundary job/artifact, then locate the automatic `Plan Historical Corpus Campaign` workflow_run execution and reconcile its read-only report against current main.

## Completion

Final commit: pending
CI run: not applicable to disposable execution branch
E2E artifact: pending Wave 002 source run and planner run
Remaining unassessed items: Wave 003 execution and Stage-2 target design
