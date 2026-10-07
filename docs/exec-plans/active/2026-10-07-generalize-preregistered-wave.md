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

- [ ] Wave summary derives expected Funding/Cash counts from composed acquisition JSON.
- [ ] No reusable verification logic hard-codes 5/3/8.
- [ ] Compact total equals expected Funding + expected Cash.
- [ ] Unique compact name count equals compact total.
- [ ] Per-strategy artifact counts exactly equal derived expected counts.
- [ ] Zero-item Funding or Cash side is handled safely.
- [ ] Selection provenance remains required for every non-empty strategy side.
- [ ] Existing first-wave default inputs remain unchanged.
- [ ] Workflow remains actions:read + contents:read only.
- [ ] Contract tests cover dynamic counts and reject reintroduction of hard-coded assumptions.
- [ ] README/testing guidance describes reusable wave semantics.
- [ ] Full CI and Ruleset checks pass.

## Implementation slices

- [x] 1. Inspect current workflow/tests and identify hard-coded count boundary.
- [ ] 2. Generalize wave summary and identity verification.
- [ ] 3. Update workflow contract tests.
- [ ] 4. Update user/agent documentation.
- [ ] 5. Verify PR CI and merge; complete/close through normal lifecycle.

## Verification matrix

| Scope | Evidence | Status |
|---|---|---|
| Plan integrity | PR required check | pending |
| Workflow contract | `tests/test_pre_registered_acquisition_wave_workflow.py` | pending |
| Static | CI | pending |
| Code | CI | pending |
| API | CI | pending |
| E2E | CI | pending |

## Decision gates

None. This removes an implementation-specific first-wave constraint while preserving the existing accepted evidence and safety boundaries.

## Evidence log

- 2026-10-07: current workflow inputs are reusable, but summary asserts expected_funding_count=5, expected_cash_count=3 and total/unique/funding/cash artifact counts 8/8/5/3.
- 2026-10-07: latest read-only planner run 37572071278 reports pinned Funding=8 / Cash=5 and no remaining candidates from preregistered-wave-001, so the next acquisition must be a new pre-registered wave rather than replaying wave 001.

## Deviations and discoveries

None yet.

## Resume from here

Edit `.github/workflows/acquire-pre-registered-historical-wave.yml` so expected counts are derived from the composed acquisition JSON and used by both summary evidence and artifact identity validation; then update focused tests before documentation.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: pending
