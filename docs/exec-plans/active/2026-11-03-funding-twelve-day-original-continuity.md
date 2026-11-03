# Extend Option A Funding immutable original-source continuity to twelve days

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-11-03
Last checkpoint: 2026-11-03

## Objective

Expand the already validated 2026-10-23..2026-11-01 (ten complete UTC source days; nine adjacent pairs) to 2026-10-23..2026-11-03 (twelve complete UTC days, eleven adjacent pairs), after confirming two new immutable releases and independently successful release.published audits. Preserve existing original source provenance and frozen decision-quality limits.

## Non-goals

No exchange GETs beyond those already captured in immutable GitHub Releases, new schedule, historical backfill, independent witness, source promotion, pinned corpus growth, threshold change, economics gate, or real trading.

## Verified current facts

- main `f68557e9f410592d5c31cc791ac7c660fe95e29a`, zero open PRs; [main CI #41320963255](https://github.com/pkking/future-opportunity/actions/runs/41320963255) SUCCESS.
- Previous actual read-only [10-day source ZIP review #41320703277](https://github.com/pkking/future-opportunity/actions/runs/41320703277) SUCCESS: 10/10 original days, 9/9 consistent adjacent pairs, 0 numeric revisions and 0 unassessed, derived artifact SHA256 `aee7b535b305927033138e33aab1fc1e2536c1d668dd73e26771fdc57a645f27`.
- New immutable [11/02 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-11-02), published `2026-11-02T00:00:15Z`, original-source.zip SHA256 `de652a639e81ea3c96f13caa0a2e10a83d5e3ea33a1c77ff9f05e0984d993aa1`, independent [release.published audit #41364823950](https://github.com/pkking/future-opportunity/actions/runs/41364823950) SUCCESS.
- New immutable [11/03 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-11-03), published `2026-11-03T00:00:16Z`, original-source.zip SHA256 `cae70a1453747f2e976b8c04901e4a17d19fbc721c76404764eafb6e96cfd0ba`, independent [release.published audit #41549637333](https://github.com/pkking/future-opportunity/actions/runs/41549637333) SUCCESS.
- Read-only [watcher 11/02 #41402172730](https://github.com/pkking/future-opportunity/actions/runs/41402172730) and [watcher 11/03 #41594886226](https://github.com/pkking/future-opportunity/actions/runs/41594886226) SUCCESS, both nonnegative Funding/high 100bps volatility; no observed samples in three other strata.
- Separate best-effort GitHub scheduled pre-entry collectors [11/02 #41379260511](https://github.com/pkking/future-opportunity/actions/runs/41379260511) and [11/03 #41575495262](https://github.com/pkking/future-opportunity/actions/runs/41575495262) started after UTC 00:15 and failed closed, not a VPS source chain incident.
- **New 11/01→02 and 11/02→03 adjacent pair numerical consistency is UNASSESSED until real postmerge replay.**

## Required sources

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md
- docs/agents/workflow.md, docs/agents/testing.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py

## Constraints

- Only read original immutable GitHub ZIPs with matching successful independent release event audit and source SHA256 per day; fail closed on any missing original, audit, API completeness, numerical revision or invalid historical confirmation.
- Preserve workflow_dispatch manual exact 2..90 completed UTC date scope, workflow-file-only one-shot main-push trigger, no cron, GitHub read-only permissions and no source writes.
- Preserve frozen Funding sign / spot trailing 100bps volatility 2×2, no market-wide opportunity arrival claims.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`, Funding pinned 32/90, Cash 66; no Stage-2 economic gate or trade.

## Acceptance criteria

- [ ] Extend one-shot workflow main-push default to `2026-10-23..2026-11-03` inclusive (12 original days, 11 adjacent pairs).
- [ ] Offline regression test enforces exact 12 days, 11 pairs and unchanged manual read-only/safety constraints.
- [ ] Exact final PR head has all 5 required CI checks plus Historical Smoke SUCCESS.
- [ ] After merge, actual main-push GitHub original ZIP report confirms all 12 day statuses and 11 adjacent comparison states; report exact pair populations, numerical/confirmation revision findings, unassessed count and original/derived SHA256; do not assume consistency ahead of time.
- [ ] Record audited outcome in Issue #85, then archive evidence and update parent plan in a separate completion-only PR; parent Issue remains open.

## Slices

- [ ] 1. Modify workflow bounded default date only.
- [ ] 2. Modify exact-date governance regression test.
- [ ] 3. PR, final-head CI/Historical Smoke, merge if authorized, verify real 12-day source report.
- [ ] 4. Comment Issue #85 and archive in separately verified PR.

## Verification

| Gate | State |
|---|---|
| Final PR head 5 required CI checks | pending |
| Final PR head Historical Smoke | pending |
| Real source continuity main-push report | not triggered |
| Postmerge main CI | pending |

## Decision gates

None for bounded read-only Option A extension. New trust authorities, alternate witness, changed evidence admission, markets sampling schedule, historical promotion, economic/real-trade permission remain unapproved.

## Evidence log

- 2026-11-03: Rechecked immutable GH Releases, new release audit runs and daily watchers for 11/02-03. Verified scheduled GitHub collectors missed strict time guard. New original adjacency consistency remains unassessed.

## Deviations and discoveries

None at planning time.

## Resume from here

Change one-shot workflow end date and test on this branch, open PR, wait for exact HEAD CI and Historical Smoke, merge only if GitHub rules permit, inspect actual immutable original-source report and record evidence before archiving.

## Completion

Pending real postmerge original ZIP review and CI; no historical admission or economic/trading permission.
