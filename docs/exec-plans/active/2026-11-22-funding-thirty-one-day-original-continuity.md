# Extend Option A Funding immutable original-source continuity to thirty-one days

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-11-22
Last checkpoint: 2026-11-22

## Objective

Expand the already validated 2026-10-23..2026-11-03 (twelve complete UTC source days; eleven adjacent pairs) to 2026-10-23..2026-11-22 (thirty-one complete UTC days, thirty adjacent pairs), after confirming all nineteen new immutable releases and their independently successful `release.published` audits. Preserve existing original source provenance and frozen decision-quality limits.

## Non-goals

No exchange GETs beyond those already captured in immutable GitHub Releases, new schedule, historical backfill, independent witness, source promotion, pinned corpus growth, threshold change, economics gate, or real trading.

## Verified current facts

- main `dbe197d1b3f0d996b2176020cbbb8ab419cf1dde`, zero open PRs; [main CI #41684697537](https://github.com/pkking/future-opportunity/actions/runs/41684697537) SUCCESS.
- Previous actual read-only [12-day source ZIP review #41684148969](https://github.com/pkking/future-opportunity/actions/runs/41684148969) SUCCESS: 12/12 original days, 11/11 consistent adjacent pairs, 0 numeric revisions and 0 unassessed, derived artifact ZIP SHA256 `cef985c80d872bf7b67ead53272d3aa485fa5176cd88e6264c7516ab95d7f4d0`.
- Nineteen new immutable `funding-vps-YYYY-MM-DD` Releases exist for 2026-11-04..2026-11-22, every one with an independently successful `release.published` audit run (all SUCCESS):

| UTC day | Independent audit run | UTC day | Independent audit run |
|---|---|---|---|
| 2026-11-04 | [#41743508734](https://github.com/pkking/future-opportunity/actions/runs/41743508734) | 2026-11-14 | [#43531169666](https://github.com/pkking/future-opportunity/actions/runs/43531169666) |
| 2026-11-05 | [#41938041264](https://github.com/pkking/future-opportunity/actions/runs/41938041264) | 2026-11-15 | [#43655997882](https://github.com/pkking/future-opportunity/actions/runs/43655997882) |
| 2026-11-06 | [#42133588827](https://github.com/pkking/future-opportunity/actions/runs/42133588827) | 2026-11-16 | [#43777812411](https://github.com/pkking/future-opportunity/actions/runs/43777812411) |
| 2026-11-07 | [#42315488987](https://github.com/pkking/future-opportunity/actions/runs/42315488987) | 2026-11-17 | [#43984025723](https://github.com/pkking/future-opportunity/actions/runs/43984025723) |
| 2026-11-08 | [#42427751239](https://github.com/pkking/future-opportunity/actions/runs/42427751239) | 2026-11-18 | [#44204176696](https://github.com/pkking/future-opportunity/actions/runs/44204176696) |
| 2026-11-09 | [#42537850372](https://github.com/pkking/future-opportunity/actions/runs/42537850372) | 2026-11-19 | [#44425431757](https://github.com/pkking/future-opportunity/actions/runs/44425431757) |
| 2026-11-10 | [#42724912641](https://github.com/pkking/future-opportunity/actions/runs/42724912641) | 2026-11-20 | [#44642262760](https://github.com/pkking/future-opportunity/actions/runs/44642262760) |
| 2026-11-11 | [#42927878277](https://github.com/pkking/future-opportunity/actions/runs/42927878277) | 2026-11-21 | [#44840823881](https://github.com/pkking/future-opportunity/actions/runs/44840823881) |
| 2026-11-12 | [#43124050561](https://github.com/pkking/future-opportunity/actions/runs/43124050561) | 2026-11-22 | [#44964483532](https://github.com/pkking/future-opportunity/actions/runs/44964483532) |
| 2026-11-13 | [#43333500220](https://github.com/pkking/future-opportunity/actions/runs/43333500220) | | |

- Read-only watcher runs [#44881323311](https://github.com/pkking/future-opportunity/actions/runs/44881323311) (11-21) and [#44998176251](https://github.com/pkking/future-opportunity/actions/runs/44998176251) (11-22) SUCCESS and re-verified their rolling three-day windows; the isolated 11-20 watcher [#44697120922](https://github.com/pkking/future-opportunity/actions/runs/44697120922) failed fast (~1.5s, transient GitHub API access failure before any report), the same failure class as the previously classified [2026-10-26 watcher 403](https://github.com/pkking/future-opportunity/actions/runs/40273247940); it is a watcher-only incident, not a missing immutable Release, and the 11-20 Release plus its independent audit #44642262760 succeeded.
- Separate best-effort GitHub scheduled pre-entry collectors keep failing their hard 00:15 UTC clock gate (latest [#44980760730](https://github.com/pkking/future-opportunity/actions/runs/44980760730)); not a VPS source chain incident, never backfilled.
- **All nineteen new adjacent pairs 11/03→04 .. 11/21→22 remain UNASSESSED until the real postmerge GitHub-only replay.** Watcher health and release metadata do not establish numeric overlap consistency.

## Required sources

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md
- docs/agents/workflow.md, docs/agents/testing.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py

## Constraints

- Only read original immutable GitHub ZIPs with matching successful independent release event audit and source SHA256 per day; fail closed on any missing original, audit, API completeness, numerical revision or invalid historical confirmation.
- Preserve workflow_dispatch manual exact 2..90 completed UTC date scope, workflow-file-only one-shot main-push trigger, no cron, GitHub read-only permissions and no source writes. The previous 12-day main-push review job completed in 27 seconds; thirty-one days stay far inside the existing 25-minute timeout, so no timeout change is required.
- Preserve frozen Funding sign / spot trailing 100bps volatility 2×2, no market-wide opportunity arrival claims.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`, Funding pinned 32/90, Cash 66; no Stage-2 economic gate or trade.

## Acceptance criteria

- [ ] Extend one-shot workflow main-push default to `2026-10-23..2026-11-22` inclusive (31 original days, 30 adjacent pairs).
- [ ] Offline regression test enforces exact 31 days, 30 pairs and unchanged manual read-only/safety constraints.
- [ ] Exact final PR head has all 5 required CI checks plus Historical Smoke SUCCESS.
- [ ] After merge, actual main-push GitHub original ZIP report confirms all 31 day statuses and 30 adjacent comparison states; report exact pair populations, numerical/confirmation revision findings, unassessed count and original/derived SHA256; do not assume consistency ahead of time.
- [ ] Record audited outcome in Issue #85, then archive evidence and update parent plan in a separate completion-only PR; parent Issue remains open.

## Implementation slices

- [ ] 1. Modify workflow bounded default date only.
- [ ] 2. Modify exact-date governance regression test.
- [ ] 3. PR, final-head CI/Historical Smoke, merge if authorized, verify real 31-day source report.
- [ ] 4. Comment Issue #85 and archive in separately verified PR.

## Verification matrix

| Gate | State |
|---|---|
| Final PR head 5 required CI checks | pending |
| Final PR head Historical Smoke | pending |
| Real source continuity main-push report | not triggered |
| Postmerge main CI | pending |

## Decision gates

None for bounded read-only Option A extension. New trust authorities, alternate witness, changed evidence admission, markets sampling schedule, historical promotion, economic/real-trade permission remain unapproved.

## Evidence log

- 2026-11-22: Confirmed 31 consecutive immutable `funding-vps-*` Releases 2026-10-23..2026-11-22 via GitHub API; all 19 new-day independent release audits SUCCESS; main CI green on `dbe197d1b3f0d996b2176020cbbb8ab419cf1dde`; zero open PRs. Classified 11-20 watcher failure as transient watcher-only API incident (re-verified by 11-21/11-22 successful watchers). New adjacent-pair overlap consistency remains unassessed.

## Deviations and discoveries

None yet.

## Resume from here

Implementing: change `.github/workflows/review-funding-source-continuity.yml` default `END_DATE` and header comment to 2026-11-22, update `tests/test_funding_source_continuity.py` governance test to thirty-one days / thirty pairs, run offline tests and ruff, then open the PR with `Issue: #85` and this plan as `Plan:`.

## Completion

In progress.
