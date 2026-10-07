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
- [x] Deterministic <=10-day range chunking is offline-tested.
- [x] Full range inventory is captured as machine-readable Actions evidence.
- [x] Each module summary reports first/latest available date and lag from probe date.
- [x] Internal gaps inside first..latest coverage are explicitly reported.
- [x] Cross-module frontier agreement/disagreement is reported.
- [x] Full PR CI and Historical Smoke pass.
- [x] Existing Wave 002/003 samples remain untouched.
- [x] Result states whether a new study-design decision is required.

## Implementation slices

- [x] 1. Open Issue #31 and create this branch/plan.
- [x] 2. Add pure frontier/chunk/summary helpers.
- [x] 3. Add bounded non-gating network probe/workflow.
- [x] 4. Add focused offline tests.
- [x] 5. Probe run 37604606262 completed. All five modules have the same contiguous frontier: 2026-06-01..2026-06-26, 26 available dates, zero internal gaps, latest_age_days=103.
- [x] 6. Source coverage is frontier-like and cross-module consistent. Archive/merge this measurement; leave exact future study/execution timing as the next explicit decision.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Unit | `tests/test_history_publication_frontier.py` in CI 37604660667 | passed |
| Static/API/E2E | CI 37604660667 (success) | passed |
| Historical smoke | 37604660888 | passed |
| Frontier probe | run 37604606262 artifact 11474327068 / sha256:8c9d1a6575c6ac8d6065c843be4b8d97351ca76a0d1f40dfcbc86950d93ebc0c | passed |

## Decision gates

No decision is needed to measure the source frontier.

The source constraint is now established: as of probe date 2026-10-07, all five tested BTC-USDT FUTURES-chain historical modules have a contiguous daily archive frontier ending on **2026-06-26**, with no internal gaps from 2026-06-01.

A study/execution decision is required next, but the preferred path is **not to resample**. The already-approved Wave 002/003 dates remain fixed. Because their exclusions were caused by source availability, the methodologically cleaner next step is to monitor for the next quarterly archive frontier (expected to include the BTC-USDT-260925 period if/when OKX publishes it), then retry acquisition for the exact same pre-registered dates. Any decision to abandon those dates and design Wave 004 would require explicit operator approval.

## Evidence log

- 2026-10-07: Issue #31 opened after #29/PR #30 established zero alternate-source coverage for all 28 Wave dates.
- 2026-10-07: branch `agent/measure-okx-history-frontier` created from main 598a2d84873a0629a2940f5f37b2fea16c756d5a.
- 2026-10-07: pure 10-day chunk/frontier helpers and offline tests added.
- 2026-10-07: non-gating probe run 37604606262 started from workflow commit 42e7ed3f35d4cd1c38f5394222f9c1a01d03983e.
- 2026-10-07: probe run 37604606262 artifact 11474327068 digest `sha256:8c9d1a6575c6ac8d6065c843be4b8d97351ca76a0d1f40dfcbc86950d93ebc0c`.
- Modules 1/2/4/5/6 each report: available_count=26, first=2026-06-01, latest=2026-06-26, latest_age_days=103, internal_gap_count=0, frontier_contiguous=true.
- Cross-module summary: frontier_agreement=true and all_modules_contiguous=true.
- The exact common frontier date 2026-06-26 matches the expiry of the previously pinned `BTC-USDT-260626` quarterly future. This supports a quarterly-publication hypothesis, but the repository records it only as a hypothesis until a later frontier transition is observed.
- PR #32 CI 37604660667 and Historical Smoke 37604660888 passed.

## Deviations and discoveries

- The missing July-September evidence is not irregular within the scanned source interval; all five modules stop at the same clean frontier.
- Official OKX help documents a 2-day download delay for candlesticks, which is insufficient to explain the observed 103-day FUTURES-chain frontier. Therefore a generic T+2 rule must not be applied to FUTURES-chain archives.
- The 2026-06-26 frontier aligns with quarterly expiry, so source readiness should be monitored by actual catalog evidence rather than a guessed day-lag constant.

## Resume from here

Frontier evidence is reconciled. Archive this plan and merge PR #32 after final completion-plan checks. Then create a source-readiness monitor for the exact Wave 002/003 dates / BTC-USDT-260925 chain; do not resample or dispatch a new wave without an explicit study-design decision.

## Completion

Final commit: d7c441bdbb3c72097ea4ffc6e1cdbf936cbf84d9
CI run: https://github.com/pkking/future-opportunity/actions/runs/37604660667
E2E artifact: strategy E2E evidence from CI run 37604660667
Frontier probe: https://github.com/pkking/future-opportunity/actions/runs/37604606262
Frontier artifact: 11474327068 / sha256:8c9d1a6575c6ac8d6065c843be4b8d97351ca76a0d1f40dfcbc86950d93ebc0c
Historical smoke: https://github.com/pkking/future-opportunity/actions/runs/37604660888
Remaining unassessed items: when OKX publishes the BTC-USDT-260925/Q3 FUTURES-chain archives; whether to retry exact Wave 002/003 acquisition then or explicitly design a new study wave
