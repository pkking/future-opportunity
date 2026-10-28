# Bounded multi-page GitHub Release audit discovery

Issue: #85
Status: IMPLEMENTING
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

- [ ] Retrieve older matching Release audit from page 2+ using read-only GitHub workflow-run pagination.
- [ ] Report `AUDIT_MISSING` only when all relevant pages have been consumed, and `UNASSESSED` when the configured maximum is reached without an audit.
- [ ] Preserve correctness for multiple target days, HTTP outages, malformed responses, disabled promotion and existing release/audit status semantics.
- [ ] Targeted no-network regression tests pass.
- [ ] Final PR head passes all five CI checks and Historical Smoke; record actual run URLs and artifact evidence.

## Implementation slices

- [ ] 1. Add bounded targeted audit pagination and definitive vs incomplete search classification.
- [ ] 2. Add deterministic tests for page-2 success, complete absence, capped uncertainty, multi-day partial match and error on later page.
- [ ] 3. Submit scoped PR and observe exact-head CI / Historical Smoke before completion/archival.

## Verification matrix

| Gate | Command or workflow | Status |
|---|---|---|
| Targeted | `uv run pytest tests/test_funding_release_watch.py -v` | pending |
| Static | `uv run ruff check .` | pending |
| Code/API/E2E/Agent Plan | `.github/workflows/ci.yml` | pending |
| Historical Smoke | `.github/workflows/historical-smoke.yml` | pending |

## Decision gates

None: this is a conservative read-only diagnostics correction inside approved Option A.

## Evidence log

- 2026-10-28: GitHub connector inspected `main`, Issue #85 OPEN/BLOCKED_EVIDENCE, PR #159 merged and current watcher source/test; latest baseline `81d5517520f1f8b68aa742c736c09b904cca54cb`.

## Deviations and discoveries

None.

## Resume from here

Implement the bounded multi-page audit lookup in `scripts/check_funding_release_watch.py`, then add no-network tests and push a PR against main.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: historical OKX first publication, unobserved Funding negative-low regime, 32/90 Funding pinned (58 short).