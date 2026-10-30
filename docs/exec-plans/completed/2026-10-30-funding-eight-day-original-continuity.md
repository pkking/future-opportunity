# Expand Option A immutable Funding source continuity to eight completed days

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-30
Last checkpoint: 2026-10-30

## Objective

Include the newly published **2026-10-29 and 2026-10-30** original immutable GitHub Funding Releases in the existing verified 2026-10-23..28 chain. Recheck **eight consecutive UTC days, seven adjacent pairs**, preserving the six-day report as prior evidence and never treating a successful independent Release audit as proof that all adjacent values agree.

## Non-goals

No new market requests, webhook/publisher/witness infrastructure, schedule, historical case acquisition, corpus promotion, economic threshold, or live order. No retrospective evidence reclassified as authentic point-in-time OKX publication.

## Must-read context

- AGENTS.md, docs/agents/workflow.md, docs/agents/testing.md.
- docs/design-baseline-v0.1.md, docs/v0-implementation-status.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md.
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md.
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py.

## Current facts

- Latest main baseline `be8289caf8d58c9efb40e1eade86bf5f093f6d81`; no open PR; final main CI [#40734665349](https://github.com/pkking/future-opportunity/actions/runs/40734665349) SUCCESS.
- Existing actual six-day read-only replay [#40734065510](https://github.com/pkking/future-opportunity/actions/runs/40734065510) verified 6/6 originals and 5/5 adjacent pairs, with zero funding or previously confirmed spot-close numeric revisions. This is immutable prior evidence, not an ongoing scan.
- New [10/29 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-10-29) `published_at=2026-10-29T00:00:15Z`, original ZIP SHA256 `501fabe643f84e80585f1646637514b75b12f074d84b25995bb7f8c2d8263c9d`; corresponding independent [audit #40791148257](https://github.com/pkking/future-opportunity/actions/runs/40791148257) SUCCESS.
- New [10/30 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-10-30) `published_at=2026-10-30T00:00:16Z`, original ZIP SHA256 `41ae5e8fb95a86738b3cdf61f360c54e91dac7cdb703d2a91b6b445082b456aa`; corresponding independent [audit #40976858162](https://github.com/pkking/future-opportunity/actions/runs/40976858162) SUCCESS.
- Read-only daily watchers [#40829201158](https://github.com/pkking/future-opportunity/actions/runs/40829201158), [#41013961483](https://github.com/pkking/future-opportunity/actions/runs/41013961483) both SUCCESS and categorized 10/29 and 10/30 as `nonnegative_high_volatility`. The separate best-effort GitHub scheduled collectors failed their strict UTC 00:15 timing gate on both days (about 02:49/02:55 UTC); no evidence that independent VPS immutable Release failed.
- **New 28→29 and 29→30 raw-source overlap consistency is still UNASSESSED pending actual GitHub-only replay.**

## Constraints and invariants

- Only read original GitHub Release ZIPs and independent successful release.published audits; retain exact original ZIP digests and derived SHA256.
- Preserve manual 2..90 completed UTC day option and one-shot workflow-file-only main push. No added scheduled scan, writes, or live market GET.
- Detect missing/retrospective evidence, abnormal candle confirmations, numeric revisions and source unavailability instead of suppressing errors.
- Keep fixed 100bps and 2×2 sign/vol strata. No qualification or market-wide rate inference.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`.

## Acceptance criteria

- [x] One-shot workflow main-push default is 2026-10-23..30 inclusive; seven adjacent pairs; manual date inputs unchanged.
- [x] Governance test enforces eight days/seven pairs and no schedule/write/data capture.
- [x] Final PR head passes Static/Code/API/E2E/Plan Integrity and Historical Smoke.
- [x] After verified merge, real main-push review audits all eight dates against exact original ZIPs and records seven pair statuses and counts plus derived artifact digest. No consistency claim before the run.
- [x] Record verified completion and remaining uncertainty in parent Issue #85, archive child plan separately without closing parent.

## Implementation slices

- [x] 1. Update workflow fixed window only.
- [x] 2. Update deterministic no-network workflow test.
- [x] 3. Submit PR, validate final head, merge under rules, inspect and record real eight-day results.
- [x] 4. Archive child plan after evidence is verified.

## Verification matrix

| Gate | Scope | State |
|---|---|---|
| Static / Code / API / E2E / Plan Integrity | PR CI | five required jobs SUCCESS, run #41082819750 |
| Historical Smoke | PR | SUCCESS, run #41082820009 |
| Actual GitHub-only continuity | workflow-file main push | SUCCESS, run #41082946274; 8/8 originals and 7/7 consistent pairs |

## Decision gates

None for this bounded read-only reuse of existing approved Option A. Altering evidence admission, deploying inactive option B, new schedules or trades remains explicitly unapproved.

## Evidence log

- 2026-10-30: Read production GitHub Release and successful independent audit metadata, daily watcher logs and late GitHub scheduled collector failures for October 29/30; no claim about adjacent numeric overlaps.

## Deviations and discoveries

No new source values, timing, admission, governance, or promotion rules were changed. The work is a one-shot extension of the same existing read-only workflow; postmerge main CI and actual immutable-original review both passed.

## Resume from here

Completed and archived. Continue only from the parent Issue #85 Option A active plan for future genuinely published UTC source days; do not rerun these eight days only to produce another artifact.

## Completion

Final commit: `a0629fd650d656a83a5e343c2877ce69e2a32139` (PR #163 squash-merged)
CI run: [#41082819750](https://github.com/pkking/future-opportunity/actions/runs/41082819750) all five required jobs SUCCESS at final PR HEAD `fdd67b8a364023be9144870ca4eb70d1a89d53a9`; [Historical Smoke #41082820009](https://github.com/pkking/future-opportunity/actions/runs/41082820009) SUCCESS; [postmerge main CI #41082946281](https://github.com/pkking/future-opportunity/actions/runs/41082946281) SUCCESS
Real source artifact: [run #41082946274](https://github.com/pkking/future-opportunity/actions/runs/41082946274) SUCCESS, artifact ID `12990182445`, ZIP SHA256 `bcda4c924684fa10a2fad4b018946d9fd0727ecf7a22b4839e6be8b418ca4e6e`
Remaining unassessed items: independent OKX first-publication authentication, negative/low and other missing 2×2 regimes, 32/90 Funding pinned, 66 Cash pinned; market-wide opportunity arrival and Stage-2 economic/trading permissions remain unavailable.


## 2026-10-30 real original-source evidence checkpoint

Actual read-only postmerge GitHub Actions [#41082946274](https://github.com/pkking/future-opportunity/actions/runs/41082946274) independently reloaded exact original ZIPs for eight complete 2026-10-23..30 UTC entry days and validated matching successful release.published audits.

Status `OVERLAP_VALUES_CONSISTENT_ONLY`: `checked_day_count=8`, `github_audited_day_count=8`, `expected_pair_count=7`, `consistent_pair_count=7`, `revision_pair_count=0`, `unassessed_pair_count=0`, `every_adjacent_pair_assessed=true`. All seven pairs have one expected current-day `1Dutc confirm=0→1` transition, zero unexpected historical confirmation advances and regressions, zero revised settled Funding and previously confirmed spot closes.

| UTC adjacent pair | Shared settled Funding events | Numeric revisions | Result |
|---|---:|---:|---|
| 10/23→24 | 284 | 0 | CONSISTENT |
| 10/24→25 | 286 | 0 | CONSISTENT |
| 10/25→26 | 290 | 0 | CONSISTENT |
| 10/26→27 | 293 | 0 | CONSISTENT |
| 10/27→28 | 275 | 0 | CONSISTENT |
| 10/28→29 | 277 | 0 | CONSISTENT |
| 10/29→30 | 281 | 0 | CONSISTENT |

New SHA256 original ZIPs independently checked:
- 2026-10-29: `501fabe643f84e80585f1646637514b75b12f074d84b25995bb7f8c2d8263c9d`;
- 2026-10-30: `41ae5e8fb95a86738b3cdf61f360c54e91dac7cdb703d2a91b6b445082b456aa`.

Eight days of observed Funding/100bps volatility classification: `nonnegative_high_volatility=8`, all other three strata = 0. These are source-day observations, not market-wide opportunity arrivals or historical acquisition-eligible samples. Exchange-signed first publication remains not independently verified; `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`. No economic or trading approval.
