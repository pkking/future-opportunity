# Real three-day immutable Funding original continuity, Option A

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-25
Last checkpoint: 2026-10-25

## Objective

Re-check the existing immutable GitHub/VPS Funding originals and independent successful release.published audit for **three actual consecutive 2026-10-23..25 UTC days**, rather than continuing to cite only the earlier two-day success. Exercise the production 2–90-day report with all two adjacent date edges and archive exact original source hashes, latest regime counts, anomalies and evidence gaps. Diagnose, but do not falsely repair or replay, the separately failed best-effort scheduled capture run #40151260280.

## Baseline

- Main `942587d8e5eed3e79bf708aa629572eadcee297e`; no open PRs, main CI #40196917076 SUCCESS.
- Genuine public immutable Releases `funding-vps-2026-10-23`, `2026-10-24`, `2026-10-25`; 25 independent successful `release.published` run #40144972278. The earlier two-day pair succeeded with a normal one-day 0→1 daily candle advance.
- `scripts/report_funding_source_continuity.py` already verifies per-day Release original ZIP and independent audit, SHA256 exact original, and each adjacent numeric Funding/spot value revision.
- Existing manual read-only GitHub workflow defaults for its workflow-file push one-shot to 2026-10-23..24, which **omits the new 25th**. It has no schedule and no source writes.
- Separate scheduled GitHub collector [run #40151260280](https://github.com/pkking/future-opportunity/actions/runs/40151260280) started 2026-10-25 01:35:55 UTC, and correctly failed its capture guard at 01:36:04 UTC because pre-entry source window is 00:00..00:15; it retained a failure receipt. This GitHub schedule is best-effort and cannot replace reliable VPS publication.

## Non-goals and safety

- Option A exclusively: existing prospective VPS→immutable GitHub Release→independent release event audit. No B observer, external storage/time witness, real market API GET, new periodic schedule, source capture, backfill, fixture promotion, new numerical economics, trading or change to sample admission.
- Read-only main-push single diagnostic is permitted only because actual immutable date exists, and is scoped to workflow file change. Must not assert new historical pin, 90 genuine dates or independent OKX first publication.
- Preserve missing/unaudited source day as UNASSESSED rather than bridge gaps or fabricate zero opportunity; preserve source status/revision fail-closed behavior.

## Acceptance criteria

- [ ] Verify Release 2026-10-25 exists immutable, was published before 00:15 UTC with separately successful release event audit; keep 23/24 original SHA constraints unchanged.
- [ ] Narrow workflow code change expands actual one-time main-push fallback to 2026-10-23..25, preserving explicit manual 2..90 date inputs, no schedule and all read-only permissions.
- [ ] Add offline workflow contract tests to assert exact current three-day default, manual override, no market GET/Release creation, non-promotion flags; inspect existing continuity regression tests.
- [ ] Document objective root cause for GitHub scheduled collector delay; do not infer VPS collector outage or waive UTC fail-closed window.
- [ ] Final-head five CI gates, Historical Smoke all SUCCESS, squash-merge and verify postmerge main CI.
- [ ] **Actual source review** GitHub workflow on main-push succeeded or failed closed, report expected 2 date pairs, exact per-pair values/digests, source regimes, derived Artifact ID and SHA256. Failure must be honestly recorded, not silently fixed.
- [ ] Archive verified plan with evidence in separate completed PR and append Issue #85 checkpoint, while issue remains OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [ ] 1. Update the scope-limited no-schedule workflow's built-in main-push diagnostic to three actually existing release dates.
- [ ] 2. Add regression safety assertions and update runbook including GitHub delayed-cron failure semantics.
- [ ] 3. Full final-head CI/Smoke; merge; inspect real GitHub original-source review and postmerge CI.
- [ ] 4. Archive plan separately and record actual primary evidence and remaining blocking limitations.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_source_continuity.py` | pending |
| Static | `uv run ruff check .` | pending |
| CI | five jobs on PR final head | pending |
| Historical Smoke | final-head pinned replay | pending |
| Source | production exact three-day GitHub original-source continuity run | pending |

## Decision gates

None. The user explicitly selected A, the existing GitHub-only immutable source audits and manual diagnostic are already accepted. This slice does not deploy any observer/third-party authority or change business evidence admission.

## Evidence log

- 2026-10-25: Latest main/PR/release checked. Independent event audit #40144972278 SUCCESS, 2026-10-25 Release immutable published 00:00:15 UTC. Scheduled GHA capture #40151260280 START 01:35:55 UTC (80 min after close of capture window) and correctly refused past-deadline source; separate audit job completed SUCCESS for the failure receipt. Missing scheduled source is not a market-negative sample. No real 3-day compare claimed yet.

## Resume from here

Implement scoped three-day GitHub original review with test and runbook, submit tracked PR; run exact-head 5/5 CI and Historical Smoke; merge and *inspect actual production 3-day source artifact* before marking complete. Keep Issue #85 OPEN/BLOCKED_EVIDENCE.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: independent OKX first dissemination time/signature, 90 preferred pinned Funding dates, negative-low regime, historical source admissions, Stage-2 economics and trading.
