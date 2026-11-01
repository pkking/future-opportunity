# Option A: ten real immutable Funding original-source days

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-11-01
Last checkpoint: 2026-11-01

## Objective

Expand the existing one-shot GitHub-only source-continuity workflow from real 2026-10-23..30 (8 days / 7 adjacent comparisons) to real 2026-10-23..2026-11-01 (10 days / 9 comparisons), with separately published and successful independent GitHub release.published audits on 10/31 and 11/01. Preserve all earlier source and CI evidence.

## Non-goals

No exchange API fetches, manual triggering, new schedules, witness setup, changes to fixed market regimes, historical acquisition/promotion, strategy economics, or live trades. No claim about newly adjacent comparisons before genuine postmerge report.

## Must-read context

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md, docs/agents/workflow.md, docs/agents/testing.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py

## Current verified facts

- Default branch main SHA: `f4a6a95ce554079181736aff614b863d9347687a`; no open PRs. [Last main CI #41083394825](https://github.com/pkking/future-opportunity/actions/runs/41083394825) SUCCESS.
- [Prior 8-day real original-source report #41082946274](https://github.com/pkking/future-opportunity/actions/runs/41082946274) SUCCESS; 8/8 original days, 7/7 adjacent pairs consistent, no anomalies; prior artifact `12990182445`, SHA256 `bcda4c924684fa10a2fad4b018946d9fd0727ecf7a22b4839e6be8b418ca4e6e`.
- New [2026-10-31 immutable Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-10-31), `published_at=2026-10-31T00:00:15Z`, original ZIP SHA256 `0c515d8335a46faa96dc3dcc885c54ff6a5295dbbb18f6b4c67f05493aed1d6c`; [independent release audit #41147720491](https://github.com/pkking/future-opportunity/actions/runs/41147720491) SUCCESS.
- New [2026-11-01 immutable Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-11-01), `published_at=2026-11-01T00:00:15Z`, original ZIP SHA256 `e432b3abd9c582ea43e66351b2226146c7fff91201920091c1f4275ac781429e`; [independent release audit #41254820044](https://github.com/pkking/future-opportunity/actions/runs/41254820044) SUCCESS.
- [Rolling watcher #41175874361](https://github.com/pkking/future-opportunity/actions/runs/41175874361) and [#41282320606](https://github.com/pkking/future-opportunity/actions/runs/41282320606) both SUCCESS, new daily regime `nonnegative_high_volatility`. Separate best-effort GitHub cron launches at 02:42/02:32 UTC missed the hard 00:15 UTC gate and failed closed; they do not disprove VPS immutable releases.
- **10/30→10/31 and 10/31→11/01 adjacent raw source consistency is UNASSESSED until real postmerge original ZIP comparison.**

## Constraints and invariants

- Change only immutable GitHub originals single-shot read-only workflow default end date and exact governance test.
- Preserve strictly consecutive UTC dates, manual 2..90 day parameters, workflow-file-only main push trigger, GitHub actions:read/contents:read, no cron or source writes.
- Require successful independent release.published audit and SHA256-matched original ZIP for every source day, fail closed on any missing source, numeric revision or historic candle confirmation.
- Frozen Funding sign × 100bps spot-vol 2×2 regime inventory, zero inference about market-wide opportunities.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`; no Stage-2 economics enablement or trading.

## Acceptance criteria

- [x] One-shot workflow defaults to 2026-10-23..2026-11-01 inclusive and compares exactly 9 adjacent pairs; existing explicit manual dates unchanged.
- [x] Strict offline workflow regression test reflects 10 real days, 9 comparisons, no cron/write/market capture.
- [x] Final PR head has five required CI checks and Historical Smoke SUCCESS.
- [x] After merge inspect true main-push eight→ten-day original-source report with exact 10 hashes, 9 pair statuses, numeric/confirmation revision counts, immutable derived artifact and provenance limitations.
- [x] Completion-only archival PR captures actual CI and derived evidence; parent Issue #85 stays open.

## Implementation slices

- [x] 1. Update workflow exact fixed observation dates.
- [x] 2. Update deterministic no-network governance regression test.
- [x] 3. Submit PR, verify exact-head CI and Smoke; merge under rules and inspect the actual independent source report.
- [x] 4. Publish source evidence to Issue #85; archive plan in a separate documentation-only PR with own validation.

## Verification matrix

| Gate | Scope | State |
|---|---|---|
| Static / Code / API / E2E / Agent Plan | PR CI | 5/5 SUCCESS, run #41320638371 |
| Historical Smoke | PR | SUCCESS, run #41320638403 |
| Actual immutable original ZIP continuity | workflow-file main push | SUCCESS, run #41320703277, 10/10 days and 9/9 consistent pairs |

## Decision gates

None for read-only Option A. Source promotion, any new external witness/schedule or trade remains a separate unapproved material decision.

## Evidence log

- 2026-11-01: Confirmed 10/31 and 11/01 immutable GitHub Release and independently successful audit runs; read-only watchers SUCCESS. New adjacent-value consistency remains UNASSESSED.

## Deviations and discoveries

No new trusted first-publication evidence or market regimes. GitHub best-effort collector was late but the separate VPS→immutable Release→independent audit chain succeeded, as verified by the main-push original ZIP review.

## Resume from here

Completed and archived. Resume future Option A evidence collection from the parent Issue #85 active plan; do not repeat the same ten original UTC days merely to produce artifacts.

## Completion

Final commit: `0bbbe3841ac34038921ea0d1887cfd3474f891e3` (PR #165 squash merge)
CI run: [#41320638371](https://github.com/pkking/future-opportunity/actions/runs/41320638371) 5/5 required checks SUCCESS at final PR HEAD `e6a9133817ac08cc2c27b4dce3e264b8b9a9b904`; [Historical Smoke #41320638403](https://github.com/pkking/future-opportunity/actions/runs/41320638403) SUCCESS; [postmerge main CI #41320703148](https://github.com/pkking/future-opportunity/actions/runs/41320703148) SUCCESS
Real-source report: [main-push #41320703277](https://github.com/pkking/future-opportunity/actions/runs/41320703277) SUCCESS, derived artifact ID `13089366753`, ZIP SHA256 `aee7b535b305927033138e33aab1fc1e2536c1d668dd73e26771fdc57a645f27`
Remaining unassessed items: independent OKX first-publication proof, three unobserved prospective source regimes, Funding pinned 32/90 and Cash pinned 66; no historical source admission, Stage-2 economics or trading.


## 2026-11-01: true immutable original-source evidence

Actual independent original ZIP replay [#41320703277](https://github.com/pkking/future-opportunity/actions/runs/41320703277) compared ten strictly consecutive complete UTC source dates 2026-10-23..2026-11-01, requiring matching successful release.published audit and SHA256-verified original bytes for each. Outcome `OVERLAP_VALUES_CONSISTENT_ONLY`: `checked_day_count=10`, `github_audited_day_count=10`, `expected_pair_count=9`, `consistent_pair_count=9`, `revision_pair_count=0`, `unassessed_pair_count=0`, `every_adjacent_pair_assessed=true`. Every pair had exactly one valid current-day daily candle `confirm=0→1`, zero unexpected historical confirmation advances or regressions and zero revised settled Funding/previously confirmed spot closes.

| UTC adjacent pair | Common settled Funding observations | Numeric revisions | Status |
|---|---:|---:|---|
| 10/23→24 | 284 | 0 | CONSISTENT |
| 10/24→25 | 286 | 0 | CONSISTENT |
| 10/25→26 | 290 | 0 | CONSISTENT |
| 10/26→27 | 293 | 0 | CONSISTENT |
| 10/27→28 | 275 | 0 | CONSISTENT |
| 10/28→29 | 277 | 0 | CONSISTENT |
| 10/29→30 | 281 | 0 | CONSISTENT |
| 10/30→31 | 284 | 0 | CONSISTENT |
| 10/31→11/01 | 287 | 0 | CONSISTENT |

New genuine immutable Release original ZIP SHA256: 2026-10-31 `0c515d8335a46faa96dc3dcc885c54ff6a5295dbbb18f6b4c67f05493aed1d6c`; 2026-11-01 `e432b3abd9c582ea43e66351b2226146c7fff91201920091c1f4275ac781429e`. All ten days were `nonnegative_high_volatility` under unchanged fixed sign / 100bps split; other three strata = 0. This is GitHub custody of original VPS-supplied bytes and stable overlapping source values, **not independently signed OKX first publication**. `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`. No economics gate or trading.
