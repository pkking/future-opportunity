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
- [ ] Candlestick coverage evidence exists for future + spot controls.
- [ ] Trade coverage evidence exists where the documented 3-month retention window applies.
- [ ] Retention-window exclusions are not misclassified as missing instruments/data.
- [ ] Expired-future control behavior is recorded.
- [ ] Machine-readable Actions artifact has run/artifact identity.
- [ ] Offline tests cover deterministic inputs and summary semantics.
- [ ] Full PR CI and historical smoke pass.
- [ ] Result clearly states whether an evidence-semantics decision is required.

## Implementation slices

- [x] 1. Open Issue #29 and create this main-based branch/plan.
- [x] 2. Add package-level deterministic input/coverage summary helpers.
- [x] 3. Add a read-only OKX alternate-history network probe and dedicated non-gating workflow.
- [x] 4. Add focused offline tests.
- [~] 5. Probe run 37603034103 is executing the fixed 28-date matrix; reconcile its artifact when complete.
- [ ] 6. If lower-fidelity coverage is material, stop at operator decision; otherwise archive and close without changing evidence semantics.

## Decision gate

No decision is needed to run the probe.

A material operator decision is required only if official trade/candlestick evidence materially recovers dates unavailable in L2. Using those sources for Cash backtest execution prices/liquidity would change evidence fidelity relative to the current L2 contract and must be handled explicitly, likely via a new ADR.

## Resume from here

Probe run 37603034103 is in progress from commit 9384cbbbc9de7ac271fc09be75ddd0dc641652a5. Inspect its machine-readable report before any evidence-source decision. In parallel, open the implementation PR and run full repository gates. Do not modify any Cash preparation/importer path.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: alternate official source coverage and any resulting evidence-semantics decision
