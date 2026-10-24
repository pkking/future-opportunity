# Funding prospective Release: audited 2x2 regime coverage (read-only)

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Make the existing GitHub-only daily Funding Release watcher report which of the four **fixed** Funding sign × trailing spot volatility regimes were actually observed in **independently audited, pre-entry GitHub-hosted** immutable releases, with explicit missing/unassessed dates. This is an operational evidence *inventory*, NOT acquisition-eligible historical cohort evidence.

## Non-goals

- No new OKX request, rerun, VPS/token/systemd change, GitHub write in the monitor, historical backfill, corpus pinning, promotion, economics gate, or trading.
- No attempt to prove exchange-signed or OKX-as-of publication from GitHub timestamps.
- No calculation of opportunity or profitability rates, no tuning of the frozen 100bps regime threshold, no extrapolation outside checked dates.
- No persistent cumulative cohort count: this report covers exactly the current bounded 1..7 checked UTC dates, not all market days.

## Current facts

- Main baseline: `10b9ccb133bded53e6d0c0b39bbb489fd4a3e476`; no open PRs when work began.
- Existing `scripts/check_funding_release_watch.py` independently checks immutable public original ZIP/manifest, strict replay and matching successful `release.published` audit.
- Existing report already carries verified per-day `regime`, or a precise missing/audit-failure status; watcher looks back three days, maximum seven.
- Original 2026-10-23 release was timely; on 2026-10-24 a new immutable release published at 00:00:15Z with original ZIP digest `d3961babf389449900dff7f56b3006291459ebb8776de2c03abff944af33894b`. Independent audit Run #40042736659 and watcher Run #40064545177 both concluded success.
- Legacy scheduled capture Run #40052039585 failed despite successful production VPS->GitHub evidence; these paths are independent.
- Funding pinned 32 / Cash pinned 66 as previously validated; Issue #85 retains BLOCKED_EVIDENCE until separate exchange-source publication and negative/low regime proofs.

## Safety and design constraints

Follow `AGENTS.md`, `docs/agents/workflow.md`, `docs/agents/testing.md`, ADR-0008, and the active parent plan `docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md`.

An inventory entry is verified only when the **same day** has `RELEASE_AND_INDEPENDENT_AUDIT_VERIFIED` plus both `github_hosted_preentry_source_verified=true` and `github_release_attestation_verified=true` and a recognized frozen regime. All other days are excluded from four bucket counts and remain explicit, even if a regime field is present. Every report must keep false exchange publication, acquisition, promotion and market-wide inference flags.

## Acceptance criteria

- [x] Deterministic 2x2 counts and exact unique observed day lists from strict audited daily watcher records, no double count, no bucket manipulation.
- [x] Explicit checked count, audited count, non-audited dates/status, and empty strata; no unsupported research/promotion eligibility.
- [x] Fail closed for unknown regime or inconsistent verified flags, without concealing that day's broken evidence; watcher must not incorrectly return HEALTHY.
- [x] Deterministic offline regression covering one/multiple days, missing/failed audits, unverified regime labels, duplicates, wrong status flags, and 4 fixed classes; no network or exchange credential.
- [ ] Run targeted tests and repository CI including five required checks + Historical Backtest Smoke on final head. No corpus changes.
- [x] Update operational runbook to document the output and its limitations.

## Implementation slices

- [x] 1. Add a strictly guarded audited-release regime inventory to the existing watcher report.
- [x] 2. Add deterministic tests for complete and partial windows, malformed records and non-promotion invariants.
- [ ] 3. Run final-head CI + Historical Smoke, review/merge, and separately archive the plan only after CI evidence. Runbook updated.

## Verification matrix

| Gate | Command / evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_release_watch.py` | Pending |
| Static | `uv run ruff check .` | Pending |
| Full code/API/E2E/plan | GitHub `CI` workflow on exact PR head | Pending |
| Historical | `Historical Backtest Smoke` exact PR head | Pending |

## Decision gates

None: this is read-only additive operational observability inside accepted Issue #85 and ADR-0008 semantics. Do not take a new trade/economics/source-promotion decision implicitly.

## Evidence log

- 2026-10-24: Implementation commit `2b51fe4431df14e6af494a6f7b42e59690a983ef` adds strict audited 2x2 summary; test commit `f7049c5678702190ae7fefa45c96baff0a2f4a2d` covers trusted/untrusted regimes; runbook commit `ef8a9afb56fdf5fc674ced89c50a8eb6a8ec9ffa`. Runtime verification remains PENDING CI.

- 2026-10-24: GitHub Releases API independently showed 2026-10-24 immutable publication at 00:00:15Z. Audit #40042736659 and watcher #40064545177 concluded SUCCESS on main `10b9ccb`. Historical exchange-publication authenticity remains UNASSESSED.

## Resume from here

Implementation and deterministic tests are committed on the task branch; next inspect exact PR-head CI and Historical Backtest Smoke. Fix real failures without relaxing the safety assertions. Do not merge or archive until the final head passes.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed: independent OKX publication time, true acquisition eligibility, missing negative/low regime and operator VPS preflight.
