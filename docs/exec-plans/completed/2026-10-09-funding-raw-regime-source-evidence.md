# 2026-10-09-funding-raw-regime-source-evidence

Issue: #67
Status: COMPLETED
Owner: agent
Started: 2026-10-09
Last checkpoint: 2026-10-09

## Objective

Provide a reproducible, read-only bridge from bounded official OKX funding settlement-history and confirmed UTC spot daily candles into Funding regime *research* features. Establish raw response hashes, timestamp and missingness evidence without making an acquisition-ready claim.

## Baseline

- Main: fe3e64af791168230356e3466e986cde12235c34.
- Funding pinned: 32 dates; 0 qualified; evidence-only Stage-2 authorized ADR-0008.
- Cash pinned: 30 dates; 2 expiry cohorts; additional 2025 Q3/Q4 12+12 wave manifests already committed, preparation needs explicit dispatch.
- Existing 2x2 regime research module: src/future_opportunity/backtest/funding_regime_research.py.
- Economic return gates disabled; historical gate provenance_and_semantics.
- OKX funding-rate-history historical public API is limited to approximately three months.

## Invariants

- No expected/realized return, qualified classification or fixture access may influence research selection.
- Funding uses settled historical realizedRate, not a later predicted fundingRate; require event at least 1h before 00:15 UTC entry to avoid 00:00 settlement race.
- Spot volatility uses exactly seven completed UTC-day close-to-close log returns from eight completed daily candles; never include an open candle.
- Missing source data, duplicate/conflicting records, and stale funding events fail closed or are marked missing; never become a zero-return observation.
- Record raw request/response payload hashes, exact event and candle dates, per-row source digest. No invented publication timestamp or source signature.
- Source capture is retrospective. A captured response hash alone is NOT independent source authenticity or proof of availability at historical entry time.
- Raw and research artifacts are read-only; no acquisition approval, promotion approval, pinned corpus change or economics threshold.
- Do not change any Cash 2025 selected dates or current Funding/Cash pinned fixtures.

## Acceptance criteria

- [x] Deterministic pure transform validates funding and spot API payload schemas and produces reproducible feature rows and explicit missing dates.
- [x] Source digest and per-day hashes bind raw input and derived features.
- [x] Lag and 7-day completed spot-candle window are enforced.
- [x] Duplicate/conflicting source records, bad decimals, stale funding and incomplete candles are rejected or missing, never silently substituted.
- [x] Research output remains source-authentication-pending and acquisition/promotion disabled.
- [x] Read-only GitHub Action captures a fixed recent study window and uploads raw+features+research evidence.
- [x] Tests cover successful reconstruction, no-lookahead, missingness, duplicates and digest changes.
- [x] Required CI 5/5 (37809269547) and Historical Smoke (37809269794) green on review head.
- [x] Archive execution plan; final-head CI/Smoke is a mandatory merge condition.
- [x] Merge/main verification specified as mandatory follow-up; Issue #67 stays open until completed.

## Implementation slices

- [x] 1. Inspect current 2x2 research, official API semantics and current repo work.
- [x] 2. Create Issue #67, branch, active plan.
- [x] 3. Implement deterministic raw-input feature reconstruction with explicit limitations.
- [x] 4. Implement bounded official API capture with immutable evidence and research-only workflow.
- [x] 5. Add tests and technical handoff documentation.
- [x] 6. PR review-head CI/Smoke successful and plan archived; final-head validation and main verification remain mandatory next gates.

## Verification matrix

| Gate | Expected |
|---|---|
| Fixed study window | 2026-09-15 through 2026-09-21 |
| Funding ID | BTC-USDT-SWAP |
| Spot ID / bar | BTC-USDT / 1Dutc confirmed |
| Lag | settled event >=1h before entry |
| Volatility | standard deviation of 7 completed UTC close-to-close log returns, decimal bps, no annualization |
| Regime threshold | unchanged research-only 100 bps |
| Source provenance | request/response SHA-256 + row digest |
| Report mode | research only |
| Acquisition/promotion approval | false |
| Existing pinned corpora | Funding 32 / Cash 30 unchanged |
| Stage-2 economics gate | disabled |
| CI / Smoke | review head: CI 37809269547 5/5 success; Smoke 37809269794 success |

## Resume from here

Initial source probe run 37808540222 downloaded 305 Funding and 100 SPOT daily rows but failed to reconstruct 7-day features because the local daily-candle open anchor incorrectly used 00:15. The corrected, same-date, outcome-blind run 37808770909 succeeded with 7/7 feature rows and no missing days. Its artifact ID is 11564166495 (sha256:41c75db5daefb07f9eea49033193f5cffb41483ccca47b34513ce62b46dcecf3); raw captured response canonical SHA 9a05ef96c8a0e780a2f8316d463612fc5b11e235958d4951b5ba85676fdbfda3. All seven rows are nonnegative/high-volatility; 2 selected, three regime cells retain explicit zero capacity and quota shortfalls. Acquisition and promotion remain disallowed. See docs/research/funding-raw-regime-source-lineage-7-days.md.

PR #68 passed review-head CI run 37809269547 (all five required checks) and Historical Smoke 37809269794. Update PR Plan reference to completed/2026-10-09-funding-raw-regime-source-evidence.md and remove this active plan. Require fresh final-head 5/5 CI plus Historical Smoke, then squash-merge only the verified head SHA. Verify main still has Funding 32 / Cash 30 pinned, unchanged decision-quality approvals and disabled economics before closing Issue #67.

## Completion

Final commit: 4944396841d472f17e44f8668b7679366582a819
CI run: 37809269547 (5/5 success); Historical Smoke 37809269794 (success)
Remaining unassessed items: final archival-head checks, merge and main verification; retrospective API capture is not independent historical publication-time authentication
