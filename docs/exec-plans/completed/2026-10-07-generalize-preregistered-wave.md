# 2026-10-07-generalize-preregistered-wave: Generalize pre-registered acquisition waves

Issue: #12
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Remove the first-wave-only 5 Funding + 3 Cash verification assumption from the reusable pre-registered acquisition workflow so subsequent pre-registered waves can reuse the same evidence pipeline without editing workflow source.

## Non-goals

- No sampling-policy change.
- No Stage-2 activation or threshold change.
- No automatic corpus promotion, PR creation, or merge.
- No change to exchange/strategy economics.

## Current facts

- Main historical corpus is Funding=8 / Cash=5.
- ADR-0007 requires at least 30 distinct pinned days per strategy before Stage-2 design is eligible.
- The reusable pre-registered acquisition workflow now derives expected Funding/Cash/total counts from canonical `acquisition.json`.
- First-wave 5+3 inputs remain regression defaults only.
- Main CI and the final main-branch acquisition self-test are green.
- Planner run 37575896276 finds no remaining unpinned candidate from wave 001.

## Constraints and invariants

- Selection provenance comes from exact verified source artifacts.
- The wave remains corpus read-only and cannot push branches or create PRs.
- Artifact names remain unique.
- Compact artifact count must exactly match the composed acquisition manifest.
- Total acquisition items remain bounded to 31.
- Zero-item strategy sides are valid only when the other side is non-empty.

## Acceptance criteria

- [x] Wave summary derives expected Funding/Cash counts from composed acquisition JSON.
- [x] No reusable verification logic hard-codes 5/3/8.
- [x] Compact total equals expected Funding + expected Cash.
- [x] Unique compact name count equals compact total.
- [x] Per-strategy artifact counts exactly equal derived expected counts.
- [x] Zero-item Funding or Cash side is handled safely.
- [x] Selection provenance remains required for every non-empty strategy side.
- [x] Existing first-wave default inputs remain unchanged.
- [x] Workflow remains actions:read + contents:read only.
- [x] Contract tests cover dynamic counts and reject hard-coded assumptions.
- [x] README/testing guidance describes reusable wave semantics.
- [x] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Inspect current workflow/tests and identify hard-coded count boundary.
- [x] 2. Generalize wave summary and identity verification.
- [x] 3. Update workflow contract tests.
- [x] 4. Update user/agent documentation.
- [x] 5. Merge PR, verify main, and archive through the normal completion lifecycle.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR #13 CI 37574759832 | passed |
| Workflow contract | Code-level tests in 37574759832 | passed |
| Static | 37574759832 | passed |
| Code | 37574759832 | passed |
| API | 37574759832 | passed |
| E2E | 37574759832 | passed |
| Historical smoke | 37574759685 | passed |
| Real 5+3 workflow self-test | 37573580430 | passed |
| Main CI | 37574824941 | passed |
| Main final workflow self-test | 37574825594 | passed |
| Planner reconciliation | 37575896276 | passed; selected_count=0 |

## Decision gates

None. This removes an implementation-specific first-wave constraint while preserving the accepted evidence and safety boundaries.

## Evidence log

- 2026-10-07: reusable workflow originally duplicated 5/3/8 as verification constants.
- 2026-10-07: generalized summary now derives Funding/Cash/total counts from canonical acquisition JSON and uses those same values for artifact identity checks.
- 2026-10-07: focused tests reject static 5/3/8 verification assumptions and preserve read-only/provenance contracts.
- 2026-10-07: PR #13 final CI 37574759832 and Historical Smoke 37574759685 passed.
- 2026-10-07: PR #13 merged as fe12f3041f66ca54aa35e537c2664c633e8a627a.
- 2026-10-07: main CI 37574824941 passed.
- 2026-10-07: main workflow self-test 37574825594 passed end to end against the original 5 Funding + 3 Cash evidence.
- 2026-10-07: planner 37575896276 reports pinned Funding=8 / Cash=5, selected_count=0, excluded_pinned_count=8, so wave 001 has no remaining promotion work.

## Deviations and discoveries

- Funding preparation is materially slower than Cash because each Funding day downloads roughly hundreds of MB of official L2 archives; the monthly Funding-rate archive itself is tiny, so caching that monthly file is not the dominant optimization target.
- The next corpus-growth bottleneck is producing a new pre-registered sample/case-plan evidence wave, not replaying or promoting wave 001.

## Resume from here

Completed. Start the next corpus-growth task from a new pre-registered sample. Prefer orchestration that composes existing sampling, sampled-Cash discovery, Cash case planning, acquisition preparation and campaign planning without changing their evidence boundaries.

## Completion

Final commit: fe12f3041f66ca54aa35e537c2664c633e8a627a
CI run: https://github.com/pkking/future-opportunity/actions/runs/37574824941
E2E artifact: PR #13 CI 37574759832 plus real acquisition self-tests 37573580430 and 37574825594
Remaining unassessed items: Stage-2 threshold design remains intentionally deferred until corpus eligibility and separate approval
