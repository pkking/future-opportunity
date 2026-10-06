# 2026-10-06-pre-registered-acquisition-wave: Acquire first pre-registered historical corpus candidates

Status: PLANNING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Turn the already-reviewed deterministic sampling evidence into the first batch of
real compact historical candidates that are explicitly attributable to
pre-registration.

Reuse the existing verified pipeline rather than duplicating it:

```text
exact Funding sampling artifact
+
exact sampled Cash case-plan artifact
  -> reusable read-only acquisition composer
  -> normalized acquisition JSON with both selection provenances
  -> reusable acquisition campaign
  -> per-day full + commit-ready compact artifacts
```

No artifact is pinned automatically. Promotion/corpus review remains a separate
explicit step.

## Reviewed inputs for the first wave

Funding:
- source sampling run: 37482498880
- artifact: historical-market-day-sample-37482498880
- artifact ID: 11421537670
- selected dates: 2026-01-01, 01-08, 01-13, 01-22, 01-29

Cash:
- sampling run: 37487331716
- sampling artifact: cash-historical-market-day-sample-37487331716
- sampled discovery run: 37488688098
- sampled case-plan run: 37490008931
- case-plan artifact: cash-acquisition-case-plan-37490008931
- artifact ID: 11425760361
- selected dates: 2026-06-02, 06-04, 06-08
- selected_count=3, excluded_count=0
- future: BTC-USDT-260626
- exit: 2026-06-25T00:15:00Z
- expiry: 2026-06-26T08:00:00Z

## Non-goals

- Do not pin or promote automatically.
- Do not alter ADR-0007 readiness semantics.
- Do not change sampling dates after observing market outcomes.
- Do not replace failed/unavailable sampled days.
- Do not add another acquisition/composition implementation.
- Do not enable live trading.

## Constraints and invariants

- Composer and acquisition workflows remain corpus read-only.
- Exact source workflow/artifact identity is verified before composition.
- Both Funding and Cash selection provenance must survive into acquisition JSON.
- Reusable acquisition must pass strategy-specific provenance unchanged to each
  preparation job.
- A preparation failure remains a failed sampled day; it must not cause a
  replacement date.
- Full and compact manifests independently validate strategy/date membership.
- Maximum existing 31-item acquisition bound remains in force.
- Every successful compact artifact remains prepared_unpinned/commit_ready
  evidence only until explicit promotion.
- Legacy pinned corpus remains untouched during this plan.

## Acceptance criteria

- [ ] Acquisition composer is reusable and exposes normalized acquisition JSON.
- [ ] Acquisition campaign is reusable and accepts normalized acquisition JSON.
- [ ] Existing workflow_dispatch/push behavior remains backward compatible.
- [ ] Add thin pre-registered-wave workflow using exact reviewed artifacts.
- [ ] Wave composition contains Funding and Cash selection provenance.
- [ ] Funding preparation matrix contains exactly the five reviewed dates.
- [ ] Cash preparation matrix contains exactly the three reviewed cases.
- [ ] No unsampled replacement date appears.
- [ ] Successful full/compact artifacts retain selection provenance.
- [ ] Failed sampled dates, if any, remain explicit failures and are not replaced.
- [ ] Acquisition summary proves corpus was not mutated.
- [ ] Workflow/contract tests lock reusable composition and acquisition behavior.
- [ ] Final CI green.
- [ ] Document first-wave evidence and next promotion step.

## Implementation slices

- [ ] 1. Make composer reusable with acquisition_json output.
- [ ] 2. Make acquisition campaign reusable with acquisition_json input.
- [ ] 3. Add pre-registered acquisition-wave orchestration.
- [ ] 4. Add workflow-contract tests.
- [ ] 5. Execute first 5+3 sampled wave and inspect artifacts.
- [ ] 6. Record failures/exclusions without replacement.
- [ ] 7. Document/verify/archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | workflow/architecture safety | pending |
| Code | composer/acquisition contract tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged | pending |
| Historical smoke | committed legacy corpus unchanged | pending |
| Wave | exact 5 Funding + 3 Cash sampled preparations | pending |

## Decision gates

None. Inputs were pre-registered before market outcomes and the workflow is
read-only with respect to the corpus.

A later decision is still required for Stage-2 threshold activation and for
human review/merge of promotion PRs.

## Evidence log

- 2026-10-06: selection-provenance implementation completed; final CI
  37490819625 passed.
- 2026-10-06: sampled Cash discovery 37488688098, case plan 37490008931 and
  mixed acquisition composer 37490187894 succeeded.

## Resume from here

Add `workflow_call` contracts and outputs to the existing composer and
acquisition workflows. Then create a thin orchestration workflow that feeds the
reviewed artifacts above through those reusable workflows.

## Completion

Final implementation commit:
Final CI:
Wave run:
Successful sampled artifacts:
Failed/unavailable sampled dates:
Remaining unassessed items:
