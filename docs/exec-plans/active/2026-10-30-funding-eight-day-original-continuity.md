# Expand Option A immutable Funding source continuity to eight completed days

Issue: #85
Status: IMPLEMENTING
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

- [ ] One-shot workflow main-push default is 2026-10-23..30 inclusive; seven adjacent pairs; manual date inputs unchanged.
- [ ] Governance test enforces eight days/seven pairs and no schedule/write/data capture.
- [ ] Final PR head passes Static/Code/API/E2E/Plan Integrity and Historical Smoke.
- [ ] After verified merge, real main-push review audits all eight dates against exact original ZIPs and records seven pair statuses and counts plus derived artifact digest. No consistency claim before the run.
- [ ] Record verified completion and remaining uncertainty in parent Issue #85, archive child plan separately without closing parent.

## Implementation slices

- [ ] 1. Update workflow fixed window only.
- [ ] 2. Update deterministic no-network workflow test.
- [ ] 3. Submit PR, validate final head, merge under rules, inspect and record real eight-day results.
- [ ] 4. Archive child plan after evidence is verified.

## Verification matrix

| Gate | Scope | State |
|---|---|---|
| Static / Code / API / E2E / Plan Integrity | PR CI | pending |
| Historical Smoke | PR | pending |
| Actual GitHub-only continuity | workflow-file main push | not yet triggered |

## Decision gates

None for this bounded read-only reuse of existing approved Option A. Altering evidence admission, deploying inactive option B, new schedules or trades remains explicitly unapproved.

## Evidence log

- 2026-10-30: Read production GitHub Release and successful independent audit metadata, daily watcher logs and late GitHub scheduled collector failures for October 29/30; no claim about adjacent numeric overlaps.

## Deviations and discoveries

None.

## Resume from here

Change the bounded workflow default and offline test, create a PR, verify exact final-head CI/Historical Smoke, merge if permitted, and inspect the postmerge source continuity report before marking seven pairs consistent.

## Completion

Final commit: pending
CI run: pending
Real source artifact: pending
Remaining unassessed items: two new adjacent original-source comparisons, upstream first-publication authenticity, empty regimes, 32/90 Funding pinned, Cash 66.
