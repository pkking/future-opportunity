# Cash 2025 Q3 deep-book non-positive price diagnosis

Issue: #69
Status: IMPLEMENTING
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
- [ ] Final-head static, code, API, E2E and historical CI gates pass; merge and
      post-merge main CI evidence recorded.

## Implementation slices

- [x] 1. Extend diagnostic extractor to inspect the full first event and
      produce bounded per-side anomaly evidence.
- [x] 2. Add synthetic deeper-price and malformed-level regression tests.
- [ ] 3. Verify CI, record exact head/results, merge on approved clean PR,
      verify main; leave Issue #69 open pending new operator source evidence.

## Verification matrix

| Gate | Command / evidence | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_cash_l2_failure_diagnostics.py -v` | pending |
| Static | `uv run ruff check .` | pending |
| Code | `uv run pytest tests --ignore=tests/test_api_smoke.py --ignore=tests/e2e` | pending |
| API | `uv run pytest tests/test_api_smoke.py` | pending |
| E2E | `uv run pytest tests/e2e -v` | pending |
| Historical | Historical Backtest Smoke pinned offline replay | pending |

## Decision gates

None for metadata-only diagnostic enhancement. A later adjustment to treatment
of invalid prices is a separate semantics decision requiring captured raw
levels, format documentation, a new regression contract, and review.

## Evidence log

- 2026-10-15: downloaded and read ZIP artifact 11959004684. `entry_future`
  failed; first three prices are nonzero; observed 400 bid and ask levels.
- No exact offending `[price,size,orderCount]` tuple is yet available.
- First code implementation includes full 400-level index traversal with a cap
  of 8 representative anomalies per book side; the replay gate is unchanged.
  CI must validate the actual test run before this is complete.

## Resume from here

Add capped anomaly evidence to `okx_l2_diagnostics.py` with tests. Ship through
PR linked to Issue #69. When on main, operator may re-dispatch the **same
one-case diagnostic only** to obtain level indices and raw values. Do not
re-run the frozen 12-date Q3 wave until reviewed normalization/source resolution.

## Completion

Pending final reviewed head, CI, Historical Smoke, main.
Issue #69 stays open. No 2025 Q3 source case promoted.
