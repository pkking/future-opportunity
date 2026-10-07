# 2026-10-06-pre-registered-acquisition-wave: Acquire first pre-registered historical corpus candidates

Status: COMPLETED
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-07

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

- [x] Acquisition composer is reusable and exposes normalized acquisition JSON.
- [x] Acquisition campaign is reusable and accepts normalized acquisition JSON.
- [x] Existing workflow_dispatch/push behavior remains backward compatible.
- [x] Add thin pre-registered-wave workflow using exact reviewed artifacts.
- [x] Wave composition contains Funding and Cash selection provenance.
- [x] Funding preparation matrix contains exactly the five reviewed dates.
- [x] Cash preparation matrix contains exactly the three reviewed cases.
- [x] No unsampled replacement date appears.
- [x] Successful full/compact artifacts retain selection provenance.
- [x] Failed sampled dates, if any, remain explicit failures and are not replaced.
- [x] Acquisition summary proves corpus was not mutated.
- [x] Workflow/contract tests lock reusable composition and acquisition behavior.
- [x] Final CI green.
- [x] Document final wave evidence, review PR, and next promotion step.

## Implementation slices

- [x] 1. Make composer reusable with acquisition_json output.
- [x] 2. Make acquisition campaign reusable with acquisition_json input.
- [x] 3. Add pre-registered acquisition-wave orchestration.
- [x] 4. Add workflow-contract tests.
- [x] 5. Execute first 5+3 sampled wave and inspect artifacts.
- [x] 6. Record failures/exclusions without replacement.
- [x] 7. Document/verify/archive.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | workflow/architecture safety | PR #4 CI 37558106807 passed |
| Code | composer/acquisition/distribution tests | PR #4 CI 37558106807 passed (after mixed-provenance assertion correction) |
| API | no regression | PR #4 CI 37558106807 passed |
| Reference E2E | unchanged business targets | PR #4 CI 37558106807 passed |
| Historical smoke | indexed corpus provenance and replay | PR #4 run 37558106798 passed |
| Wave | exact 5 Funding + 3 Cash sampled preparations | acquisition 37551952412 passed (8 of 8, no replacements) |
| Main documentation | full CI after README update | run 37558182454 passed |

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
- 2026-10-06: composer and acquisition campaign now expose reusable
  `workflow_call` contracts. Composer returns canonical normalized
  `acquisition_json`; acquisition accepts the same versioned JSON while
  retaining original manual dispatch and push self-tests.
- 2026-10-06: first pre-registered wave run 37491514724 started successfully.
  The composed acquisition is exactly Funding
  [2026-01-01, 01-08, 01-13, 01-22, 01-29] plus Cash
  [2026-06-02, 06-04, 06-08], and includes both canonical selection-provenance
  records. Acquisition resolver completed successfully and launched the
  strategy preparation matrices under existing concurrency bounds.
- 2026-10-06: main CI runs 37491396261, 37491402987 and 37491513856 verified
  the reusable workflow changes and orchestration definition before the
  long-running market-data preparation phase.
- 2026-10-07: first wave run 37491514724 completed successfully with all five
  Funding and all three Cash preparations green. No sampled date failed, so
  there was no replacement or post-outcome reselection.
- 2026-10-07: inspected commit-ready compact artifacts from run 37491514724.
  Funding 2026-01-01 and all three Cash compact manifests retain the exact
  pre-registered sampling provenance, including source sampling run/artifact,
  policy version, seed, population, requested sample size, and the complete
  originally selected date set.
- 2026-10-07: the first run exposed one orchestration defect unrelated to market
  data: all three Cash compact artifacts used the same artifact name because the
  reusable Cash workflow name omitted entry_market_date. Artifact IDs/digests
  and manifest dataset IDs were distinct, but run-level name selection was
  ambiguous. The Cash workflow was fixed to include entry_market_date in full,
  compact, and actuals artifact names.
- 2026-10-07: pre-registered wave now fails closed unless the parent run contains
  exactly eight compact artifacts with eight unique names (5 Funding, 3 Cash).
  Workflow-contract tests lock this identity rule.
