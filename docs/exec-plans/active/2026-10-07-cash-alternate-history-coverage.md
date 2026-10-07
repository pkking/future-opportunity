# 2026-10-07-cash-alternate-history-coverage: Probe alternate official Cash history

Issue: #29
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Determine whether official OKX historical candlestick or trade products cover the exact 28 Wave 002/003 Cash dates that are absent from both L2 order-book modules 4 and 6.

This is a **coverage diagnostic only**. It must not silently redefine Cash-and-Carry historical evidence semantics.

## Current facts

- Issue #26/PR #27 proved module 4 and module 6 have identical dated-futures coverage for the tested matrix: 5/5 positive controls unique, 28/28 Wave 002/003 dates absent.
- Current pinned Cash corpus remains 5 distinct days.
- ADR-0006 requires source/schema provenance, fail-closed interpretation, and explicit missing evidence.
- ADR-0007 requires at least 30 distinct market days per strategy before Stage-2 target design is eligible.
- Official OKX documentation states tick-level historical trades are available from September 2021 and OHLC candlestick downloads from July 2023; the public API also documents historical candlesticks from recent years, while public history-trades is limited to the last three months.
- The approved Wave 002/003 Cash sample dates and future facts are immutable.

## Fixed coverage inputs

Wave 002:
2026-07-02, 07-03, 07-05, 07-07, 07-10, 07-12, 07-15, 07-17, 07-18, 07-21, 07-23, 07-25, 07-27, 07-31.

Wave 003:
2026-08-02, 08-04, 08-10, 08-12, 08-16, 08-21, 08-26, 08-28, 08-31, 09-06, 09-09, 09-14, 09-18, 09-20.

- Future: `BTC-USDT-260925`
- Spot control: `BTC-USDT`
- Entry clock: `00:15:00 UTC`
- Known expired-future control: `BTC-USDT-260626` around pinned June Cash dates where the endpoint supports it.

## Constraints

- Read-only public OKX APIs only.
- No sample replacement or outcome-driven date changes.
- No importer/backtest/qualification/target changes.
- Treat trade retention-window exclusions separately from endpoint/instrument absence.
- Record exact endpoint parameters, OKX code/message, sample count, min/max timestamps and target-window coverage.
- Network probe is diagnostic/non-gating; pure classification and summary logic is offline-tested.
- Do not infer a bulk-download module number for trade/candle data without official or captured evidence.

## Acceptance criteria

- [x] Exact 28 Wave 002/003 dates and approved future are versioned before probing.
- [x] Candlestick coverage evidence exists for future + spot controls.
- [x] Trade coverage evidence exists where the documented 3-month retention window applies.
- [x] Retention-window exclusions are not misclassified as missing instruments/data.
- [x] Expired-future control behavior is recorded.
- [x] Machine-readable Actions artifact has run/artifact identity.
- [x] Offline tests cover deterministic inputs and summary semantics.
- [x] Full PR CI and historical smoke pass.
- [x] Result clearly states whether an evidence-semantics decision is required.

## Implementation slices

- [x] 1. Open Issue #29 and create this main-based branch/plan.
- [x] 2. Add package-level deterministic input/coverage summary helpers.
- [x] 3. Add a read-only OKX alternate-history network probe and dedicated non-gating workflow.
- [x] 4. Add focused offline tests.
- [x] 5. Reconcile REST + bulk catalog evidence. REST expired-future APIs reject the approved/positive-control contracts; bulk modules 1/2/5 each have the June positive control but 0/28 pre-registered dates. Existing modules 4/6 are also 0/28.
- [x] 6. No alternate official evidence class materially recovers the 28 dates, so no evidence-semantics decision is required. Preserve the current L2 evidence contract and track publication-frontier diagnosis separately.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Offline coverage tests | `tests/test_cash_alternate_history.py` in CI 37603607706 | passed |
| Static/API/E2E | CI 37603607706 | passed |
| Historical smoke | 37603607999 | passed |
| REST coverage probe | run 37603034103 artifact 11473861175 | passed |
| Bulk catalog inventory | run 37603600279 artifact 11474390262 / sha256:0c0d729b5469d19e5fac5a51fd54c65b105d24a61f202aef853f58a865154c2f | passed |

## Decision gate

No decision is needed to run the probe.

No material evidence-semantics decision is required from this task.

Captured evidence shows **no alternate official source recovers the missing 28 dates**:
- module 1 trade archives: June positive control present, Wave dates 0/28;
- module 2 one-minute candlestick archives: June positive control present, Wave dates 0/28;
- module 5 5000-level L2: June positive control present, Wave dates 0/28;
- modules 4/6 L2 were already 0/28 under Issue #26;
- REST historical future candles/trades reject expired futures with OKX 51001, while spot controls work.

Therefore changing evidence fidelity cannot solve the current gap. Keep the existing L2 evidence contract. The next problem is source **publication availability/frontier**, not evidence semantics.

## Resume from here

All alternate-source evidence is reconciled. Archive this plan after final PR checks. Then merge PR #30, close Issue #29, and open a separate publication-frontier task to determine the latest date currently available in OKX bulk historical archives before designing any future Cash evidence wave.

## Evidence log

- 2026-10-07: OKX official docs confirm historical trade downloads from Sep 2021, candlestick downloads from Jul 2023, and separate L2 order-book downloads; REST `history-candles` covers recent years while `history-trades` documents a 3-month retention window.
- 2026-10-07: run 37603034103 artifact 11473861175 digest `sha256:46132a24b4cd1776c893ca72137f62a430390c26a16589e8b9c761bf884bc881`.
- REST summary: candles future = 28 API errors / 0 covered; candles spot = 28/28 target covered; trades future = 25 API errors + 3 retention-excluded; trades spot = 24 target covered + 1 no-data + 3 retention-excluded.
- Expired-future candlestick positive control `BTC-USDT-260626` on 2026-06-01 returns OKX code 51001 (`Instrument ID, Instrument ID code, or Spread ID doesn't exist.`), while the spot positive control returns code 0. This distinguishes expired-instrument addressability from endpoint/date availability.
- PR #30 initial Plan Integrity failure is plan-format-only: this plan lacked the required `## Verification matrix`; fixed here.
- 2026-10-07: bulk probe run 37603600279 artifact 11474390262 digest `sha256:0c0d729b5469d19e5fac5a51fd54c65b105d24a61f202aef853f58a865154c2f`.
- Bulk module 1: positive control=1 (`BTC-USDT-futureschain-trades-2026-06-01.zip`), pre-registered coverage=0/28.
- Bulk module 2: positive control=1 (`BTC-USDT-futureschain-candlesticks-2026-06-01.zip`), pre-registered coverage=0/28.
- Bulk module 5: positive control=1 (`BTC-USDT-futureschain-L2orderbook-5000lv-2026-06-01.tar.gz`), pre-registered coverage=0/28.
- Existing Issue #26 evidence already established module 4 and module 6 positive controls=5/5 and pre-registered coverage=0/28.
- Latest implementation PR CI 37603607706 and Historical Smoke 37603607999 both succeeded on commit 548f96cbc65aa70e0dd08f832dcf16b90eb5cb2b.
- Cross-source pattern is contiguous: known June FUTURES-chain archive controls are present while the selected July-September dates are absent across trade/candle/L2 classes. Treat this as a publication-availability hypothesis for the next task, not as proven permanent absence.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: alternate official source coverage and any resulting evidence-semantics decision
