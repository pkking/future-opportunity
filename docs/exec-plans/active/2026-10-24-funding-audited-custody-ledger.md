# Bounded prospective Funding audited-custody history report

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Provide a **reproducible, bounded longitudinal inventory** of existing prospective Funding immutable GitHub Releases across an explicit date window (1–90 complete UTC days). Reuse the established per-day original ZIP/manifest strict replay and exact release.published independent audit, and the recently merged fixed four-stratum regime inventory. This makes multi-week evidence coverage and missing data observable without suggesting that GitHub custody proves exchange-signed publication.

## Non-goals

- No OKX requests, historical acquisition, campaign promotion, publication backfill, strategy profitability/market arrival claims, source modification, authenticated trading or changed 100bps regime definitions.
- No new scheduled polling/job (one-time path-triggered GitHub read-only diagnostic is allowed), persisted corpus, automatically generated historical fixture or external storage.
- No new exchange provenance policy, automatic Stage-2 admission or acceptance criteria.

## Current facts

- Main after PR #142: `10ca4ea53e8a91486b68e19754be198f9f8a0a32`; postmerge main CI #40098685646 SUCCESS.
- PR #141 merged a strict per-day 2x2 audited regime summary into the 1–7-day operations watcher; all five final-head CI jobs and Historical Smoke SUCCESS.
- The immutable GitHub Releases for 2026-10-23 and 2026-10-24 published by UTC 00:00:15 and their release.published audits succeeded.
- GitHub original-source custody timestamp is not the OKX source's independently verified historical publication time. Funding 32 / Cash 66 pinned days remain separate from prospective daily evidence.

## Constraints

Obey repository AGENTS.md, ADR-0008, current active parent plan (Issue #85), design-baseline V0 paper-only, and the existing `scripts/check_funding_release_watch.py` acceptance semantics. The daily function must continue to fail closed for missing/non-immutable/invalid evidence, and a successful independent audit must match exactly the Release tag. No market API calls, source retention changes or new write permissions.

## Acceptance criteria

- [x] Explicit canonical inclusive UTC start/end, within prospective first date 2026-10-23, at most 90 complete days; reject invalid/future/out-of-bounds windows before HTTP.
- [x] Read-only GitHub audit-run pagination with bounded pages and no silent truncation; fail closed when the relevant run list cannot be established.
- [x] Reuse existing day-level Release asset hash/original ZIP replay and matching successful independent release.published verification; duplicate/invalid/unassessed days excluded from verified regimes.
- [x] Exact date-by-date source status, total audited/checked/missing counts and four stable regime buckets; no sampling/returns inference, false provenance/promote flags.
- [x] CLI emits review artifact without overwriting an existing report; report remains UNASSESSED on incomplete or failed evidence.
- [x] Offline no-network regression tests for clean 2+ day report, missing day, independent audit failure, pagination boundary/truncation, time range invalid, no POST/exchange calls.
- [ ] Final exact-head CI five jobs + Historical Backtest Smoke all SUCCESS; up-to-date README/runbook and PR with valid Issue/Plan.
- [ ] Human review then merge, postmerge CI; separate completed plan archival.

## Implementation slices

- [x] 1. Implement bounded GitHub-only 90-day audit and regime-history script.
- [x] 2. Add deterministic unit and integration-style MockTransport tests.
- [x] 3. Document safe manual use, freshness limitations and interpretation, including opt-in GitHub Actions diagnostic.
- [ ] 4. Final-head CI/Historical Smoke, merge/reconcile main CI, then archive independently.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Source offline | Covered by code-level tests in CI #40099281056 on implementation head `332860b` | PASS |
| Ruff/architecture | CI #40099281056 static architecture | PASS |
| CI code/API/E2E/plan | CI #40099281056 five SUCCESS on implementation head `332860b`; checkpoint commit will require its own fresh CI | IN PROGRESS |
| Historical | #40099281118 SUCCESS on implementation head `332860b`; checkpoint commit requires its own smoke | IN PROGRESS |

## Decision gates

No decision to approve new source standards is made. A future explicit ADR/human gate remains required before changing historical source publication policy or funding economics. This is an auditable *diagnostic ledger* only, not an acceptance protocol.

## Evidence log

- 2026-10-24: Implementation HEAD `332860b000b121cc904f24e6b82ef8e2ca59dfa9` passed all five CI jobs https://github.com/pkking/future-opportunity/actions/runs/40099281056 and Historical Backtest Smoke https://github.com/pkking/future-opportunity/actions/runs/40099281118. E2E artifact ID `12562590506` / `sha256:b2097e1df1700abd8eb531db40061062fcf839f6b49892a3a18df6a1389af6c0`; historical artifact ID `12562501008` / `sha256:243647bf18cd79348cf255bbf1c781f7dac6f24c5df508df00cd4becb5a57eda`. After this evidence-only checkpoint commit, CI and Smoke must be verified afresh on the exact PR head. No real longitudinal workflow has executed yet.

- 2026-10-24: Added opt-in `review-funding-prospective-custody.yml` read-only Actions diagnostic (workflow_dispatch + one-time main path-triggered preview; no schedule), bounded pagination negative tests, original source remains an immutable GitHub Release. Real external diagnostic has NOT run yet; verification is pending. Implementation commit `e52a546b4ec451fa286ea4655a66ce2eb3153c06`, tests `85e685a03ebb7ccaaab151de96bb098d79526c36`.

- 2026-10-24: First implementation committed on branch: `scripts/report_funding_prospective_custody_ledger.py` commit `6c8fbb3db010ab33f2fb4981e4b4cf5abf045324`, offline MockTransport tests `4fe54223cfc1b78b16ed0e046470b6af2ac2fe11`, operator runbook `a9e06e5aad04acad5c05efd1593ec9d9c048239e`. All verification remains PENDING until CI executes; no live source request performed.

- 2026-10-24: Starting from merged and CI-validated main `10ca4ea53e8a91486b68e19754be198f9f8a0a32`. Independent published Release audit runs 2026-10-23/#39875400476 and 2026-10-24/#40042736659 are successful. Previous 90-day retention limit applies to derived Actions Artifacts, not immutable Releases.

## Resume from here

Verify the new checkpoint-only PR #143 head against all five CI jobs and Historical Smoke, then merge if green. After merge independently verify main CI and the new actual read-only GitHub rollout diagnostic (2026-10-23..24). Record actual evidence, then archive in a separate completion PR. No promotion.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: OKX independently signed as-of publication and negative/low-volatility coverage; historical acquisition remains blocked.
