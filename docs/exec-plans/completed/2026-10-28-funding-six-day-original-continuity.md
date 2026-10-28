# Six real immutable Funding originals: 2026-10-23..28

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-28
Last checkpoint: 2026-10-28

## Objective

Expand the existing one-shot, read-only on-main-push original-source continuity diagnostic from three actually published Funding Release days (2026-10-23..25) to six (2026-10-23..28), comparing **all five consecutive UTC adjacent pairs**. Keep the separately recorded three-day evidence immutable. This PR itself changes only a bounded default and deterministic workflow tests; evidence cannot be accepted until an actual postmerge original-ZIP replay.

## Non-goals

No market API GET, third-party witness, new schedule, manual workflow trigger, Release publication, re-pinning historical days, corpus changes, economic thresholds, or trading. Do not claim source agreement before the real derived report is verified.

## Must-read context

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md.
- docs/adr/0008-funding-stage2-historical-distribution-gate.md.
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md.
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py and tests/test_funding_source_continuity.py.
- docs/agents/workflow.md and docs/agents/testing.md.

## Current verified facts

- Base main `81d5517520f1f8b68aa742c736c09b904cca54cb`. Existing PR #160 independently fixes the release watcher pagination, remains open; this slice does not depend on its merge.
- Existing source continuity run [40209332389](https://github.com/pkking/future-opportunity/actions/runs/40209332389) authenticated 2026-10-23..25 (2 pairs).
- New immutable GitHub Releases have tags `funding-vps-2026-10-26`, `funding-vps-2026-10-27`, `funding-vps-2026-10-28`, all published around 00:00 UTC and independently successful `release.published` audits [40247244298](https://github.com/pkking/future-opportunity/actions/runs/40247244298), [40423529334](https://github.com/pkking/future-opportunity/actions/runs/40423529334), [40605906514](https://github.com/pkking/future-opportunity/actions/runs/40605906514). **New original ZIP equality and cross-day continuity remain UNASSESSED until actual replay.**
- Oct 26 read-only release watcher [40273247940](https://github.com/pkking/future-opportunity/actions/runs/40273247940) returned UNASSESSED due to GitHub API HTTP 403, not a confirmed missing VPS Release. Oct 27/28 watcher runs succeeded.
- Oct 26/27/28 optional GitHub scheduled collector runs failed to start before 00:15 UTC; separate VPS→immutable GitHub Release/audit chain succeeded. Never synthesize late sources.

## Constraints

- Exactly six completed UTC days, five adjacent pairs, no skipped dates; bounded 2..90 day tool.
- Main-push only for workflow-file changes plus explicit operator manual range. No cron or automatic recurring scan.
- GH permissions `contents: read`, `actions: read`, no source calls except original published GitHub ZIPs.
- All upstream exchange first-publication, acquisitions/promotions and economics approval fields must remain false.
- Workflow script uses main at actual postmerge commit; do not imply PR test proves live source consistency.

## Acceptance criteria

- [x] Set on-main-push defaults to `2026-10-23..2026-10-28` without changing manual 2..90 date inputs.
- [x] Regression tests enforce six inclusive UTC days, five adjacent pairs, no schedule and read-only permission.
- [x] Final-head five required CI checks and offline Historical Smoke SUCCESS.
- [x] After merge: verify real GitHub main-push workflow run, original ZIP SHA256s and five pair classifications; record exact run/artifact and any UNASSESSED or changed-source findings before calling done.

## Implementation slices

- [x] 1. Change safe fixed workflow defaults/comment.
- [x] 2. Update targeted read-only governance test.
- [x] 3. PR and final-head CI/Smoke; wait for genuine human PR review/merge before postmerge derived replay and archival.

## Verification matrix

| Gate | Command or workflow | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_funding_source_continuity.py -v` | PASS under Code-level CI #40733933324 |
| Static | `uv run ruff check .` | PASS under CI #40733933324 |
| Code/API/E2E/Agent Plan | `.github/workflows/ci.yml` | all five SUCCESS, CI #40733933324 |
| Historical Smoke | `.github/workflows/historical-smoke.yml` | SUCCESS, run #40733933471 |
| Real continuity | Main-push `Review Funding Source Continuity` | SUCCESS, run #40734065510; 6/6 audited, 5/5 consistent |

## Decision gates

None for the read-only research review itself. Historical source admissions or new observer trust assumptions still require explicit separate approval.

## Evidence log

- 2026-10-28: inspected production GitHub Release/audit run metadata for 26/27/28 and failure logs for optional scheduled source and Oct 26 HTTP 403 watcher. New cross-day original ZIP values not yet rechecked.

## Deviations and discoveries

- PR #160 merged while #161 was open; GitHub strict required status checks rejected stale-base merge (HTTP 405). The #161 branch was reconciled to new main via a non-forced two-parent commit `02b256bbe7a254da08cd3175b06b32e658befbb4`, with the main tree plus only #161's three changed blobs; fresh final-head CI/Smoke then passed. No code or plan from #160 was reverted.

## Resume from here

Completed; the parent Issue #85 Option A plan owns future new-day source continuity reviews. Do not republish/replay these original six days solely to create another artifact.

## Completion

Final commit: `5a6b6da4dbea1b33fde44a41524d587ad3488e9f` (PR #161 squash merge)
CI run: [#40733933324](https://github.com/pkking/future-opportunity/actions/runs/40733933324), five required checks SUCCESS on exact HEAD `02b256bbe7a254da08cd3175b06b32e658befbb4`; [Historical Smoke #40733933471](https://github.com/pkking/future-opportunity/actions/runs/40733933471) SUCCESS; postmerge main [#40734065661](https://github.com/pkking/future-opportunity/actions/runs/40734065661) SUCCESS
E2E artifact: GitHub Actions ID `12837065334`, SHA256 `7d93ddee65056460cf194445fb6d68535f8ad08b6f5b4267afe6be5433c2cd49`
Real six-day artifact: [Run #40734065510](https://github.com/pkking/future-opportunity/actions/runs/40734065510) SUCCESS; derived artifact ID `12836248240`, ZIP SHA256 `443f634b221435636069a581fe5f5a23972410c623117ba0863dc29de88af99d`
Remaining unassessed items: upstream OKX first-publication authenticity, negative+low Funding regime (0 observed), historical acquisitions/promotion. Funding pinned 32/90, Cash pinned 66. Numerical economics gates still disabled.


## Real original-source continuity evidence (2026-10-28)

The postmerge one-shot GitHub-only read-only report verified all six complete original source days 2026-10-23..28, original ZIP digests, six successful corresponding independent release.published audits and five strict consecutive UTC adjacent pairs. It returned `OVERLAP_VALUES_CONSISTENT_ONLY`, `checked_day_count=6`, `github_audited_day_count=6`, `expected_pair_count=5`, `consistent_pair_count=5`, `revision_pair_count=0`, `unassessed_pair_count=0`, and `every_adjacent_pair_assessed=true`.

| Adjacent UTC source days | Overlapping settled Funding events | Realized-rate numerical revisions | Unexpected historical confirmations | Regressions | Status |
|---|---:|---:|---:|---:|---|
| 2026-10-23→24 | 284 | 0 | 0 | 0 | CONSISTENT |
| 2026-10-24→25 | 286 | 0 | 0 | 0 | CONSISTENT |
| 2026-10-25→26 | 290 | 0 | 0 | 0 | CONSISTENT |
| 2026-10-26→27 | 293 | 0 | 0 | 0 | CONSISTENT |
| 2026-10-27→28 | 275 | 0 | 0 | 0 | CONSISTENT |

Each pair also had exactly one expected current-day 1Dutc `confirm=0→1` transition, zero previously-confirmed spot-close numeric revisions and no retroactive historical confirmation anomaly. Original source ZIP SHA256: 23 `bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068`; 24 `d3961babf389449900dff7f56b3006291459ebb8776de2c03abff944af33894b`; 25 `932431486e42b0620df7b73ab23b3d7a2c9bdcb6800f2c755748a3c746d1119c`; 26 `976c9f2b49e59d53096e045806d418139dc1d9ec31963d5bd59c3af10aa4aab8`; 27 `3a2423d71d780fe2f91a4fbea667c9db65d0462de8f3d2ce852c381e1d590734`; 28 `929272be6e352c439d7e7d15ecf69e59862934838b4794e1169496dd20347d53`.

Audited prospective 2×2 regime distribution (fixed sign and 100bps threshold): nonnegative/high=6, other three strata=0; not a market-wide estimate. `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`; keep all economic and trading boundaries unchanged.
