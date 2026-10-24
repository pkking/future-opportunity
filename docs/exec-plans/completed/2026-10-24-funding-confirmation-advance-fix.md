# Funding source revision audit: expected unconfirmed-to-confirmed daily candle transition

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Correct a real false positive in the just-deployed GitHub-only original-source overlap audit: a daily UTC candle with `confirm=0` (in progress) in the first pre-entry original can become `confirm=1` (completed) in the following day's original. This is *expected market-data lifecycle*, not historical revision. Preserve fail-closed source integrity for `1→0` and changed already-confirmed closes.

## Non-goals

No change to OKX collection or exchange timestamp authentication; no new market API fetch, immutable Release upload, Stage-2 historical corpus, economic gate, or trading. No change in the raw/source hash policy.

## Verified evidence

- PR #145 merged `58d281cc8b129e62f9e1c76e07d704a8b7470c3d`, final-head CI #40101850764 five SUCCESS and Historical Smoke #40101850768 SUCCESS.
- **Actual independent GitHub original-source audit** https://github.com/pkking/future-opportunity/actions/runs/40101911029 failed closed with `SOURCE_REVISION_DETECTED`; retained derived Artifact ID `12563356664`, SHA256 `5333178399d570d9f02d6a4fc3071974e11c901ccdda9670efa8cac4d8c1f5cb`.
- Original ZIP hashes matched both immutable GitHub releases. 284 exact overlapping settled Funding event rates had zero revisions; 98 previously completed common spot closes had zero revisions. The **only** comparison conflict was 2026-10-23T00:00:00Z daily candle confirmation changing between two successive pre-entry snapshots: earlier 0, later 1.
- This transition is the expected `1Dutc` current-day candle lifecycle. It must not be used to infer missing history, fraudulent source, or exchange publication signature. Strict source-origin status still stays false.

## Acceptance criteria

- [x] Distinguish `0→1` normal confirmation advances (report explicit timestamp list) from `1→0` confirmation regressions (fail-closed source revision).
- [x] Keep both-previously-confirmed candle close and common settled funding rate revisions failing closed; do not compare an unfinished candle as if it were a completed close.
- [x] Offline tests for actual 0→1 transition with stable overlap SUCCESS, 1→0 regression FAIL, already-confirmed close/settlement changes FAIL, no overlap UNASSESSED.
- [x] Workflow original read-only permissions, no new market GET and mandatory original SHA256/audit gate unchanged.
- [x] Verify exact final-head CI five SUCCESS, Historical Backtest Smoke SUCCESS; merge and verify postmerge main CI.
- [x] Independently rerun the existing read-only workflow against 2026-10-23/24 originals; report actual run and artifact before archival. Do not treat the old failure as passing.
- [x] Move plan to completed with final evidence and explicitly retain parent Issue #85 OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [x] 1. Fix expected confirmation-state progression in overlap comparison.
- [x] 2. Add deterministic regression tests and clarify runbook.
- [x] 3. CI/Historical Smoke, merge, real GitHub-only diagnostic, independently archive.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | CI code-level tests #40102242986, includes added actual-lifecycle tests | PASS |
| Static / API / code / E2E / Plan | final head `ffe1b845` CI #40102242986 five SUCCESS, postmerge main #40102318332 SUCCESS | PASS |
| Historical | final head #40102242958 SUCCESS | PASS |
| Actual source | #40102318270 SUCCESS on the original archived bytes | PASS |

## Decision gates

None. Correcting a current-day candle's normal confirmation transition is evidence semantics inside the existing source-only contract, NOT changing frozen capital, domain, exchange-authentication or trading policy.

## Evidence log

- 2026-10-24: Final PR #146 head `ffe1b845ae6501e4dda8b11768cff36dab16bc01` passed all five CI https://github.com/pkking/future-opportunity/actions/runs/40102242986 and Historical Backtest Smoke https://github.com/pkking/future-opportunity/actions/runs/40102242958. Squash-merged to main `eb43c13e18e3f376ee09a8b8a184c5eecdabefdc`; postmerge main CI https://github.com/pkking/future-opportunity/actions/runs/40102318332 SUCCESS. E2E artifact ID `12562339762`, SHA256 `a5263a599688d128e043b04f3d32b26815928825a0d1d954961e66fe30114be2`; historical ID `12563730263`, SHA256 `d87b24b0cd89e8e24c94fa1358ca48b413e8e8fc30ed668834e5c86699810edd`.
- 2026-10-24: Rerun on real same immutable originals was triggered by the scope-limited workflow-file main push, **not** a new market collection. https://github.com/pkking/future-opportunity/actions/runs/40102318270 SUCCESS: 284 common Funding rates / zero revisions, 98 previously confirmed spot closes / zero revisions, 2026-10-23T00:00Z current daily candle 0→1 normal confirmation advancement / zero regressions. Final `OVERLAP_VALUES_CONSISTENT_ONLY`. Derived artifact `funding-original-overlap-revision-review` ID `12563576192`, SHA256 `f62a0930352a7db609599e1f818d03603baee3a3d70e4886e7173d289cae7720`. Original failed Run #40101911029 remains retained separately. All source/financial eligibility gates remain false.

- 2026-10-24: Code now separately records `confirmation_state_advances` (0→1, nonfailure) and `confirmation_state_regressions` (1→0, fail-closed) and keeps `confirmation_state_conflicts` for the latter compatibility. Added no-network tests reproducing the actual 2026-10-23 UTC still-open candle and unchanged negative regressions; updated runbook. **CI and real second audit not yet executed**.

- 2026-10-24: Original rollout failed closed on a false positive; no contradictory settled funding values or completed spot closes observed. Keep original failure run visible.

## Resume from here

The code and actual original-source correction are independently verified and complete. Continue active Issue #85's source publication/authentication and missing regime research; do not use a stable overlapping response as proof of exchange publication or historical sample acquisition eligibility.

## Completion

Final commit: `eb43c13e18e3f376ee09a8b8a184c5eecdabefdc` (PR #146, exact tested head `ffe1b845ae6501e4dda8b11768cff36dab16bc01`)
CI run: #40102242986 (5 SUCCESS), Historical #40102242958 SUCCESS, postmerge #40102318332 SUCCESS, real source #40102318270 SUCCESS
E2E artifact: `12562339762`; Historical artifact: `12563730263`; real source: `12563576192` (digests in evidence log)
Remaining unassessed items: OKX as-of publication/exchange signatures and missing negative-low volatility regime; historical promotion and strategy economics remain disabled.
