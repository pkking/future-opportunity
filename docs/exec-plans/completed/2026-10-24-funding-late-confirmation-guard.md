# Funding original-source late-confirmation safety guard

Issue: #85
Status: COMPLETED
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

- [x] Same-UTC-day 0→1 transition remains benign and explicitly listed in `confirmation_state_advances`.
- [x] 0→1 change for a UTC daily candle before or after earlier snapshot entry day is distinct `unexpected_historical_confirmation_advances` and fails closed, even with unchanged numerical rates and completed closes.
- [x] Previously confirmed→unconfirmed (1→0) continues to fail, with `confirmation_state_regressions` and `confirmation_state_conflicts`; comparable completed close/rate numeric revisions still fail.
- [x] Source capture `start_date` used for temporal classification is canonical, valid and identical to earlier source identity already validated by immutable-source replay; malformed capture date cannot silently classify a status as benign.
- [x] Both two-day and three-day longitudinal scripts inherit the guard with regression tests; missing middle day and SHA-digest mismatch still fail closed. Original GitHub sources never rewritten.
- [x] Runbook describes expected current-candle 0→1 and delayed historical confirmation anomalies without implying signed exchange publication.
- [x] Final-head five CI SUCCESS and Historical Backtest Smoke SUCCESS, merge and postmerge main CI SUCCESS, then real read-only GitHub original-source two-day recheck on unchanged originals.
- [x] Completion-only PR archives a validated plan with original failing/passing evidence, all checksums and same parent Issue #85 OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [x] 1. Add strict prior entry date classification and an explicit delayed historical confirmation evidence list.
- [x] 2. Add targeted offline 2-day/3-day tests and documentation.
- [x] 3. Final-head CI/Historical Smoke, merge, verify actual original source with no new market GET.
- [x] 4. Record complete audit and archive plan separately after gates.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | CI #40143217480 code-level tests cover both cases, implementation head | PASS |
| Static | CI #40143217480 static/architecture SUCCESS | PASS |
| Code/API/E2E/plan | Final PR #150 head `6e3859c` CI #40143304320 5/5 SUCCESS; postmerge main #40143358419 SUCCESS | PASS |
| Historical | Final PR #150 head Historical Smoke #40143304218 SUCCESS | PASS |
| Real source | Main-push read-only original audit #40143358400 SUCCESS, exact existing 2026-10-23/24 ZIPs | PASS |

## Decision gates

None. This is a semantic correctness guard internal to the already accepted read-only source integrity diagnostics, not a change to strategy qualification, historical admissions, reference tests or trading policy. The OKX as-of publication provenance remains unverified.

## Evidence log

- 2026-10-24: PR #150 final tested HEAD `6e3859c268d56cc4fb454f62ca525637d4693a23`: [CI #40143304320](https://github.com/pkking/future-opportunity/actions/runs/40143304320) all five SUCCESS; [Historical Smoke #40143304218](https://github.com/pkking/future-opportunity/actions/runs/40143304218) SUCCESS. Squash-merged to main `4c12588e5ed4dc95bfd6be3ce5898c7158ae6d99`. [Postmerge main CI #40143358419](https://github.com/pkking/future-opportunity/actions/runs/40143358419) SUCCESS. Final PR-head E2E Artifact ID `12579053818`, SHA256 `dbaa326904f1e0f675f05fa1c878dea571bed8f04ae73debf3873d4e54754f71`; Historical Artifact ID `12579023939`, SHA256 `054e3d0786a4c19ea7cd8927764919e5d76fc84d3a2a11591b16507f22735d16`.
- 2026-10-24: **Actual unchanged original ZIP read-only main-push diagnostic** [#40143358400](https://github.com/pkking/future-opportunity/actions/runs/40143358400) SUCCESS. 2026-10-23/24 immutable ZIP digests `bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068` and `d3961babf389449900dff7f56b3006291459ebb8776de2c03abff944af33894b` replayed. 284 overlapping historical Funding events with **zero** numerical revisions, 98 previously confirmed spot closes with **zero** revisions, **one** normal same-day 0→1 confirmation, **zero** unexpected historical 0→1 advances, **zero** 1→0 regressions. Final status `OVERLAP_VALUES_CONSISTENT_ONLY`. Derived Artifact ID `12580041448` SHA256 `caea6190422f31f9d6e07bd2949542a9504c0a15945d9b7b26ecbd18fe64072c`. No OKX GET or source/corpus mutation, no exchange as-of authentication proven.

- 2026-10-24: Initial PR #150 implementation head `37baf3e403732fe15a7df87321656b2ad11b7499` passed [CI #40143217480](https://github.com/pkking/future-opportunity/actions/runs/40143217480) all five jobs SUCCESS and [Historical Smoke #40143217487](https://github.com/pkking/future-opportunity/actions/runs/40143217487) SUCCESS. E2E artifact ID `12580011169` SHA256 `0ca3f3577fc957552ca2a0602d7a70014cef4ea73dd52c12bccd3e336ba361ce`; historical artifact ID `12580026247` SHA256 `e0f0ecf80eaa4eff35901422ab0d794cc1c9dc189e2cf71b2b28ab80174f16ad`. Also scoped existing GitHub-only original-overlap workflow for a one-time first-merge recheck of exactly the same 2026-10-23/24 originals, commit `0e2e30f246d58f433244d26a7b57379b92e44e3a`. Retest required on final PR HEAD after this checkpoint; no new source or exchange GET.

- 2026-10-24: Implemented exact canonical adjacent original capture days in shared `compare_overlapping_sources`, scoped benign `confirm=0→1` to first snapshot's current UTC candle, added `unexpected_historical_confirmation_advances` fail-closed and kept true 1→0 regressions separate. Two-day MockTransport tests, three-day chain failure test, and operator runbook updated. No live exchange request or original ZIP write. CI is pending.

- 2026-10-24: Base main verified. Shared function currently treats every 0→1 as benign; actual production first-day 0→1 is valid and must remain so.

## Resume from here

Slice complete. Continue parent active Issue #85 plan's latest resume: await and verify genuine new immutable Funding Releases with matching independent audits, collect further pre-registered regimes, and seek independently signed/published-as-of OKX evidence. Do not elevate GitHub custody-only observations to historical acquisition, economics or live-trading authority.

## Completion

Final commit: `4c12588e5ed4dc95bfd6be3ce5898c7158ae6d99` (PR #150 squash, final tested head `6e3859c268d56cc4fb454f62ca525637d4693a23`)
CI run: #40143304320 5 SUCCESS; Historical #40143304218 SUCCESS; main #40143358419 SUCCESS; real original ZIP #40143358400 SUCCESS
E2E artifact: ID `12579053818`; historical ID `12579023939`; real GitHub original ID `12580041448` (SHA256 in evidence log)
Remaining unassessed items: OKX exchange-signed public-as-of publication, historically eligible Funding additions, absent negative/low-volatility regime and numerical economics.
