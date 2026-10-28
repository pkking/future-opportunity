# Six real immutable Funding originals: 2026-10-23..28

Issue: #85
Status: IMPLEMENTING
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

- [ ] Set on-main-push defaults to `2026-10-23..2026-10-28` without changing manual 2..90 date inputs.
- [ ] Regression tests enforce six inclusive UTC days, five adjacent pairs, no schedule and read-only permission.
- [ ] Final-head five required CI checks and offline Historical Smoke SUCCESS.
- [ ] After merge: verify real GitHub main-push workflow run, original ZIP SHA256s and five pair classifications; record exact run/artifact and any UNASSESSED or changed-source findings before calling done.

## Implementation slices

- [ ] 1. Change safe fixed workflow defaults/comment.
- [ ] 2. Update targeted read-only governance test.
- [ ] 3. PR and final-head CI/Smoke; wait for genuine human PR review/merge before postmerge derived replay and archival.

## Verification matrix

| Gate | Command or workflow | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_funding_source_continuity.py -v` | pending |
| Static | `uv run ruff check .` | pending |
| Code/API/E2E/Agent Plan | `.github/workflows/ci.yml` | pending |
| Historical Smoke | `.github/workflows/historical-smoke.yml` | pending |
| Real continuity | Main-push `Review Funding Source Continuity` | not started; requires merge |

## Decision gates

None for the read-only research review itself. Historical source admissions or new observer trust assumptions still require explicit separate approval.

## Evidence log

- 2026-10-28: inspected production GitHub Release/audit run metadata for 26/27/28 and failure logs for optional scheduled source and Oct 26 HTTP 403 watcher. New cross-day original ZIP values not yet rechecked.

## Deviations and discoveries

None.

## Resume from here

Change workflow defaults and governance tests, submit PR, verify exact-head CI/Smoke. Only after merge can the on-main-push six-day real original-source replay be independently reported.

## Completion

Final head: pending
PR CI: pending
Real six-day artifact: UNASSESSED pending postmerge run
Funding pinned 32/90, Cash pinned 66; upstream first-publication authenticity remains unverified.
