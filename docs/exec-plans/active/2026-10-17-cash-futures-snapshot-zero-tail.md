# Strict OKX FUTURES snapshot empty-tail compatibility

Issue: #69
Status: BLOCKED_EVIDENCE
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
- Do not infer remaining 67 raw level sizes/order counts. Fail closed unless
  *all* 75 levels match the exact observed empty-row tuple.
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
- [ ] Issue #69 checkpointed; user operator explicitly re-runs **one
      diagnostic-only historical case** to verify live source semantics,
      before any frozen Q3 rerun or Q4 dispatch.

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

## Decision gate
The unsupported general claim that *all* zero-priced exchange levels are
meaningless remains prohibited. This narrowly recognized transport-format
suffix is a provisional adapter rule; if any level differs from the exact
captured tuple, fail closed with source and level evidence. Widening the
format contract requires further source evidence and review.

## Resume from here
**Blocked on operator source verification, not development.** The
strict FUTURES suffix parser is on main at `a41fe7366b6412d23cdf660198dde80753847ab4`.
Explicitly dispatch only the original **single-case diagnostic**:

```bash
gh workflow run prepare-cash-historical-fixture.yml -R pkking/future-opportunity --ref main \
  -f entry_at=2025-07-04T00:15:00+00:00 \
  -f exit_at=2025-09-25T00:15:00+00:00 \
  -f future_id=BTC-USDT-250926 \
  -f expiry_at=2025-09-26T08:00:00+00:00
```

If it succeeds, validate entry and exit SPOT/FUTURES provenance, checksum,
staleness and actuals; inspect whether all 75 trailing rows were accepted by
the **exact** 3-field suffix gate, not just first eight. If it fails, capture
the new source error and diagnostic artifact. This single-case run lacks
frozen selection provenance and is **not promotable**. Only after independent
review of a successful diagnostic, operator runs the unchanged frozen Q3
12-date wave, audits exact 12×3 artifacts, then Q4 and corpus planning.
Issue #69 stays open; no new pinned case or trading/economics gate was enabled.

## Completion
Implementation merged and post-merge CI green; acceptance of *real* Q3
historical source remains UNASSESSED until the next explicit operator run.
No new pinned cases or Q3/Q4 promotion; Issue #69 remains open.
