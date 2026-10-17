# Cash 2025 Q3 deep-book non-positive price diagnosis

Issue: #69
Status: COMPLETED
Owner: agent
Started: 2026-10-15
Last checkpoint: 2026-10-15

## Objective

Make the already successful failure-evidence upload identify the **actual
offending deep-book price levels** in the frozen 2025 Q3 Cash historical
source, without changing what the normalization adapter accepts. This is a
read-only diagnostic aid and does not make any new samples commit-ready.

## Source evidence and correction

- Operator single-case diagnostic run [38709843446](https://github.com/pkking/future-opportunity/actions/runs/38709843446),
  2026-10-15T09:01:08Z, main `8fa9f955d706bb2235875b9b18b5aa825a6ffc88`:
  `failure` with expected `historical price must be positive at line 1`.
- Uploaded evidence artifact `cash-l2-diagnostics-2025-07-04-BTC-USDT-250926-38709843446`
  (artifact ID 11959004684, Actions SHA-256
  `42cf15dd8918edd80daa750677c4381f10a615165486c9b69ad2dbf8352a8ae1`).
  The ZIP contained `entry_future.json`, **not** `entry_spot.json`.
- This **corrects** the earlier assumption in the [previous diagnosis
  plan](2026-10-15-cash-2025-l2-first-record-diagnostics.md) that
  `entry_spot` failed. It passed. The initial futures snapshot
  `BTC-USDT-250926-L2orderbook-400lv-2025-07-04.data` has 400 bids and
  400 asks; its first three levels on both sides contain **positive prices**.
  The error lies elsewhere in the initial snapshot. Raw ZIP SHA-256
  `0889b779631687d433472d8c1d2b3b8890edc29afff583d3891bff1900d0cafa`;
  first-line SHA-256 `0b0c9fd8aca7e29bb6a86d7b97d67e67ee63f53d78f08d5485171cd5c7dc310f`.
- Official OKX API documentation describes initial 400-level snapshot
  structure but does **not** establish that zero-priced levels may safely
  be ignored. No relaxation of strict positivity is justified at this point.
- Previous run 38693593014's 12/12 frozen Q3 cases failed, but the exact
  per-date offending level remained unknown.

## Non-goals / safety boundaries

- Do not suppress, repair, round, drop, synthesize, or reinterpret data.
- Do not change `iter_okx_l2_sampled_jsonl`, `_apply_levels`, or downstream
  canonical book / qualification / return rules.
- No source URL logging, full raw line/ZIP upload, on-chain or live trading,
  frozen sample replacement, Q4 dispatch, or corpus promotion.
- Source semantics remain `UNASSESSED` until deep-level details and
  authoritative exchange evidence exist.

## Acceptance criteria

- [x] Inspect every level of the **first nonblank source event** on both sides;
      report all detected nonpositive price counts, out-of-range/non-numeric
      category counts, and bounded offending examples with side, zero-based
      index, raw `[price,size,orderCount]` and reason.
- [x] Keep output bounded (at most 8 offending examples per side and capped
      field lengths), deterministic, JSON-serializable; preserve first three
      levels for continuity with the existing evidence schema.
- [x] Never mask or alter the original normalization failure; no source URLs,
      raw archive contents, or strategy semantics change.
- [x] Synthetic 400-level regression proves a first invalid price at index
      beyond the first 3 is found, and verifies correct reported side/size,
      counts, bounds, and continued fail-closed replay.
- [x] Final-head static, code, API, E2E and historical CI gates pass.
- [x] Merge and post-merge main CI evidence recorded.

## Implementation slices

- [x] 1. Extend diagnostic extractor to inspect the full first event and
      produce bounded per-side anomaly evidence.
- [x] 2. Add synthetic deeper-price and malformed-level regression tests.
- [x] 3. Verify CI, record exact head/results, merge on approved clean PR,
      verify main; leave Issue #69 open pending new operator source evidence.

## Verification matrix

| Gate | Command / evidence | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_cash_l2_failure_diagnostics.py -v` | code-level tests 38710698213 success |
| Static | `uv run ruff check .` | 38710698213 success |
| Code | `uv run pytest tests --ignore=tests/test_api_smoke.py --ignore=tests/e2e` | 38710698213 success |
| API | `uv run pytest tests/test_api_smoke.py` | 38710698213 success |
| E2E | `uv run pytest tests/e2e -v` | 38710698213 success |
| Historical | Historical Backtest Smoke pinned offline replay | 38710698154 success |

## Decision gates

None for metadata-only diagnostic enhancement. A later adjustment to treatment
of invalid prices is a separate semantics decision requiring captured raw
levels, format documentation, a new regression contract, and review.

## Evidence log

- 2026-10-15: downloaded and read ZIP artifact 11959004684. `entry_future`
  failed; first three prices are nonzero; observed 400 bid and ask levels.
- No exact offending `[price,size,orderCount]` tuple is yet available;
  a **new** operator-run artifact is required. PR #74 completion is an
  implementation milestone, not successful market-data preparation.
- 2026-10-15: PR #74 final head `14e19a6` passed CI 38710879648 and
  Historical Smoke 38710879663; squash merged `bc27e44`, post-merge
  CI 38710975850 passed.
- First code implementation includes full 400-level index traversal with a cap
  of 8 representative anomalies per book side; the replay gate is unchanged.
  PR #74 head `566f7a0aab0323c50899cb3d7b69096de9744439` CI
  [38710698213](https://github.com/pkking/future-opportunity/actions/runs/38710698213)
  and Historical Smoke [38710698154](https://github.com/pkking/future-opportunity/actions/runs/38710698154)
  both succeeded for plan/static/code/API/E2E/historical gates.

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

Initial fully green review head: `566f7a0aab0323c50899cb3d7b69096de9744439` (PR #74).
CI 38710698213 success; Historical Smoke 38710698154 success.
Final head: `14e19a6d53ba5dadf8cca15f4ff511f9b82d295f`.
Final-head CI: https://github.com/pkking/future-opportunity/actions/runs/38710879648 (success).
Final-head Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/38710879663 (success).
PR #74 squash merged: `bc27e44bc8b10e2b41ab87723ddd5beae83f8566`.
Post-merge main CI: https://github.com/pkking/future-opportunity/actions/runs/38710975850 (success).
Issue #69 stays open. No 2025 Q3 source case promoted.

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
