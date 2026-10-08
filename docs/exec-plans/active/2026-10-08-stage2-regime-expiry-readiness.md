# 2026-10-08-stage2-regime-expiry-readiness

Issue: #57
Status: IMPLEMENTING
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
- Funding selection may consume only independently sourced features timestamped strictly before entry at 00:15 UTC; no return labels, qualified flags, or realized economics can enter the input.
- Funding fixed 2x2 stratification: sign of prior observed funding rate and trailing realized spot volatility (<100bps vs >=100bps); explicitly a research stratification threshold, **not an economics gate**.
- Reject duplicate dates, missing source identity, future-dated observations, post-entry feature windows, schema drift and quota shortfalls.
- The resulting Funding artifact is a research pre-registration candidate and must not be represented as an accepted acquisition-ready selection provenance; handoff requires independent source authentication/ADR review.
- No promotion, capital deployment, economic-threshold activation or automatic workflow modification.

## Acceptance criteria

- [ ] Fixed Cash 2025 Q3/Q4 source probe records each selected source date, chain archive and exact expiry member; missing/error cases remain explicit.
- [ ] Cash source probe uses official OKX module-4 BTC-USDT FUTURES evidence, without changing existing Cash samples.
- [ ] Funding sampler deterministically replays 2x2 regimes and source identity, rejects future leakage, duplicate candidate dates and ambiguous data.
- [ ] No date substitution after sampling outcomes; insufficient quota remains insufficient.
- [ ] Selection evidence explicitly indicates not approved for acquisition/promotion until provenance bridge and source validation.
- [ ] Unit tests cover Cash status and Funding sampler invariants.
- [ ] Read-only workflow artifacts and operator handoff instructions.
- [ ] All five required CI jobs and Historical Smoke pass on PR review and final heads.
- [ ] Completed plan, squash merge, main validation and issue closure.

## Implementation slices

- [x] 1. Inspect historical sampling/corpus/catalog and identify two separate evidence gaps.
- [x] 2. Create Issue #57, branch and plan.
- [ ] 3. Add Cash multi-quarter archive read-only probe + tests/workflow.
- [ ] 4. Add Funding pre-entry regime research sampler + tests/CLI.
- [ ] 5. Document observed/prospective boundaries and next decisions.
- [ ] 6. Open PR, verify first-head CI/Smoke.
- [ ] 7. Archive, final-head CI/Smoke, merge and verify main.

## Verification matrix

| Gate | Result |
|---|---|
| Cash pinned and expiry cohorts | 30 / 2 |
| Funding pinned / qualified | 32 / 0 |
| Cash candidate source (2025 Q3/Q4) | unassessed before probe |
| Funding source feature identity | not yet authenticated |
| Funding selection | research-only; no promotion |
| Stage-2 decisions | approved for both, economics disabled |
| Required CI / historical Smoke | pending |

## Resume from here

Add a small read-only Cash Q3/Q4 probe (fixed representative dates and explicit status), plus fail-closed research-only Funding stratifier. Run CI and capture any workflow evidence; do not select acquisition waves until feature source identity and future expiry evidence have been verified.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: source probe, regime sampler, tests, evidence verification, governed merge
