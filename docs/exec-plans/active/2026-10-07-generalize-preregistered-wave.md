# 2026-10-07-generalize-preregistered-wave: Generalize pre-registered acquisition waves

Issue: #12
Status: IMPLEMENTING
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
- `acquire-pre-registered-historical-wave.yml` accepts arbitrary exact Funding sampling and Cash case-plan run/artifact inputs.
- Its summary still asserts exactly 5 Funding, 3 Cash, total 8 compact artifacts.
- That hard-coded verification makes a valid second wave with different counts fail.
- The underlying acquisition resolver already enforces a maximum total of 31 items.

## Constraints and invariants

- Selection provenance must come from exact verified source artifacts.
- The wave remains corpus read-only and cannot push branches or create PRs.
- Artifact names must remain unique.
- Derived compact artifact count must exactly match the composed acquisition manifest.
- First-wave defaults remain valid as backward-compatible self-test evidence.
- A strategy side with zero items must not cause grep exit semantics to create a false failure.

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
- [x] Contract tests cover dynamic counts and reject reintroduction of hard-coded assumptions.
- [x] README/testing guidance describes reusable wave semantics.
- [x] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Inspect current workflow/tests and identify hard-coded count boundary.
- [x] 2. Generalize wave summary and identity verification.
- [x] 3. Update workflow contract tests.
- [x] 4. Update user/agent documentation.
- [ ] 5. Merge PR after final evidence checkpoint; complete/close through normal lifecycle.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR CI 37573750547 | passed |
| Workflow contract | Code-level tests in PR CI 37573750547 | passed |
| Static | PR CI 37573750547 | passed |
| Code | PR CI 37573750547 | passed |
| API | PR CI 37573750547 | passed |
| E2E | PR CI 37573750547 | passed |

## Decision gates

None. This removes an implementation-specific first-wave constraint while preserving the existing accepted evidence and safety boundaries.

## Evidence log

- 2026-10-07: current workflow inputs are reusable, but summary asserts expected_funding_count=5, expected_cash_count=3 and total/unique/funding/cash artifact counts 8/8/5/3.
- 2026-10-07: latest read-only planner run 37572071278 reports pinned Funding=8 / Cash=5 and no remaining candidates from preregistered-wave-001, so the next acquisition must be a new pre-registered wave rather than replaying wave 001.
- 2026-10-07: generalized summary derives Funding/Cash/total counts from acquisition.json; artifact identity compares actual totals/unique/per-strategy counts against those derived values.
- 2026-10-07: focused workflow tests now explicitly reject reintroduction of static 5/3/8 verification assumptions; README/testing contract documents dynamic wave semantics.

## Deviations and discoveries

- Current push self-test of the generalized workflow is run 37573580430; it reuses the original 5+3 source artifacts as a regression case while exercising dynamic count derivation.
- 2026-10-07: PR #13 CI 37573750547 passed Agent Plan Integrity, Static, Code, API and E2E; Historical Backtest Smoke 37573750369 passed.
- 2026-10-07: real acquisition self-test 37573580430 succeeded end to end. Compose/manifest validation passed, all 5 Funding + 3 Cash preparations succeeded, and final `Verify wave boundary` passed using dynamic expected counts rather than static 5/3/8 assertions.

## Resume from here

PR CI and the real 5+3 workflow self-test are green. Re-run required PR checks after this evidence-only checkpoint, then merge PR #13, verify main CI, and finalize/close through the completed-plan lifecycle.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: pending
