# Bounded multi-page GitHub Release audit discovery

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-28
Last checkpoint: 2026-10-28

## Objective

Prevent a false `AUDIT_MISSING` conclusion when the GitHub read-only Funding VPS Release watcher examines a completed historical UTC day whose matching `release.published` audit has aged beyond the most recent 100 workflow runs. A bounded/incomplete search must instead say `UNASSESSED`.

## Non-goals

No additional OKX requests, new clocks, historical acquisitions/promotions, Funding pinning, change to four frozen regime strata or 100bps boundary, approval of exchange publication authenticity, economic gate, or orders. Keep user-selected Option A, not inactive Option B.

## Must-read context

- `AGENTS.md`, `docs/design-baseline-v0.1.md`, `docs/v0-implementation-status.md`
- `docs/adr/0008-funding-stage2-historical-distribution-gate.md`
- `docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md`
- `scripts/check_funding_release_watch.py` and `tests/test_funding_release_watch.py`
- `docs/agents/workflow.md` and `docs/agents/testing.md`

## Current facts

- Base: `main` at `81d5517520f1f8b68aa742c736c09b904cca54cb`; no open PR as of start.
- `_get_audits` calls `actions/workflows/{workflow}/runs?event=release&per_page=100` without pagination.
- A missing entry in that truncated result is currently classified `AUDIT_MISSING` even if the audit may be on page 2 or later.
- Existing production custody for 2026-10-23..25 was separately audited with original ZIPs (PR #159), but this is NOT upstream OKX first-publication evidence. Historical source approval remains false.

## Constraints and invariants

- Read-only GitHub REST GET and bounded pages (no market/API writes).
- A successful audit must match the existing name, event, exact tag and created-after-release rule.
- Stop fetching as soon as every requested date has a matching relevant run, or pagination is provably exhausted; never infer absence after a capped search.
- On HTTP error, malformed pages, or incomplete capped search, fail closed as `UNASSESSED`.
- Keep `exchange_signed`, `point_in_time_publication_verified`, `acquisition_approved` and `promotion_approved` false.

## Acceptance criteria

- [x] Retrieve older matching Release audit from page 2+ using read-only GitHub workflow-run pagination.
- [x] Report `AUDIT_MISSING` only when all relevant pages have been consumed, and `UNASSESSED` when the configured maximum is reached without an audit.
- [x] Preserve correctness for multiple target days, HTTP outages, malformed responses, disabled promotion and existing release/audit status semantics.
- [x] Targeted no-network regression tests pass.
- [x] Final PR head passes all five CI checks and Historical Smoke; record actual run URLs and artifact evidence.

## Implementation slices

- [x] 1. Add bounded targeted audit pagination and definitive vs incomplete search classification.
- [x] 2. Add deterministic tests for page-2 success, complete absence, capped uncertainty, multi-day partial match and error on later page.
- [x] 3. Submit scoped PR and observe exact-head CI / Historical Smoke before completion/archival.

## Verification matrix

| Gate | Command or workflow | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_funding_release_watch.py -v` | PASS under Code-level CI #40731389087 |
| Static | `uv run ruff check .` | PASS under CI #40731389087 |
| Code/API/E2E/Agent Plan | `.github/workflows/ci.yml` | all five checks SUCCESS, CI #40731389087 |
| Historical Smoke | `.github/workflows/historical-smoke.yml` | SUCCESS, run #40731389320 |

## Decision gates

None: this is a conservative read-only diagnostics correction inside approved Option A.

## Evidence log

- 2026-10-28: PR #160 opened from branch `agent/funding-watch-bounded-audit-pages-85`; source change `3ba3faa129d8cdf8b0b39edc6567b001f01db4ce`, offline tests `7a953293c02c032a14e02c81f83a9921bcaa6e93`. Initial exact-head CI `40731295246` and Historical Smoke `40731295260` were SUCCESS; subsequent final HEAD was checked separately.
- 2026-10-28: GitHub connector inspected `main`, Issue #85 OPEN/BLOCKED_EVIDENCE, PR #159 merged and current watcher source/test; latest baseline `81d5517520f1f8b68aa742c736c09b904cca54cb`.

## Deviations and discoveries

None: full-page GitHub Release audit discovery is bounded at 10 pages and never silently upgrades an incomplete scan to `AUDIT_MISSING`.

## Resume from here

Completed; future work on Issue #85 resumes from the parent Option A plan, not this archived slice. Do not replay a finished PR just to create new evidence.

## Completion

Final commit: `43fa24ce1cc333e4be6bcfa091182b01f59c6fa0` (PR #160 squash merge)
CI run: [#40731389087](https://github.com/pkking/future-opportunity/actions/runs/40731389087) five required checks SUCCESS at exact HEAD `8b12a085fb35352ded734601b88e233f460a07bc`; [Historical #40731389320](https://github.com/pkking/future-opportunity/actions/runs/40731389320) SUCCESS; postmerge main [CI #40733786300](https://github.com/pkking/future-opportunity/actions/runs/40733786300) SUCCESS
E2E artifact: GitHub Actions ID `12834634634`, SHA256 `d639bf2c641cb19a24cb243986b988cf3f3504960a522b8dd53b6004aa5f8ccb`
Remaining unassessed items: historical OKX first publication, unobserved Funding negative-low regime, 32/90 Funding pinned (58 short).

## Final evidence (2026-10-28)

PR #160 merged after full final-head validation. This archive is completion-only, contains no code changes. The read-only watcher was subsequently reused by the 2026-10-23..28 main-push original continuity audit [#40734065510](https://github.com/pkking/future-opportunity/actions/runs/40734065510), which succeeded on the expanded six-day source window. That does not provide upstream exchange publication authentication.
