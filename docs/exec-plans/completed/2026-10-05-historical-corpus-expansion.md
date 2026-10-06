# 2026-10-05-historical-corpus-expansion: Expand pinned historical corpus

Status: COMPLETED
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
- Funding Carry pinned entry-market days: 2 (2026-09-01, 2026-09-02).
- Cash-and-Carry pinned entry-market days: 2 (2026-06-01, 2026-06-02).
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
- [x] Funding Carry batch workflow can prepare multiple dates independently.
- [x] Prepared Funding days emit compact, commit-ready fixtures plus provenance.
- [x] Cash-and-Carry preparation accepts explicit entry/exit dates and future ID/spec provenance.
- [x] Cash batch discovery identifies historical dates/instruments without inventing expired metadata.
- [x] Add at least one additional pinned real-market day per strategy through the generalized path.
- [x] CI/historical smoke remain green.
- [x] Docs explain how to add a day and how 30/90 readiness is computed.

## Implementation slices

- [x] 1. Add corpus contract + validator/index.
- [x] 2. Generalize Funding Carry single-day preparation.
- [x] 3. Add Funding date-range/batch workflow.
- [x] 4. Generalize Cash-and-Carry preparation inputs.
- [x] 5. Cash discovery batch implemented; prepare second discovered day.
- [x] 6. Pin additional days through generalized workflows.
- [x] 7. Verify corpus/readiness evidence and document reproduction.

## Verification matrix

| Scope | Expected evidence | Status |
|---|---|---|
| Static | ruff + architecture/agent contract | passed in final CI 37431649316 |
| Code | corpus/preparation/duplicate/idempotency tests | passed in final CI 37431649316 |
| API | no regression | passed in final CI 37431649316 |
| Reference E2E | unchanged deterministic targets green | passed in final CI 37431649316 |
| Historical smoke | Stage-1 gate green, readiness count increases only for valid pinned days | passed run 37431012300 |
| Preparation diagnostics | source/checksum/compact derivation evidence | Funding 37327493270; Cash 37327804191 |

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
- 2026-10-06: Funding batch run 37327493270 prepared 2026-09-02 successfully.
  Full artifact 11353260627 and commit-ready compact artifact 11353595058 were
  produced; 2026-09-02 is now pinned in the corpus.
- 2026-10-06: Cash discovery run 37327462529 discovered 2026-06-02 successfully.
  Cash batch run 37327804191 then prepared the explicit BTC-USDT-260626 case;
  compact artifact 11353141045 was produced and 2026-06-02 is pinned.
- 2026-10-06: corpus counts are now Funding Carry 2 days and Cash-and-Carry
  2 days. Historical Backtest Smoke run 37431012300 passed after the Funding
  2026-09-02 corpus index update.
- 2026-10-06: code-level CI exposed stale tests that hard-coded the original
  1+1 corpus. The tests were changed to derive expectations from the versioned
  corpus index so future corpus growth does not create false failures.
- 2026-10-05: Funding batch preparation accepts an inclusive UTC date range up
  to 31 days and executes each date as an independent matrix job with
  fail-fast=false. The batch reuses the single-day workflow rather than
  duplicating provenance logic.
- 2026-10-05: Cash preparation accepts explicit entry_at, exit_at, future_id,
  and expiry_at. The historical future ID remains an explicit input and product
  specification provenance is separated from unavailable expired-instrument
  metadata.
- 2026-10-05: Cash preparation now derives and finalizes a compact fixture using
  the same frozen-capital/depth-preservation rule as Funding.
- 2026-10-05: Cash batch discovery accepts a bounded date range; each date
  independently queries official module-4 FUTURES history, verifies the archive
  member identity, checks public delivery evidence, and leaves missing delivery
  evidence unassessed rather than synthesizing it.

## Deviations and discoveries

None.

## Resume from here

Use the generalized workflows to prepare a second pinned day for each strategy:
Funding 2026-09-02 and, if official Cash discovery succeeds, Cash 2026-06-02
with the discovered future ID. Validate compact artifacts, commit them to the
corpus index, then recompute readiness.

## Completion

Final implementation/docs commit: 4950dab89a9fa94a6e5a6bdc980514a0ae409fc2
CI run: https://github.com/pkking/future-opportunity/actions/runs/37431649316
Historical smoke artifact: run 37431012300 (green)
Pinned day counts: Funding Carry 2; Cash-and-Carry 2
Remaining unassessed items: Stage-2 distribution thresholds; intentionally deferred by ADR-0007

- 2026-10-06: final documentation commit 4950dab89a9fa94a6e5a6bdc980514a0ae409fc2
  passed all CI gates in run 37431649316. Static, code-level, API contract, and
  reference E2E were green. The corpus/readiness tests now derive expectations
  from the versioned corpus index instead of hard-coding corpus size.
