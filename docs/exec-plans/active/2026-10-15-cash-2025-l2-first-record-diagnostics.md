# Cash 2025 Q3 initial L2 record diagnosis

Issue: #69
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-15
Last checkpoint: 2026-10-15

## Objective

Preserve actionable, bounded, cryptographically identified evidence of the
exact raw OKX L2 snapshot/update record that makes frozen Cash 2025 Q3 fixture
preparation fail on `historical price must be positive at line 1`.
Do not reinterpret or silently drop invalid book prices.

## Non-goals

- Do not replace frozen market dates, change SPOT/FUTURES instruments, alter
  historical normalization or qualification semantics, promote fixtures, or
  enable trading/economics thresholds.
- Do not infer that a zero-price record is a documented exchange sentinel until
  a captured raw record and official format evidence establish this.

## Must-read context

- `AGENTS.md`, `docs/design-baseline-v0.1.md`,
  `docs/v0-implementation-status.md`,
  `docs/agents/workflow.md`, `docs/agents/testing.md`
- `src/future_opportunity/adapters/historical/okx_l2.py`
- `scripts/prepare_okx_cash_and_carry_fixture.py`
- `.github/workflows/prepare-cash-historical-fixture.yml`
- `tests/test_okx_historical_l2.py`

## Current facts

- On 2026-10-15 at 06:38:12 UTC operator-dispatched run
  https://github.com/pkking/future-opportunity/actions/runs/38693593014
  on main `811ab34a9da3e8d21147ff94ae48319c038626f2`.
- Frozen Q3 resolve and acquisition manifest validation succeeded.
- 2025-07-04, 2025-07-11 and subsequent Cash cases fail while preparing the
  **first** component `entry_spot`, prior to `entry_future`/exit evidence.
- Exact causal stack: `iter_okx_l2_sampled_jsonl` ->
  `_apply_levels` -> `_positive_decimal`; observed error
  `ValueError: historical price must be positive at line 1`.
- Failed preparation currently uploads no raw-source evidence; actuals file is
  absent. A catalog file identity does not establish L2 validity or cadence.
- GitHub Actions cannot be dispatched by the current GitHub connector.

## Acceptance criteria

- [ ] On normalization failure, write bounded diagnostic JSON that identifies
      component, UTC market sample, exact expected instrument, raw archive
      filename/member, bytes/SHA-256 and first-record action/ts/level counts
      and bounded bid/ask preview, without recording presigned source URLs.
- [ ] Diagnostic capture never masks the original error, nor converts failed
      preparation into success; no raw archive files committed or uploaded.
- [ ] Workflow uploads diagnostic evidence with `if: always()` and limited
      `contents: read`, even if preparation fails.
- [ ] Offline tests prove diagnostic contents/failure behavior on a controlled
      synthetic tar.gz with first-level zero price and malformed records.
- [ ] Final-head CI, API, E2E and pinned Historical Smoke pass.

## Implementation slices

- [ ] 1. Write an explicit first-record diagnostic extractor.
- [ ] 2. Guard normalization in Cash preparer; preserve diagnostics on failure.
- [ ] 3. Add always-upload artifact step and focused contract tests.
- [ ] 4. Run final-head checks, archive evidence or leave active if pending.

## Verification matrix

| Scope | Verification | Evidence |
|---|---|---|
| Targeted | `uv run pytest tests/test_cash_l2_failure_diagnostics.py -v` | pending |
| Static | `uv run ruff check .` | pending |
| Code | full repository code-tests | pending |
| API | REST contract CI | pending |
| E2E | deterministic strategy acceptance | pending |
| Historical | pinned offline replay | pending |

## Evidence log

- 2026-10-15: run 38693593014; 2025-07-04 job 116285061210 and
  2025-07-11 job 116285061294 have identical first-line non-positive
  price errors. The exact invalid level and raw archive provenance were
  not logged in those runs.
- Parser enforces strictly positive prices and non-negative sizes. This gate
  must remain intact absent raw-data evidence and accepted policy.

## Decision gates

No product decision for observability-only diagnostics. Normalization of any
previously rejected book level requires independent format evidence and
separate review. Operator dispatch remains explicit.

## Resume from here

Implement extractor and failure-upload contract. Once CI passes, merge
diagnostics only; record Run 38693593014's terminal outcome in Issue #69.
The operator can rerun frozen Q3 after the diagnostic change is on main.
Use the diagnostic artifact to determine if raw data is invalid or a
documented record encoding requires a separate parser fix.

## Completion

Final reviewed head: pending
CI: pending
Historical Smoke: pending
Unassessed: exact first raw record and Q3 source-content correctness.
