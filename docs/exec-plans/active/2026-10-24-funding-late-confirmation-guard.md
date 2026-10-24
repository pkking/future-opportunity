# Funding original-source late-confirmation safety guard

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Fix a fail-open edge in the already released read-only Funding original ZIP consistency auditor: the current two-day comparator treats **any** historical spot candle `confirm=0 → confirm=1` change as a benign progression. Such progression is benign only for the first snapshot's **current UTC daily candle** (open time at the earlier capture's `start_date` midnight). A previous-day/older candle that remained unconfirmed at the first captured 00:15 UTC entry and becomes confirmed later is a delayed/stale historic source condition, not normal current-candle completion. Detect and report it explicitly without extrapolating its cause or authorizing source promotion.

## Current facts

- Main `6e70ec81b9a7dc68a7161514856cd29e2a6069ad`, no open PRs, last main CI #40109489861 SUCCESS.
- Official immutable GitHub Release original-source dates 2026-10-23 and 2026-10-24 only; no new 2026-10-25 source. Issue #85 remains OPEN/BLOCKED_EVIDENCE.
- [Original two-day review #40102318270](https://github.com/pkking/future-opportunity/actions/runs/40102318270) SUCCESS: 284 common settled Funding rates and 98 previously confirmed spot closes unchanged, with exactly one `2026-10-23T00:00Z` current-day 0→1 candle completion.
- The new 2–90 day `scripts/report_funding_source_continuity.py` calls `compare_overlapping_sources`, so fixing its shared semantics covers both two-day and longitudinal reviews without altering GitHub Release audit, source hash, or original evidence.

## Constraints

- V0 paper-only; ADR-0008 disables all numerical economics gates; no live orders, no OKX GET, no new source, new schedule or new storage.
- Independent original immutable GitHub Release SHA256 and release.published audit MUST remain preconditions in `audit_pair` and `audit_continuity`.
- Normal progression 0→1 is eligible for benign classification **only** when the candle's UTC open is exactly the earlier source's entry date at midnight. Once a candle should already be fully closed at an earlier entry, delayed confirmation is a source-completeness anomaly.
- Distinguish `unexpected_historical_confirmation_advances` from confirmed→unconfirmed `confirmation_state_regressions`. Retain `confirmation_state_conflicts` as a backward-compatible union of true source confirmation anomalies. Both anomaly forms return `SOURCE_REVISION_DETECTED` for strict diagnostics, **not** an economic return or exchange first-publication claim.

## Acceptance criteria

- [ ] Same-UTC-day 0→1 transition remains benign and explicitly listed in `confirmation_state_advances`.
- [ ] 0→1 change for a UTC daily candle before or after earlier snapshot entry day is distinct `unexpected_historical_confirmation_advances` and fails closed, even with unchanged numerical rates and completed closes.
- [ ] Previously confirmed→unconfirmed (1→0) continues to fail, with `confirmation_state_regressions` and `confirmation_state_conflicts`; comparable completed close/rate numeric revisions still fail.
- [ ] Source capture `start_date` used for temporal classification is canonical, valid and identical to earlier source identity already validated by immutable-source replay; malformed capture date cannot silently classify a status as benign.
- [ ] Both two-day and three-day longitudinal scripts inherit the guard with regression tests; missing middle day and SHA-digest mismatch still fail closed. Original GitHub sources never rewritten.
- [ ] Runbook describes expected current-candle 0→1 and delayed historical confirmation anomalies without implying signed exchange publication.
- [ ] Final-head five CI SUCCESS and Historical Backtest Smoke SUCCESS, merge and postmerge main CI SUCCESS, then real read-only GitHub original-source two-day recheck on unchanged originals.
- [ ] Completion-only PR archives a validated plan with original failing/passing evidence, all checksums and same parent Issue #85 OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [ ] 1. Add strict prior entry date classification and an explicit delayed historical confirmation evidence list.
- [ ] 2. Add targeted offline 2-day/3-day tests and documentation.
- [ ] 3. Final-head CI/Historical Smoke, merge, verify actual original source with no new market GET.
- [ ] 4. Record complete audit and archive plan separately after gates.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_overlap_revision_audit.py tests/test_funding_source_continuity.py` | pending |
| Static | `uv run ruff check .` | pending |
| Code/API/E2E/plan | GitHub CI five jobs | pending |
| Historical | Historical Backtest Smoke | pending |
| Real source | existing 2026-10-23/24 immutable ZIPs; no new source | pending |

## Decision gates

None. This is a semantic correctness guard internal to the already accepted read-only source integrity diagnostics, not a change to strategy qualification, historical admissions, reference tests or trading policy. The OKX as-of publication provenance remains unverified.

## Evidence log

- 2026-10-24: Base main verified. Shared function currently treats every 0→1 as benign; actual production first-day 0→1 is valid and must remain so.

## Resume from here

Implement exact earlier capture day classification, add regression tests and sync runbook; run PR-level CI + Historical Smoke. Keep historical raw source and all promotion/approval flags unchanged.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: OKX exchange-signed public-as-of publication, historically eligible Funding additions, absent negative/low-volatility regime and numerical economics.
