# Funding source revision audit: expected unconfirmed-to-confirmed daily candle transition

Issue: #85
Status: IMPLEMENTING
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
- [ ] Verify exact final-head CI five SUCCESS, Historical Backtest Smoke SUCCESS; merge and verify postmerge main CI.
- [ ] Independently rerun the existing read-only workflow against 2026-10-23/24 originals; report actual run and artifact before archival. Do not treat the old failure as passing.
- [ ] Move plan to completed with final evidence and explicitly retain parent Issue #85 OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [x] 1. Fix expected confirmation-state progression in overlap comparison.
- [x] 2. Add deterministic regression tests and clarify runbook.
- [ ] 3. CI/Historical Smoke, merge, real GitHub-only diagnostic, independently archive.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_overlap_revision_audit.py` | Pending |
| Static / API / code / E2E / Plan | final-head five CI checks | Pending |
| Historical | final-head Historical Backtest Smoke | Pending |
| Actual source | real GitHub original 2026-10-23/24 re-audit | Pending |

## Decision gates

None. Correcting a current-day candle's normal confirmation transition is evidence semantics inside the existing source-only contract, NOT changing frozen capital, domain, exchange-authentication or trading policy.

## Evidence log

- 2026-10-24: Code now separately records `confirmation_state_advances` (0→1, nonfailure) and `confirmation_state_regressions` (1→0, fail-closed) and keeps `confirmation_state_conflicts` for the latter compatibility. Added no-network tests reproducing the actual 2026-10-23 UTC still-open candle and unchanged negative regressions; updated runbook. **CI and real second audit not yet executed**.

- 2026-10-24: Original rollout failed closed on a false positive; no contradictory settled funding values or completed spot closes observed. Keep original failure run visible.

## Resume from here

Run PR tests, including final-head five CI and Historical Smoke. Merge only if exact revision passes; then verify actual read-only workflow_dispatch against original 2026-10-23/24 immutable assets and postmerge CI, record both old failure and corrected run, archive completed plan separately.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: OKX as-of publication/exchange signatures and missing negative-low volatility regime; historical promotion and strategy economics remain disabled.