- 2026-10-07: corrected pre-registered 5+3 acquisition run 37551952412
  completed successfully. All five Funding and all three Cash preparation jobs
  passed; 8 compact artifacts have distinct names. No failed or substituted
  sampled date.
- 2026-10-07: read-only planner run 37553559617 passed using the exact
  acquisition run. It selected 7 corpus promotion candidates (5 Funding +
  2 Cash); Cash 2026-06-02 was excluded as already pinned. Projection if
  reviewed/merged is Funding 7 days and Cash 4 days. The current pinned
  corpus is unchanged at 2+2 days.
- 2026-10-07: explicit planned-wave promotion run 37553856198 successfully
  verified all artifact identities, staged the seven compact fixtures atomically,
  and passed offline replay. It failed only while pushing the review branch:
  its triggering commit c49bb74 modified a protected GitHub Actions workflow,
  and GitHub App credentials lacked workflow-file write permission.
  The corpus commit object c9b70b8719bd242e9f64d5d9e01fbecdbeca2a34
  remains readable in GitHub; it changes only the corpus index and seven compact
  fixture directories. Main subsequently restored the workflow to
  explicit-dispatch-only, and CI 37553888389 passed.
- 2026-10-07: recovered the verified corpus subtree onto main without carrying
  the temporary workflow change. Recovered commit
  f15f3e322f855bb0a324269ccd289eca05d571eb has exactly 36 changed corpus
  files (35 additions across 7 fixtures plus 1 corpus-index update), zero
  paths outside tests/fixtures/historical. Opened review-only PR #4:
  https://github.com/pkking/future-opportunity/pull/4.
- 2026-10-07: PR #4 Historical Backtest Smoke run 37557962463 passed. Static,
  API, and E2E gates in initial PR CI 37557962485 passed, but Code-level failed
  at tests/test_historical_distribution_report.py:165 because the old baseline
  asserted zero pre-registered samples; the new wave correctly reports seven.
- 2026-10-07: updated the PR-only test to derive expected classification,
  aggregate coverage, per-strategy counts, and source-presence semantics from
  independently indexed fixture manifests, without altering strategy logic or
  return thresholds. PR #4 head 729b24ba90195a3c5b3e84e5abe051509ca715df
  passed all four CI gates in 37558106807 and Historical Smoke in 37558106798.
- 2026-10-07: README now records the immutable first-wave selected dates,
  acquisition and planner source IDs, the seven candidate promotion proposal,
  and the Stage-1 reporting-only boundary. Main documentation CI 37558182454
  passed all gates. GitHub PR #4 remained open and clean; no merge was performed.


## Resume from here

Completed and archived. Review-only PR #4 proposes seven pre-registered compact
fixtures. It has clean mergeability and passing CI/Historical Smoke but remains
unmerged pending human review. Once merged, validated corpus readiness increases
from Funding 2 / Cash 2 to Funding 7 / Cash 4. Do not treat this projection as
already pinned. ADR-0007 Stage 2 remains disabled and requires a separately
approved decision.

## Completion

Final acquisition run: https://github.com/pkking/future-opportunity/actions/runs/37551952412
Planner run: https://github.com/pkking/future-opportunity/actions/runs/37553559617
Original promotion verification: https://github.com/pkking/future-opportunity/actions/runs/37553856198
Review PR: https://github.com/pkking/future-opportunity/pull/4
PR head: 729b24ba90195a3c5b3e84e5abe051509ca715df
PR CI: https://github.com/pkking/future-opportunity/actions/runs/37558106807 (passed)
PR Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/37558106798 (passed)
Main README CI: https://github.com/pkking/future-opportunity/actions/runs/37558182454 (passed)
Successful sampled artifacts: 5 Funding + 3 Cash, eight unique compact artifacts
Candidate promotion: 5 Funding + 2 Cash; Cash 2026-06-02 excluded because already pinned
Failed/unavailable sampled dates: none
Current pinned days (no merge yet): Funding 2 / Cash 2
Projected after human-approved PR merge: Funding 7 / Cash 4
Remaining unassessed items: Stage-2 distribution return thresholds; human PR review/merge intentionally outside this plan.
