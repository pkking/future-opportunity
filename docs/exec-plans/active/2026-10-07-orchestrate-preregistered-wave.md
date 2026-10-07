# 2026-10-07-orchestrate-preregistered-wave: End-to-end pre-registered evidence orchestration

Issue: #15
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Turn the existing pre-registered historical evidence stages into one top-level GitHub Actions workflow so operators provide study/business facts once and do not manually copy intermediate workflow run IDs or artifact names.

Target flow:

```text
Funding sampling ───────────────────────────────┐
                                                ├─> pre-registered acquisition -> compact artifacts
Cash sampling -> sampled discovery -> case plan ┘
                                                -> campaign planner (after run completes)
```

## Non-goals

- No automatic study-window, seed, future, expiry, exit or entry-time choice.
- No selection based on strategy outcomes/returns.
- No corpus mutation, review-branch push, PR creation or merge.
- No Stage-2 threshold design/activation.
- No rewrite of existing sampling/discovery/planning/acquisition business logic.

## Current facts

- Main historical corpus is Funding=8 / Cash=5.
- Wave 001 has no unpinned candidates; planner run 37575896276 reports selected_count=0.
- Existing workflows already implement all evidence stages but most are workflow_dispatch-only.
- Existing downstream verifiers require source runs to be completed/successful, which is correct for external run IDs but prevents safe same-run chaining through reusable workflows.
- Reusable acquisition/composer workflows already exist and retain read-only/preparation-only authority.

## Design

1. Add `workflow_call` to the existing sampling, sampled Cash discovery, Cash case planning and pre-registered acquisition workflows.
2. Sampling accepts an optional explicit artifact name so Funding and Cash samples can coexist in one run without collisions.
3. Introduce a bounded same-run evidence rule:
   - external source run ID: must remain `completed/success`;
   - source run ID equal to `GITHUB_RUN_ID`: may be `in_progress`, but the consumer must be downstream through `needs` and must still resolve exactly one expected artifact with valid ID/digest/not-expired evidence.
4. Add `Prepare Pre-registered Historical Wave` top-level workflow:
   - two deterministic sampling jobs;
   - sampled Cash discovery;
   - explicit Cash case planning;
   - existing pre-registered acquisition workflow;
   - no intermediate run/artifact IDs exposed to the operator.
5. Extend campaign planner workflow_run trigger to the top-level workflow so planning begins only after the whole run completes successfully.

## Constraints and invariants

- Operator facts remain explicit: strategy windows, sample sizes, seeds/policy and Cash future/expiry/exit/entry time.
- Same-run relaxation is allowed only for exact current `GITHUB_RUN_ID`; arbitrary external in-progress runs fail closed.
- Artifact identity checks remain exact and digest-backed.
- Funding/Cash sampling artifacts must have distinct names in the same run.
- Existing standalone workflow_dispatch inputs and first-wave defaults remain compatible.
- All workflows remain read-only or preparation-only; no corpus/PR/merge write authority.
- Acquisition remains capped at 31 total prepared items.

## Acceptance criteria

- [x] Sampling supports workflow_call and caller-supplied unique artifact names.
- [x] Sampled Cash discovery supports workflow_call.
- [x] Cash case planning supports workflow_call.
- [x] Pre-registered acquisition supports workflow_call.
- [x] Same-run source validation is explicit and limited to GITHUB_RUN_ID.
- [x] External source runs still require completed/success.
- [x] Top-level workflow accepts no intermediate run/artifact ID inputs.
- [x] Top-level Funding and Cash sample artifact names are deterministic and distinct.
- [x] Cash discovery consumes only the current-run Cash sample artifact.
- [x] Cash planner consumes current-run discovery evidence only after discovery succeeds.
- [x] Acquisition consumes current-run Funding sample + Cash case-plan evidence only after both succeed.
- [x] Campaign planner follows successful top-level orchestration.
- [x] Existing standalone dispatch behavior remains compatible.
- [x] Workflow permissions remain read-only/preparation-only.
- [x] Contract tests cover orchestration, same-run bounds and no-write invariants.
- [ ] Full CI/Ruleset checks pass.

## Implementation slices

- [x] 1. Reconcile current workflows and identify same-run completion-state constraint.
- [x] 2. Add reusable contracts and same-run bounded source validation.
- [x] 3. Add top-level orchestration workflow.
- [x] 4. Extend campaign planner trigger and workflow contract tests.
- [x] 5. Update README/testing contract.
- [ ] 6. Execute push self-test, verify PR/full CI, merge and archive.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR required check | pending |
| Workflow contracts | focused tests | pending |
| Orchestrator self-test | push Actions run | pending |
| Static | CI | pending |
| Code | CI | pending |
| API | CI | pending |
| E2E | CI | pending |

## Decision gates

None for orchestration. Cash future/expiry/exit and study design remain explicit operator decisions.

## Evidence log

- 2026-10-07: #12 closed after completion-only PR #14 and main CI 37581731501 succeeded.
- 2026-10-07: latest planner 37575896276 confirms wave 001 is fully absorbed: Funding=8, Cash=5, selected_count=0.
- 2026-10-07: code review found current-run orchestration cannot reuse the existing external-run `completed/success` assertion unchanged because reusable jobs share a still-in-progress caller run.
- 2026-10-07: added reusable contracts to sampling, sampled Cash discovery, Cash case planning and pre-registered acquisition; composer/discovery/planner retain strict external-run completion checks with an exact-current-run in-progress exception.
- 2026-10-07: added top-level `Prepare Pre-registered Historical Wave`, deterministic per-strategy sample artifact names, planner workflow_run trigger, focused contract tests and README/testing guidance.

## Deviations and discoveries

- Initial orchestrator push run 37582144426 exposed that reusable workflows inherit the caller event name. Both sampling calls therefore ran the old direct-push Cash self-test and produced duplicate Cash sample artifact names. Sampling self-test is now limited to direct push with empty reusable strategy input.
- Second orchestrator self-test 37582340866 has successfully completed distinct Funding/Cash sampling, exact same-run Cash sample verification/discovery, and same-run Cash case planning; acquisition composition is in progress.

## Resume from here

Monitor orchestrator self-test 37582340866 through acquisition and planner handoff, then open PR #15 work, verify focused/full CI, merge and archive.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: pending
