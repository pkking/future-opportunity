# Strict OKX FUTURES snapshot empty-tail compatibility

Issue: #69
Status: COMPLETED
Owner: agent
Started: 2026-10-17
Last checkpoint: 2026-10-17

## Objective
Reconstruct legitimate price levels of the frozen Q3 Cash `BTC-USDT-250926`
historical futures L2 snapshot while rejecting real invalid price levels,
without losing raw source integrity or weakening unrelated instruments/events.

## Evidence and scope
- Operator single-case run [39015453399](https://github.com/pkking/future-opportunity/actions/runs/39015453399)
  (2026-10-17 07:55:44 UTC) executed main `8d8fa938bf1b25db5622ede26dfc0b4d798eeb99`;
  completed FAILURE in L2 normalization as expected. Artifact ID
  `12094284504`, `cash-l2-diagnostics-2025-07-04-BTC-USDT-250926-39015453399`,
  Actions SHA-256 `6d74496ad52fd8d054d32373fb8f4f735466d26122dd826f8a23e55afeafb7d6`.
- Downloaded ZIP; `entry_future.json` proves `BTC-USDT-250926` initial
  snapshot (line 1; `ts=1751587200011`) has exactly 400 bids and 400 asks.
  Asks index 325 onward (zero-based) are 75 nonpositive prices; first
  reported eight anomaly tuples (indices 325..332) are all
  `["0","0.0","0"]`. No anomalous bids or anomalous price type/shape.
  With 75 nonpositive prices total and first at 325, all indices 325..399
  must be zero-priced; the remaining 67 sizes/counts are not known from
  this bounded report.
- Raw source `BTC-USDT-futureschain-L2orderbook-400lv-2025-07-04.tar.gz`
  SHA-256 `0889b779631687d433472d8c1d2b3b8890edc29afff583d3891bff1900d0cafa`,
  member `BTC-USDT-250926-L2orderbook-400lv-2025-07-04.data`,
  first line SHA-256 `0b0c9fd8aca7e29bb6a86d7b97d67e67ee63f53d78f08d5485171cd5c7dc310f`.
- OKX official docs explicitly describe up to 400 book depth levels and
  price/size/order-count roles, but do not explicitly document empty tail
  padding; the interpretation is **provisional**, supported by real source
  shape but *not* a blanket exchange contract.
  Docs: https://www.okx.com/docs-v5/en/ ; https://www.okx.com/historical-data
- This is a normalization-only adapter implementation; no domain model/ADR,
  paper/live boundary, capital policy or economics target is changed.

## Non-goals
- No generic ignoring of zero prices, no nonzero quantities removed, no update
  or SPOT/SWAP changes, no source/date replacement, no corpus growth before
  real operator evidence, and no automated dispatch/promotion.
- Do not infer remaining 67 raw level sizes/order counts from the **previous
  bounded diagnostic alone**. The 2026-10-17 post-fix Run 39016429500
  successfully replayed the *same SHA-256 raw archive* under an exact-match
  fail-closed parser, giving runtime support for source compatibility.
- Do not count a diagnostic-only run without frozen selection provenance as
  successful Q3 evidence.

## Acceptance criteria
- [x] Only FUTURES 400-depth `snapshot` may elide a contiguous terminal
      suffix of *exact* `["0","0.0","0"]` records, never any other tuple.
      At least one actual price level per side must remain.
- [x] Shared handling in full and sampled historical replay; genuine
      price > 0, size/order count bounds, source order/time and downstream
      canonical checks remain fail-closed.
- [x] Tests cover observed 325/75 ask tail, short/no-pad snapshots, middle
      padding with subsequent real level, zero-price nonzero size/count,
      partial/different padding, all-zero side, SPOT/SWAP and update-event
      rejection, full and sampled archive replay and identical resulting books.
- [x] Final-head CI (static/code/API/E2E/plan) and Historical Smoke success;
      squash merge and post-merge main CI success.
- [x] Issue #69 checkpointed; operator executed one **diagnostic-only**
      historical case, Run 39016429500, which completed SUCCESS, with four
      normalized books and auditable return evidence. This establishes only
      the single-case parser compatibility, not frozen Q3 wave completion.

## Implementation slices
- [x] 1. Apply strictly scoped empty-tail parsing to snapshot level arrays.
- [x] 2. Add synthetic 400-depth contract tests for both replay paths and
      negative cases.
- [x] 3. Verify final heads, squash merge, main CI, and checkpoint outcomes.

## Verification matrix
| Gate | Command | Status |
|---|---|---|
| Targeted | New regression tests in code-level CI | final-head 39015877087 PASS |
| Static | `uv run ruff check .` | final-head 39015877087 PASS |
| Code | CI Code-level tests | 39015877087 PASS; initial head 448 passed |
| API | CI API contract tests | final-head 39015877087 PASS |
| E2E | CI E2E strategy acceptance | final-head 39015877087 PASS |
| Historical | Historical Backtest Smoke | final-head 39015877090 PASS |

## Evidence log

- PR #76 initial head `862818319d9cd3378bb516b25006a1b5c8a38992`:
  CI 39015741758 SUCCESS with 448 code-level tests passed, static,
  API, E2E, plan integrity; historical smoke 39015741705 SUCCESS.
- The first eight observed anomalous futures ask records match the
  exact tail tuple, but only these eight sizes/order counts were exposed
  by the bounded diagnostic. The other 67 must match the accepted
  tuple or this patch still fails closed. No new valid Q3 source is claimed.

- 2026-10-17: final reviewed head `edf593ba489c78f5109ebdbc126b2ac0e745658b`:
  [CI 39015877087](https://github.com/pkking/future-opportunity/actions/runs/39015877087) SUCCESS,
  [Historical Smoke 39015877090](https://github.com/pkking/future-opportunity/actions/runs/39015877090)
  SUCCESS; PR #76 squash merged as
  `a41fe7366b6412d23cdf660198dde80753847ab4`;
  [post-merge main CI 39015937288](https://github.com/pkking/future-opportunity/actions/runs/39015937288)
  SUCCESS. No live Q3 source sample has been replayed under the fix yet.

- 2026-10-17: **post-fix operator single-case run [39016429500](https://github.com/pkking/future-opportunity/actions/runs/39016429500) SUCCESS** on main `991b6dfd54b2fe92282f699ce8fc05e1d7cfdcbd`. Independently downloaded and inspected three Actions ZIPs:
  - Prepared artifact ID `12094861759`, ZIP SHA-256
    `f952e173a7f24d47cc4f467361dea2ad7e37ff1cb559137d94b54800dc03a39f`;
  - Compact artifact ID `12094144514`, ZIP SHA-256
    `889f28216557caf13ea99cdfd046bd82b2583c54416ec56931bbde2f4eabdc35`;
  - Actuals artifact ID `12095101201`, ZIP SHA-256
    `bc23d6fe578b7e0a88130646c3ac79957c666792a7501a86def3396d36b020bc`.
- SHA-256 validation for all four prepared and all four compact canonical
  JSONL files passes; all retained prices/sizes are positive. Every
  component contains exactly one sampled book. Observed staleness:
  `entry_spot` 5ms (400/400 bid/ask levels),
  `entry_future` 15ms (400/347),
  `exit_spot` 7ms (400/400),
  `exit_future` 17ms (293/200), all under 5000ms.
  The `entry_future` raw source SHA
  `0889b779631687d433472d8c1d2b3b8890edc29afff583d3891bff1900d0cafa`
  matches the source archive that failed before the fix.
  Compact `derived_from_artifact` correctly pins parent prepared ID,
  parent ZIP digest and run `39016429500`.
- Actuals: one `qualified=true`, `return_complete=true` paper backtest
  case, `initial_delta_pct=0`; expected net return
  `0.003344534466122320868897087483`, simulated realized net return
  `0.003524818444121093505496828224`; `target_status=not_yet_decided`.
  `MarginSafety` and `VenueExposure` **unassessed**.
  This is single-case reporting, not Stage 2 return threshold evidence.
- **Crucial:** this diagnostic-only run's prepared manifest has
  **no `selection_provenance`** and is **NOT promotable**. It adds **zero**
  pinned 2025 Q3 corpus days; do not count its `commit_ready` compact
  metadata alone as satisfying frozen selection proof.

## Decision gate
The unsupported general claim that *all* zero-priced exchange levels are
meaningless remains prohibited. This narrowly recognized transport-format
suffix is a provisional adapter rule; if any level differs from the exact
captured tuple, fail closed with source and level evidence. Widening the
format contract requires further source evidence and review.

## 2026-10-17 frozen Q3 source revalidation

After single-case validation, operator-dispatched frozen Q3 wave
[39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
completed SUCCESS on `437089cc`. All 12 registered, source-proven
Cash cases passed preparation and actuals generation. The workflow's
`cash-2025-quarter-summary-q3` artifact ID `12094684975` reports
`verified_inventory_only` and exactly 12 prepared, 12 compact,
12 actuals; no errors, missing, unexpected or expired artifacts.

Independently downloaded and inspected all 36 ZIPs: all 36 Actions ZIP
SHA-256 values match; all 96 prepared/compact normalized JSONL
SHA-256 values match; every canonical order-book price and retained
quantity is positive; all staleness values ≤578ms against 5000ms;
every compact's parent ZIP ID/digest matches, every source has the
original frozen selection provenance, and all 12 actuals match dates
and dataset IDs. **9 qualified + 3 correctly rejected** for
nonpositive expected net returns (September 7/15/22), no synthetic
zero realized return assigned to rejections. Paper return economics
remain reporting-only; no corpus promotion or Stage-2 gate enabled.

See `docs/exec-plans/active/2026-10-10-cash-2025-quarter-artifact-identity.md`
for the source-of-truth quarter audit and Q4 operator handoff.

## 2026-10-17 Q4 content verification (supersedes Q4 pending)

Frozen Q4 [Run 39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844)
on main `5bdc259` succeeded **12/12**, 12 prepared +
12 compact + 12 actuals. Built-in `summary-q4` artifact ID
`12095459608`: `verified_inventory_only`, no metadata errors.
An additional independent content audit verified **36/36 Actions ZIP
SHA-256**, **96/96 normalized JSONL SHA-256**, all four required
positive-price books, maximum source age 409ms/5000ms, all
parent artifact digest/ID links, frozen selection provenance,
and 12/12 actuals. Outcomes: **7 qualified**, **5 correctly
unqualified** with `realized_net_return=null`.

Q3 [39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
was independently verified before this: combined Q3/Q4 now **24
dates, 72 ZIPs, 192 canonical normalized JSONL**, with no
content audit errors. No campaign planner or corpus promotion was
dispatched by these preparation workflows.

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
Implementation merged and post-merge CI green. Post-fix **2025-07-04
single-case real source** verified via Run 39016429500 and ZIP content
checks. Frozen Q3 wave 39016938121 and its 12x3 ZIPs are now independently
VERIFIED; **no new Q3 fixture has been promoted**. Q4 Run 39018358844 now VERIFIED. Q3 and Q4 fixed waves are accepted
as historical preparation evidence, with no promotion or planner
executed. Issue #69 remains OPEN pending planning and corpus gates.

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
