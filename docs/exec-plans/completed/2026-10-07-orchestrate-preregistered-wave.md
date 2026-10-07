# 2026-10-07-orchestrate-preregistered-wave: End-to-end pre-registered evidence orchestration

Issue: #15
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Provide one top-level GitHub Actions workflow that chains deterministic Funding/Cash sampling, sampled Cash discovery, explicit Cash case planning, pre-registered acquisition preparation, and post-run campaign planning without exposing intermediate workflow run IDs or artifact names to the operator.

## Non-goals

- No automatic study-window, seed, future, expiry, exit or entry-time choice.
- No outcome-dependent sampling or reselection.
- No corpus mutation, review-branch push, PR creation or merge.
- No Stage-2 threshold design or activation.

## Current facts

- Main corpus remains Funding=8 / Cash=5.
- Top-level workflow `Prepare Pre-registered Historical Wave` is merged on main.
- Main CI, main top-level 1+1 orchestration self-test, and automatic post-run planner handoff all succeeded.
- The orchestrator exposes study/business facts only; intermediate run/artifact identities are deterministic current-run facts.
- External source runs retain strict `completed/success` validation.
- Same-run evidence is accepted only for the exact current `GITHUB_RUN_ID` after upstream `needs` completes, while exact artifact identity/digest/expiry checks remain mandatory.

## Constraints and invariants

- Funding/Cash study windows, sample sizes, seeds/policy, and Cash future/expiry/exit/entry time remain explicit operator facts.
- Funding and Cash sample artifacts are uniquely named within one run.
- Same-run source relaxation is limited to exact current run identity.
- Arbitrary external in-progress runs fail closed.
- Acquisition remains capped at 31 prepared items.
- All participating workflows retain read-only or preparation-only authority.

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
- [x] Full CI/Ruleset checks pass.

## Implementation slices

- [x] 1. Reconcile current workflows and identify same-run completion-state constraint.
- [x] 2. Add reusable contracts and same-run bounded source validation.
- [x] 3. Add top-level orchestration workflow.
- [x] 4. Extend campaign planner trigger and workflow contract tests.
- [x] 5. Update README/testing contract.
- [x] 6. Execute push self-test, verify PR/full CI, merge, verify main orchestration/planner handoff and archive.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR #16 CI 37582866583 | passed |
| Workflow contracts | Code-level tests in 37582866583 | passed |
| Feature-branch orchestration | 37582340866 | passed |
| Historical smoke | 37582866611 | passed |
| Main CI | 37582933779 | passed |
| Main orchestration | 37582934645 | passed |
| Automatic planner handoff | 37583345457 | passed |
| Planner source identity | log: Source run 37582934645 | passed |

## Decision gates

None for orchestration. Actual second-wave study windows, seeds, sample sizes and Cash future/expiry/exit facts remain a separate explicit study-design decision.

## Evidence log

- 2026-10-07: initial orchestration run 37582144426 exposed that reusable workflows inherit caller event context, causing both called sampling workflows to run the legacy direct-push Cash self-test and create duplicate Cash sample artifacts.
- 2026-10-07: direct sampling self-test was bounded to push with empty reusable strategy input; later reusable calls skipped it.
- 2026-10-07: feature-branch orchestration run 37582340866 succeeded end to end. It produced distinct Funding/Cash samples, sampled Cash discovery/control, Cash case-plan evidence, Funding/Cash compact artifacts and final wave-boundary evidence.
- 2026-10-07: PR #16 final CI 37582866583 and Historical Smoke 37582866611 passed.
- 2026-10-07: PR #16 merged as f079d324d8d114c4a8a0375f76e071dcb357960c.
- 2026-10-07: main CI 37582933779 passed.
- 2026-10-07: main top-level orchestration run 37582934645 passed all stages.
- 2026-10-07: workflow_run planner 37583345457 succeeded and explicitly logged Source run: 37582934645, Funding artifacts expected: 1, Cash artifacts expected: 1.

## Deviations and discoveries

- Reusable workflows preserve caller event context, so direct-push-only self-tests must not be gated solely by `github.event_name == 'push'`.
- Same-run artifact consumption is practical and auditable when limited to exact current-run identity plus `needs` ordering and exact artifact metadata verification.
- The main post-merge commit also launched lower-level push self-tests because several workflow files changed. This is redundant validation/cost but does not affect correctness; it is a separate optimization concern.

## Resume from here

Completed. The next corpus-growth action is an explicit second-wave study design: choose Funding/Cash study windows, sample sizes and seeds, plus Cash future/expiry/exit/entry facts, then dispatch `Prepare Pre-registered Historical Wave`.

## Completion

Final commit: f079d324d8d114c4a8a0375f76e071dcb357960c
CI run: https://github.com/pkking/future-opportunity/actions/runs/37582933779
E2E artifact: orchestrator run 37582934645 and planner handoff run 37583345457
Remaining unassessed items: second-wave study-design parameters and Stage-2 threshold design remain intentionally unassessed
