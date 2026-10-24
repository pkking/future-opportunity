# Bounded multi-day Funding original-source continuity audit

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Extend the proven 2026-10-23/24 original-source comparison into a **2–90 complete UTC days** GitHub-only longitudinal continuity audit. One request should verify each day's original immutable Release and matching successful independent `release.published` audit, then compare *each adjacent calendar pair* while reusing prior downloaded source snapshots. Explicitly preserve missing days, data revisions, normal `1Dutc` 0→1 confirmation and original hashes. No date may be silently skipped and no missing record counted as zero opportunity.

## User-facing problem

The 90-day prospective custody inventory already exists, but the cross-day stable-values checker accepts exactly one pair. Once prospective Releases grow, checking 89 adjacent pairs manually with repeated full-source audits is costly, increases missed-gap risk and does not produce a single source-continuity evidence report.

## Baseline

- At start main `fdba089fc1bab561ab75f8cb495af168a9bcebe2`, no open PR; main CI #40102729801 SUCCESS.
- Immutable GitHub Releases through 2026-10-24 only; no new 2026-10-25 source.
- Existing `report_funding_prospective_custody_ledger.py` validates 1–90 completed source days, original ZIP replay and matching successful independent release audit with Actions history pagination.
- Existing `audit_funding_source_revision.py` compares two authenticated original ZIPs; #40102318270 real Success, 284 common funding / 98 confirmed spot closes unchanged, one normal spot 0→1 advance.
- Funding historical corpus pinned 32 (preferred 90, 58 short), Cash 66. Parent Issue #85 BLOCKED_EVIDENCE for independent OKX dissemination time and empty negative/low Funding regime.

## Constraints and non-goals

- GitHub-only HTTPS GETs against known repository and original Release paths. No OKX requests, publication or source mutation, no new schedule, raw archive upload, corpus/pinning, numerical economics, trading, or source promotion.
- Use existing immutable original ZIP SHA256, schema and official normalized source-row validators and fixed regime labels. Do not weaken any source fail-closed behavior.
- Efficient: one independent audit-run-history traversal and 1 verified original download/replay per checked date already in ledger; at most one *additional* original ZIP GET per verified date for pair comparison, constant number of raw snapshots resident.
- A signed GitHub custody timestamp **is not** a signed exchange publication timestamp.

## Acceptance criteria

- [x] Validate canonical inclusive 2–90 complete UTC days before network; strict chronological days, each adjacent pair included even if missing.
- [x] Independently audit each day's GitHub immutable original exactly once via current custody ledger; no comparison if one day lacks full independent source/audit flags.
- [x] Reuse original SHA256-checked raw snapshots at most once per day, bounded rolling memory; compare only adjacent calendar dates; no re-fetch for overlapping pairs.
- [x] Preserve per-pair numeric Funding, confirmed candle and confirmation-transition evidence and precise missing/unassessed states, with counts whose denominators match all expected pairs.
- [x] Fail nonzero if any pair has source revision, insufficient overlap, ZIP mismatch or missing audit. Distinguish genuine source revisions from insufficient evidence and do not mask one by the other.
- [x] Every output contains original day/digest identity, source-custody count, four-regime inventory, all pair statuses and hard-false exchange publication/acquisition/promotion fields.
- [x] Deterministic offline no-network tests for three-day complete chain, middle missing day, later-day revision, benign confirmation advance, ZIP hash failure, insufficient overlap, duplicate/future/too-wide dates and GET-only.
- [x] Manual GitHub Actions invocation for two explicit UTC endpoints, plus one first-merge diagnostic of already-existing 2026-10-23/24 originals, no schedule, derived artifact only.
- [ ] CI all five jobs and Historical Backtest Smoke on exact final PR head; merge, verify main CI and actual production diagnostic, then separate completed-plan archive with Issue #85 checkpoint.

## Implementation slices

- [x] 1. Introduce validated source continuity report that reuses both existing audit layers.
- [x] 2. Add comprehensive no-network regression tests and static workflow policy tests.
- [x] 3. Add manual-only/one-time path-push GitHub Action and operator runbook.
- [ ] 4. Full final-head CI/Smoke, merge, actual GitHub source run and explicit archival.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_source_continuity.py` | pending |
| Static | `uv run ruff check .` | pending |
| CI | full CI five jobs (plan/static/code/API/E2E) | pending |
| Historical | Historical Backtest Smoke | pending |
| Production | genuine existing immutable source two-day continuity run | pending |

## Decision gates

None. New report is a read-only diagnostic over accepted original-source audit functions, not an alternative historical source standard. Historical acquisition, numerical economic gates and live trading require separate decisions and are untouched.

## Evidence log

- 2026-10-24: Initial implementation: `scripts/report_funding_source_continuity.py`, `tests/test_funding_source_continuity.py`, `.github/workflows/review-funding-source-continuity.yml` and operator runbook. Tests are synthetic MockTransport only; final-head CI and genuine GitHub evidence remain pending. No live OKX request and no historical sample change.

- 2026-10-24: Source and contracts inspected at main `fdba089fc1bab561ab75f8cb495af168a9bcebe2`. No new genuine source days available after 2026-10-24.

## Resume from here

Open PR against current main with this active plan. Inspect first CI + Historical Backtest Smoke; fix code/tests from actual logs if needed. For final-head green checks merge PR; independently inspect postmerge main CI and actual GitHub-original two-day workflow run. Record exact artifacts and archive this child plan in a separate completion-only PR. Issue #85 stays OPEN/BLOCKED_EVIDENCE.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: independent OKX published-as-of entry, exchange-signed responses, missing Funding negative/low volatility, true acquisition eligibility; pinned 32/90 not changed.
