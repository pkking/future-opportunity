# 2026-10-08-stage2-regime-expiry-readiness

Issue: #57
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Improve Stage-2 evidence independence and regime coverage: probe additional Cash expiry quarters via official history without inventing availability, and implement a deterministic Funding regime *research* selection planner based solely on lagged pre-entry market features.

## Current main baseline

- Main head: 9a3261edf14ef97145944f3d283eb8904d5ecda3.
- Cash: 30 pinned entry days, 2 expiry cohorts, 8 qualified with 8/8 complete conditional realized evidence.
- Funding: 32 pinned entry days, 0 qualified cases.
- Both decision-quality enabled (ADR-0008 and ADR-0009). Economics gate remains disabled; active historical gate provenance_and_semantics.

## Constraints

- No change to already pinned fixtures or existing acquisition/provenance policy.
- Cash Q3/Q4 2025 candidate quarter/archive identity is unknown until probed.
- Cash probe dates must be fixed before source query, and resulting missing/ineligible cases must not be silently replaced.
- First actual probe run 37753082901: 2/4 archive identities verified (2025-09-19 and 2025-12-12); 2025-09-12 and 2025-12-19 capped at 128 MiB, not classified as missing. Follow-up probe 37753604956 on the **same four dates**, bounded to 512 MiB, verified all 4/4 exact expiry-future archive identities. Artifact ID 11538678600, SHA256 85083f599a9e85caaf2fbc22e67962c88f1b811bbe34327aed828e01a5dca1d4. This verifies contract existence only; SPOT/exit data remain unassessed.
- Funding selection may consume only independently sourced features timestamped strictly before entry at 00:15 UTC; no return labels, qualified flags, or realized economics can enter the input.
- Funding fixed 2x2 stratification: sign of prior observed funding rate and trailing realized spot volatility (<100bps vs >=100bps); explicitly a research stratification threshold, **not an economics gate**.
- Reject duplicate dates, missing source identity, future-dated observations, post-entry feature windows, schema drift and quota shortfalls.
- The resulting Funding artifact is a research pre-registration candidate and must not be represented as an accepted acquisition-ready selection provenance; handoff requires independent source authentication/ADR review.
- No promotion, capital deployment, economic-threshold activation or automatic workflow modification.

## Acceptance criteria

- [x] Fixed Cash 2025 Q3/Q4 source probe records each selected source date, chain archive and exact expiry member; missing/error cases remain explicit.
- [x] Cash source probe uses official OKX module-4 BTC-USDT FUTURES evidence, without changing existing Cash samples.
- [x] Funding sampler deterministically replays 2x2 regimes and source identity, rejects future leakage, duplicate candidate dates and ambiguous data.
- [x] No date substitution after sampling outcomes; insufficient quota remains insufficient.
- [x] Selection evidence explicitly indicates not approved for acquisition/promotion until provenance bridge and source validation.
- [x] Unit tests cover Cash status and Funding sampler invariants.
- [x] Read-only workflow artifacts and operator handoff instructions.
- [x] PR review-head five required checks success (CI run 37753738444) and Historical Smoke success (37753738435); final archived-head checks must be repeated.
- [x] Complete this read-only evidence phase at source-authentication boundary, archive plan and require final-head CI/Smoke and post-merge main validation before issue closure.

## Implementation slices

- [x] 1. Inspect historical sampling/corpus/catalog and identify two separate evidence gaps.
- [x] 2. Create Issue #57, branch and plan.
- [x] 3. Add Cash multi-quarter archive read-only probe + tests/workflow.
- [x] 4. Add Funding pre-entry regime research sampler + tests/CLI.
- [x] 5. Document observed/prospective boundaries and next decisions.
- [x] 6. Open PR #58, verify review-head CI 37753738444 (5/5 success) and Smoke 37753738435 (success).
- [x] 7. Archive the plan and require final-head CI/Smoke; merge, main verification and issue closure remain mandatory before task close.

## Verification matrix

| Gate | Result |
|---|---|
| Cash pinned and expiry cohorts | 30 / 2 |
| Funding pinned / qualified | 32 / 0 |
| Cash candidate source (2025 Q3/Q4) | 4/4 fixed probe target identities verified in run 37753604956; acquisition still blocked on SPOT/exit evidence |
| Funding source feature identity | not yet authenticated |
| Funding selection | research-only; no promotion |
| Stage-2 decisions | approved for both, economics disabled |
| Required CI / historical Smoke | Review head CI 37753738444 5/5 success; Smoke 37753738435 success |

## Resume from here

PR #58 has passed its review-head CI 37753738444 and Historical Smoke 37753738435. Re-probe run 37753604956 verifies 4/4 identities with immutable artifact 11538678600. Funding feature identity remains unauthenticated, selection is research-only. After archiving and PR body update, revalidate final archival head before squash merge. Post-merge, open follow-up for SPOT/exit source integrity and raw Funding feature lineage; no acquisition/progression is permitted before that evidence.

## Completion

Final commit: 626dce257d1f105fd5a2815a7d8d14c8baba68f4
CI run: 37753738444 (5/5 success); Historical Smoke 37753738435 (success)
Remaining unassessed items: final archived-head CI/Smoke, merge and main verification; real Funding feature-source authentication and Cash SPOT/exit coverage are future work
