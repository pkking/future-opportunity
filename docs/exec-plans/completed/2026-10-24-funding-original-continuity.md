# Bounded multi-day Funding original-source continuity audit

Issue: #85
Status: COMPLETED
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
- [x] CI all five jobs and Historical Backtest Smoke on exact final PR head; merge, verify main CI and actual production diagnostic, then separate completed-plan archive with Issue #85 checkpoint.

## Implementation slices

- [x] 1. Introduce validated source continuity report that reuses both existing audit layers.
- [x] 2. Add comprehensive no-network regression tests and static workflow policy tests.
- [x] 3. Add manual-only/one-time path-push GitHub Action and operator runbook.
- [x] 4. Full final-head CI/Smoke, merge, actual GitHub source run and explicit archival.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | Covered by CI #40109100122 code-level tests, implementation head `f7bfa4c` | PASS |
| Static | CI #40109100122 architecture/static check | PASS |
| CI | Final PR #148 head `7be76be7` #40109183719 all five SUCCESS; postmerge main #40109242716 SUCCESS | PASS |
| Historical | Final PR #148 head `7be76be7` Historical Smoke #40109183569 SUCCESS | PASS |
| Production | Real main push #40109242759 SUCCESS; independent 2026-10-23..24 immutable GitHub source pair | PASS |

## Decision gates

None. New report is a read-only diagnostic over accepted original-source audit functions, not an alternative historical source standard. Historical acquisition, numerical economic gates and live trading require separate decisions and are untouched.

## Evidence log

- 2026-10-24: Final [PR #148](https://github.com/pkking/future-opportunity/pull/148) tested head `7be76be7b47168080d3bf091d58df30c52e09908`: [CI #40109183719](https://github.com/pkking/future-opportunity/actions/runs/40109183719) five SUCCESS and [Historical Smoke #40109183569](https://github.com/pkking/future-opportunity/actions/runs/40109183569) SUCCESS. Squash merge main `7a42ec32fd8275cff9868d15bd5697500003e6f0`, [postmerge main CI #40109242716](https://github.com/pkking/future-opportunity/actions/runs/40109242716) SUCCESS. Final head CI E2E artifact ID `12566235647` SHA256 `5df535682d1cc28f76baa2773feba410dee4d2d67dc8dbae80b52e5e046e3462`; historical artifact ID `12566195249` SHA256 `46b7378cd24ffa17589494d40bd9c0225c1fb6c55f042c3523c4cd9cd8d4d430`.
- 2026-10-24: **Actual** [GitHub-only continuity review #40109242759](https://github.com/pkking/future-opportunity/actions/runs/40109242759) SUCCESS from first workflow-file main push. Original 2026-10-23/24 ZIP digests `bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068` and `d3961babf389449900dff7f56b3006291459ebb8776de2c03abff944af33894b` independently replayed with matching successful Release audits. `checked_day_count=2`, `expected_pair_count=1`, `consistent_pair_count=1`, `revision_pair_count=0`, `unassessed_pair_count=0`. Common settled funding: 284, no changed rate; common confirmed spot candles: 98, no changed close; one normal 2026-10-23 UTC daily 0→1 confirmation, no regression. Derived artifact ID `12565966816`, SHA256 `d1c1e24d656b52a74a64c4501e219d7a3389889f1408df6a1446b56b3adb1ce0`. **This does not prove 90 real observed days, independent OKX first publishing time or historical acquisition eligibility**; current two-day source regime remains nonnegative/high only, Funding pinned corpus remains 32, economics disabled.

- 2026-10-24: PR #148 implementation HEAD `f7bfa4c7a375c8c5ac7ba6e86d4f4284f74b7ae2` passed complete [CI #40109100122](https://github.com/pkking/future-opportunity/actions/runs/40109100122) five SUCCESS and [Historical Smoke #40109100128](https://github.com/pkking/future-opportunity/actions/runs/40109100128) SUCCESS. CI E2E artifact ID `12565549091`, SHA256 `d0d428071cb870a9a24b1d99adfd8c40c06045f072615b1826bc1abefd06e1d3`; Historical artifact ID `12565303099`, SHA256 `8bd26b668a2e291f94a3f9336f5ecf0e0f53069fc32923e5ab2cc2c59d38b0dc`. The evidence-only checkpoint that adds this record changes PR head; exact final-head CI + Historical Smoke must be verified again before merge.

- 2026-10-24: Initial implementation: `scripts/report_funding_source_continuity.py`, `tests/test_funding_source_continuity.py`, `.github/workflows/review-funding-source-continuity.yml` and operator runbook. Tests are synthetic MockTransport only; final-head CI and genuine GitHub evidence remain pending. No live OKX request and no historical sample change.

- 2026-10-24: Source and contracts inspected at main `fdba089fc1bab561ab75f8cb495af168a9bcebe2`. No new genuine source days available after 2026-10-24.

## Resume from here

Verify all 5 CI jobs and Historical Smoke succeed on the new final PR #148 checkpoint SHA, then squash merge with expected head. Observe main push CI AND new workflow's one-time real immutable source run. Record exact actual pair counts, real artifact identities, and negative/empty status in this plan; archive via separate completion PR. Parent Issue #85 remains OPEN/BLOCKED_EVIDENCE.

## Completion

Final commit: `7a42ec32fd8275cff9868d15bd5697500003e6f0` (PR #148; exact tested head `7be76be7b47168080d3bf091d58df30c52e09908`)
CI run: #40109183719 all five SUCCESS, Historical Smoke #40109183569 SUCCESS, main #40109242716 SUCCESS, real GitHub original continuity #40109242759 SUCCESS
E2E artifact: ID `12566235647`; Historical ID `12566195249`; actual source ID `12565966816` (SHA256 digests in evidence log)
Remaining unassessed items: independent OKX published-as-of entry, exchange-signed responses, missing Funding negative/low volatility, true acquisition eligibility; pinned 32/90 not changed.
