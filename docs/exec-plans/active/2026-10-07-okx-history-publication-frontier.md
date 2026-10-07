# 2026-10-07-okx-history-publication-frontier: Measure OKX historical publication frontier

Issue: #31
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Measure the latest currently available OKX BTC-USDT FUTURES-chain bulk historical archive date for modules 1/2/4/5/6, and determine whether the observed missing July-September Cash dates are consistent with a publication frontier rather than isolated gaps.

## Current facts

- Issues #26/#29 proved June FUTURES-chain positive controls exist across trade/candle/L2 classes while all 28 Wave 002/003 July-September dates are absent.
- PR #30 merged as `598a2d84873a0629a2940f5f37b2fea16c756d5a`.
- REST historical market endpoints reject expired FUTURES instrument IDs with OKX 51001; bulk catalog is therefore the authoritative path for this frontier measurement.
- Official OKX API changelog states the historical-market-data query maximum is 10 daily dates per request as of 2026-08-06.
- Official OKX candlestick download help says candlestick data is downloadable two days after each day ends, but no equivalent publication SLA has yet been found for FUTURES-chain bulk archives.
- No Wave 002/003 date may be replaced.

## Constraints and invariants

- Official OKX public historical catalog only.
- Query chunks must be deterministic and no larger than 10 days.
- Fixed scan start: 2026-06-01.
- Fixed scan end for this run: 2026-10-06 (last fully completed UTC day before task date).
- Modules: 1 trade, 2 one-minute candle, 4 400-level L2, 5 5000-level L2, 6 50-level L2.
- Derive available dates from returned `dataTs/dateTs` and filename metadata; do not infer availability from HTTP success alone.
- Network diagnostic is non-gating.
- No sampler/importer/backtest/economics changes in this task.

## Acceptance criteria

- [x] Fixed scan interval and module set are versioned before probe.
- [ ] Deterministic <=10-day range chunking is offline-tested.
- [ ] Full range inventory is captured as machine-readable Actions evidence.
- [ ] Each module summary reports first/latest available date and lag from probe date.
- [ ] Internal gaps inside first..latest coverage are explicitly reported.
- [ ] Cross-module frontier agreement/disagreement is reported.
- [ ] Full PR CI and Historical Smoke pass.
- [ ] Existing Wave 002/003 samples remain untouched.
- [ ] Result states whether a new study-design decision is required.

## Implementation slices

- [x] 1. Open Issue #31 and create this branch/plan.
- [ ] 2. Add pure frontier/chunk/summary helpers.
- [ ] 3. Add bounded non-gating network probe/workflow.
- [ ] 4. Add focused offline tests.
- [ ] 5. Run probe and reconcile publication-frontier evidence.
- [ ] 6. Archive/merge if no implementation decision remains; stop only if source coverage is irregular enough that a lag rule would be unsafe.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | frontier helper tests | pending |
| Static/API/E2E | PR Ruleset | pending |
| Historical smoke | PR workflow | pending |
| Frontier probe | non-gating Actions artifact | pending |

## Decision gates

No decision is needed to measure the source frontier.

A study-design decision becomes necessary only after evidence establishes a safe historical-source eligibility boundary. This task must not select future Wave dates itself.

## Evidence log

- 2026-10-07: Issue #31 opened after #29/PR #30 established zero alternate-source coverage for all 28 Wave dates.
- 2026-10-07: branch `agent/measure-okx-history-frontier` created from main 598a2d84873a0629a2940f5f37b2fea16c756d5a.

## Deviations and discoveries

None yet.

## Resume from here

Implement deterministic 10-day chunking and pure frontier summarization, then wire a non-gating catalog probe over 2026-06-01..2026-10-06 for modules 1/2/4/5/6.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: publication frontier and future Cash sampling eligibility
