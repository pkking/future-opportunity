# 2026-10-05-historical-corpus-expansion: Expand pinned historical corpus

Status: PLANNING
Owner: agent
Started: 2026-10-05
Last checkpoint: 2026-10-05

## Objective

Operationalize the Stage-1 -> Stage-2 evidence progression defined by ADR-0007.

The repository currently has one pinned entry-market day for Funding Carry and
one for Cash-and-Carry. Build an incremental historical corpus workflow that can
accumulate additional real-market days without changing strategy targets,
without committing raw exchange archives, and without weakening provenance.

## Non-goals

- Do not define Stage-2 distribution thresholds.
- Do not change deterministic reference targets.
- Do not add live trading.
- Do not treat optimistic/no-depth scans as pinned historical days.
- Do not auto-activate Stage 2 when 30/90 days are reached.

## Governing decisions

- ADR-0006: historical dataset provenance.
- ADR-0007: progressive historical acceptance policy.
- tests/e2e/historical-target-policy.json.

## Current facts

- Stage-1 historical gate is active: provenance + deterministic replay +
  business semantics.
- Funding Carry pinned entry-market days: 1 (2026-09-01).
- Cash-and-Carry pinned entry-market days: 1 (2026-06-01).
- Stage-2 minimum eligibility: 30 distinct pinned entry-market days per strategy.
- Stage-2 preferred evidence base: 90 days per strategy.
- Historical Backtest Smoke run 37321387071 passed with artifact 11351120087.
- Final archived Stage-1 repository CI run 37321809733 passed.

## Constraints and invariants

- Raw exchange archives remain out of git.
- Every pinned day must remain independently traceable to official source
  archive/query/checksum evidence.
- Compact books must preserve the frozen scenario quantity with the declared
  safety margin.
- A pinned entry day counts toward readiness only when its committed fixture is
  offline-replayable and passes corpus validation.
- Existing negative days remain valid data.
- Duplicate strategy/date entries must fail closed.
- Corpus accumulation must be resumable and idempotent.
- Preparation workflows may use network; CI gating replay may not.

## Acceptance criteria

- [x] Define a versioned corpus index/manifest contract.
- [x] Corpus validator discovers pinned strategy/date entries and rejects duplicates.
- [x] Historical smoke readiness is derived from validated corpus facts.
- [x] Funding Carry preparation accepts arbitrary UTC entry dates.
- [ ] Funding Carry batch workflow can prepare multiple dates independently.
- [ ] Prepared Funding days emit compact, commit-ready fixtures plus provenance.
- [ ] Cash-and-Carry preparation accepts explicit entry/exit dates and future ID/spec provenance.
- [ ] Cash batch discovery identifies historical dates/instruments without inventing expired metadata.
- [ ] Add at least one additional pinned real-market day per strategy through the generalized path.
- [ ] CI/historical smoke remain green.
- [ ] Docs explain how to add a day and how 30/90 readiness is computed.

## Implementation slices

- [x] 1. Add corpus contract + validator/index.
- [x] 2. Generalize Funding Carry single-day preparation.
- [ ] 3. Add Funding date-range/batch workflow.
- [ ] 4. Generalize Cash-and-Carry preparation inputs.
- [ ] 5. Add Cash historical-date discovery/batch preparation.
- [ ] 6. Pin additional days through generalized workflows.
- [ ] 7. Verify corpus/readiness evidence and document reproduction.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | pending |
| Code | corpus/preparation/duplicate/idempotency tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged deterministic targets green | pending |
| Historical smoke | Stage-1 gate green, readiness count increases only for valid pinned days | pending |
| Preparation diagnostics | source/checksum/compact derivation evidence | pending |

## Decision gates

None yet.

A future decision is required only when Stage-2 distribution metrics/thresholds
are proposed. Accumulating evidence does not require a new decision.

## Evidence log

- 2026-10-05: ADR-0007 Stage-1 policy completed and archived.
- 2026-10-05: Stage-1 final archive CI run 37321809733 passed.
- 2026-10-05: versioned corpus index and validator implemented. Corpus loading
  fails closed on duplicate dataset IDs, duplicate strategy/date entries,
  duplicate paths, unindexed pinned fixtures, and manifest/index drift.
- 2026-10-05: historical readiness is derived from validated corpus facts. The
  current repository count is 1 pinned entry-market day for Funding Carry and 1
  for Cash-and-Carry; minimum/preferred readiness remains false at 30/90.
- 2026-10-05: Funding preparation workflow is generalized with a required
  `history_date` workflow input and emits both full provenance evidence and a
  commit-ready compact fixture for that UTC date.

## Deviations and discoveries

None.

## Resume from here

Add a resumable Funding Carry date-range batch workflow. Each UTC date must run
as an independent matrix job and emit its own full/compact artifacts so one
failed market day does not invalidate successfully prepared days. Then inspect
and generalize Cash-and-Carry preparation inputs.

## Completion

Final commit:
CI run:
Historical smoke artifact:
Pinned day counts:
Remaining unassessed items:
