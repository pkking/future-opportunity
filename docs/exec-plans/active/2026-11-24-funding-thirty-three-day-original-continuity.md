# Extend Option A Funding immutable original-source continuity to thirty-three days

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-11-24
Last checkpoint: 2026-11-24

## Objective

Expand the already validated 2026-10-23..2026-11-22 (thirty-one complete UTC source days; thirty adjacent pairs) to 2026-10-23..2026-11-24 (thirty-three complete UTC days, thirty-two adjacent pairs), after confirming the two new immutable releases and their independently successful `release.published` audits. Preserve existing original source provenance and frozen decision-quality limits.

## Non-goals

No exchange GETs beyond those already captured in immutable GitHub Releases, new schedule, historical backfill, independent witness, source promotion, pinned corpus growth, threshold change, economics gate, or real trading.

## Verified current facts

- main `4362a2e` (PR #174 archive merge), zero open PRs; [main CI #45054715692](https://github.com/pkking/future-opportunity/actions/runs/45054715692) SUCCESS.
- Previous authoritative 31-day read-only [source ZIP review #45053416810](https://github.com/pkking/future-opportunity/actions/runs/45053416810) SUCCESS: 31/31 original days, 30/30 consistent adjacent pairs, 0 numeric revisions and 0 unassessed, derived artifact ID `14766557435`. Regime inventory included the first two negative-Funding observations (2026-11-18, 2026-11-20).
- New immutable [11/23 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-11-23), published `2026-11-23T00:00:16Z` (before the 00:15 UTC cutoff), original-source.zip SHA256 `3a6d3989ee994ff9c4062b5e796683226770046499e30d51d9a683a2d89e448f`, independent [release.published audit #45086232373](https://github.com/pkking/future-opportunity/actions/runs/45086232373) SUCCESS.
- New immutable [11/24 Release](https://github.com/pkking/future-opportunity/releases/tag/funding-vps-2026-11-24), published `2026-11-24T00:00:16Z`, original-source.zip SHA256 `f9d3920a1a171e16900f512cb72a1ba1dadb184a44c4ce9efdb2b7d7a625fe4d`, independent [release.published audit #45293547841](https://github.com/pkking/future-opportunity/actions/runs/45293547841) SUCCESS.
- Read-only [watcher 11/23 #45136525132](https://github.com/pkking/future-opportunity/actions/runs/45136525132) and [watcher 11/24 #45374485860](https://github.com/pkking/future-opportunity/actions/runs/45374485860) SUCCESS.
- Separate best-effort GitHub scheduled pre-entry collectors [11/23 #45109074320](https://github.com/pkking/future-opportunity/actions/runs/45109074320) and [11/24 #45345261428](https://github.com/pkking/future-opportunity/actions/runs/45345261428) failed their hard 00:15 UTC clock gate as designed; not a VPS source chain incident, never backfilled.
- **New 11/22→23 and 11/23→24 adjacent pair numerical consistency is UNASSESSED until the real postmerge GitHub-only replay.** Watcher health and release metadata do not establish overlap consistency.

## Required sources

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md
- docs/agents/workflow.md, docs/agents/testing.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py

## Constraints

- Only read original immutable GitHub ZIPs with matching successful independent release event audit and source SHA256 per day; fail closed on any missing original, audit, API completeness, numerical revision or invalid historical confirmation.
- Preserve workflow_dispatch manual exact 2..90 completed UTC date scope, workflow-file-only one-shot main-push trigger, no cron, GitHub read-only permissions and no source writes. Every request stays authenticated (PR #173), paced and bounded-retried (PRs #170/#172), with immutable asset-download dedupe (PR #171): a 33-day review issues ~66 authenticated tag calls and ~66 asset downloads, well inside the token's 5000/hour core quota; the previous 31-day authoritative run completed cleanly.
- Preserve frozen Funding sign / spot trailing 100bps volatility 2×2, no market-wide opportunity arrival claims.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`, Funding pinned 32/90, Cash 66; no Stage-2 economic gate or trade.

## Acceptance criteria

- [ ] Extend one-shot workflow main-push default to `2026-10-23..2026-11-24` inclusive (33 original days, 32 adjacent pairs).
- [ ] Offline regression test enforces exact 33 days, 32 pairs and unchanged manual read-only/safety constraints.
- [ ] Exact final PR head has all 5 required CI checks plus Historical Smoke SUCCESS.
- [ ] After merge, the workflow-file push triggers the real main-push GitHub original ZIP report; confirm all 33 day statuses and 32 adjacent comparison states; report exact pair populations, numerical/confirmation revision findings, unassessed count and original/derived SHA256; do not assume consistency ahead of time.
- [ ] Record audited outcome in Issue #85, then archive evidence and update parent plan in a separate completion-only PR; parent Issue remains open.

## Implementation slices

- [ ] 1. Modify workflow bounded default date only.
- [ ] 2. Modify exact-date governance regression test.
- [ ] 3. PR, final-head CI/Historical Smoke, merge if authorized, verify real 33-day source report.
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

- 2026-11-24: Confirmed 33 consecutive immutable `funding-vps-*` Releases 2026-10-23..2026-11-24 via GitHub API; both new-day independent release audits SUCCESS (run IDs above); new ZIP SHA256s computed from downloaded originals; main CI green on `4362a2e`; zero open PRs. New adjacent-pair overlap consistency remains unassessed.

## Deviations and discoveries

None yet.

## Resume from here

Implementing: change `.github/workflows/review-funding-source-continuity.yml` default `END_DATE` and header comment to 2026-11-24, update `tests/test_funding_source_continuity.py` governance test to thirty-three days / thirty-two pairs, run offline tests and ruff, then open the PR with `Issue: #85` and this plan as `Plan:`.

## Completion

In progress.
