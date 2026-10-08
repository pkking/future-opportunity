# 2026-10-09-funding-raw-regime-source-evidence

Issue: #67
Status: IMPLEMENTING
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

- [ ] Deterministic pure transform validates funding and spot API payload schemas and produces reproducible feature rows and explicit missing dates.
- [ ] Source digest and per-day hashes bind raw input and derived features.
- [ ] Lag and 7-day completed spot-candle window are enforced.
- [ ] Duplicate/conflicting source records, bad decimals, stale funding and incomplete candles are rejected or missing, never silently substituted.
- [ ] Research output remains source-authentication-pending and acquisition/promotion disabled.
- [ ] Read-only GitHub Action captures a fixed recent study window and uploads raw+features+research evidence.
- [ ] Tests cover successful reconstruction, no-lookahead, missingness, duplicates and digest changes.
- [ ] Required CI 5/5 and Historical Smoke green on review head.
- [ ] Archive execution plan, update PR body, and verify final-head required CI and Smoke before merge.
- [ ] Merge and verify main; close issue only after success.

## Implementation slices

- [x] 1. Inspect current 2x2 research, official API semantics and current repo work.
- [x] 2. Create Issue #67, branch, active plan.
- [ ] 3. Implement deterministic raw-input feature reconstruction with explicit limitations.
- [ ] 4. Implement bounded official API capture with immutable evidence and research-only workflow.
- [ ] 5. Add tests and technical handoff documentation.
- [ ] 6. PR CI/Smoke, archival head verification, merge, main validation and issue closure.

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
| CI / Smoke | pending |

## Resume from here

Implement pure reconstruct-and-audit from archived OKX API response bodies (never trust client-provided derived features), then add a read-only capture workflow and synthetic tests. Keep explicit retrospective/source-authentication limitations. Open a governed PR, merge only when the final head has 5/5 required checks and Historical Smoke; verify main and close issue.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: implementation, live source availability and CI
