# Cash 2025 Q3 initial L2 record diagnosis

Issue: #69
Status: COMPLETED
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
- 2025-07-04, 2025-07-11 and subsequent Cash cases failed in the initial
  2025 Q3 wave; the exact failing component could not be determined from
  those workflow logs alone. The later single-case diagnostic run
  38709843446 proves the 2025-07-04 failure is in **entry_future**, after
  the preceding entry_spot component completed.
- Exact causal stack: `iter_okx_l2_sampled_jsonl` ->
  `_apply_levels` -> `_positive_decimal`; observed error
  `ValueError: historical price must be positive at line 1`.
- Failed preparation currently uploads no raw-source evidence; actuals file is
  absent. A catalog file identity does not establish L2 validity or cadence.
- GitHub Actions cannot be dispatched by the current GitHub connector.

## Acceptance criteria

- [x] On normalization failure, write bounded diagnostic JSON that identifies
      component, UTC market sample, exact expected instrument, raw archive
      filename/member, bytes/SHA-256 and first-record action/ts/level counts
      and bounded bid/ask preview, without recording presigned source URLs.
- [x] Diagnostic capture never masks the original error, nor converts failed
      preparation into success; no raw archive files committed or uploaded.
- [x] Workflow uploads diagnostic evidence with `if: always()` and limited
      `contents: read`, even if preparation fails.
- [x] Offline tests prove diagnostic contents/failure behavior on a controlled
      synthetic tar.gz with first-level zero price and malformed records.
- [x] Final-head CI, API, E2E and pinned Historical Smoke pass.

## Implementation slices

- [x] 1. Add bounded first-record diagnostic extractor in
      `src/future_opportunity/adapters/historical/okx_l2_diagnostics.py`.
- [x] 2. Guard canonical normalization in Cash preparer; preserve failed
      diagnostic JSON and original exception.
- [x] 3. Add always-upload diagnostic artifact step and focused contract tests.
- [x] 4. Verify final PR head, merge and verify main; preserve Q3 open
      because source-record semantics remain unassessed.

## Verification matrix

| Scope | Verification | Evidence |
|---|---|---|
| Targeted | `uv run pytest tests/test_cash_l2_failure_diagnostics.py -v` | CI 38694448296 code-tests success |
| Static | `uv run ruff check .` | CI 38694448296 success |
| Code | full repository code-tests | CI 38694448296 success |
| API | REST contract CI | CI 38694448296 success |
| E2E | deterministic strategy acceptance | CI 38694448296 success |
| Historical | pinned offline replay | 38694448328 success |

## Evidence log

- 2026-10-15: Q3 run 38693593014 completed **failure**: 12/12 Cash
  preparation matrix jobs failed; 0 prepared/compact/actuals data pairs,
  no corpus growth. Two resolve jobs passed. Jobs 116285061210 and
  116285061294 independently reproduce `historical price must be positive
  at line 1`; the logs lacked a specific component identifier, and the
  prior inference that entry_spot failed was incorrect. Inspected another
  failed job 116285552725 showing the same stack.
- 2026-10-15: PR #72 adds an explicit bounded first-record diagnostic,
  failure-only evidence upload and synthetic negative regression tests.
  First review head `234a841`: checks from runs 38694317455 and
  38694317448 passed (plan, static, code, API, E2E, historical).
- 2026-10-15: final head `cea5c74` CI 38694448296 and Historical Smoke
  38694448328 success, squash merged `f50502b`; main CI
  38694577221 success. No post-merge 2025 Q3 source diagnostic run yet.
- 2026-10-15: single-case diagnostic run 38709843446 uploaded `entry_future.json`
  (artifact 11959004684): BTC-USDT-250926 initial snapshot has 400 bids
  and 400 asks; all first three quoted prices per side are positive. Thus
  the first nonpositive price lies deeper than the first three levels.
  See `2026-10-15-cash-l2-deep-level-diagnostic.md` for this follow-up.
- Parser enforces strictly positive prices and non-negative sizes. This gate
  must remain intact absent raw-data evidence and accepted policy.

## Decision gates

No product decision for observability-only diagnostics. Normalization of any
previously rejected book level requires independent format evidence and
separate review. Operator dispatch remains explicit.

## Resume from here

**ARCHIVED / COMPLETED.** Earlier source failures, pending commands and
review-blocked state described above are retained as historical
checkpoints only and are superseded by this closeout. Do not replay
an acquisition, diagnostic, planner or promotion based on a stale
checkpoint in this file.

Issue #69 is closed/completed after the user approved [PR #82](https://github.com/pkking/future-opportunity/pull/82).
The exact frozen Q3 and Q4 12-day preparations were independently
verified (runs [39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
and [39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844));
read-only planner [39020272173](https://github.com/pkking/future-opportunity/actions/runs/39020272173)
and governed staging [39021366976](https://github.com/pkking/future-opportunity/actions/runs/39021366976)
produced the source-bound 24-item review. User-approved PR #82 merged
as `ad4790c0c7ec785eb2de9d53704e154515451001`.
Post-merge main CI and Historical Smoke both succeeded; pinned
corpus is **Cash 54 / Funding 32**, all 24 registered 2025 dates
retained including eight correctly unqualified samples.
For future work start a **new Issue and execution plan**; never
re-use the closed Issue #69. No economics threshold or live trading
was approved.

## Completion

Review head so far: `234a8410417f4264f95a6f57b8c1799bb116f202`
CI: https://github.com/pkking/future-opportunity/actions/runs/38694317455
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/38694317448
Final merge/post-merge evidence: pending
Unassessed: exact first raw record, meaning of zero-priced level, and Q3
source-content correctness. Issue #69 stays OPEN, no data promotion.

### Final reconciliation — 2026-10-17

Final commit: `ad4790c0c7ec785eb2de9d53704e154515451001` (PR #82,
human-approved completion of Issue #69, postdating the historical
checkpoints above; this archival move tracked under Issue #83).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39023534155 (main SUCCESS).
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/39023534123 (main SUCCESS).
Source integrity: Q3 39016938121 + Q4 39018358844; planner
39020272173; staged promotion 39021366976; 24/24 unique dates,
Cash 54 / Funding 32, no original fixture replaced.
Remaining unassessed items: The 90-day preferred distinct-day
coverage (Cash needs 36 more, Funding 58 more), more independent
Cash expiry cohorts, stronger Funding pre-entry regime coverage,
account-specific MarginSafety and portfolio-level VenueExposure.
Stage-2 economics and live execution remain DISABLED; these are
new research/ADR scopes, not unfinished tasks under Issue #69.
