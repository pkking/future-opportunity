# ADR-0009: Cash Stage-2 Decision-Quality Observability

- Status: Accepted
- Date: 2026-10-08
- Extends: ADR-0007, ADR-0008 (Funding-only approval remains unchanged)
- Human approval: explicitly granted 2026-10-08; scope is decision-quality observability only

## Context

Cash-and-Carry has 30 distinct pinned entry-market days following PR #52. Main run 37747210353 reports 27/30 (90%) pre-registered, expected returns assessed in 30/30, 8 qualified cases, and complete realized-return evidence for all 8 qualified cases. Twenty-two cases are rejected, and rejection reason totals overlap.

The two expiry cohorts (March 27 and June 26) contain 12 and 18 cases, of which 5 and 3 qualify. Horizons range from 5–81 and 2–89 calendar days. Same-expiry returns are correlated by shared close dates and market exposure; they are not independent trials.

This satisfies the factual Stage-2 evidence prerequisites already described by ADR-0008, but that ADR was accepted for **Funding Carry only**. ADR-0009 separately authorizes Cash Stage-2 decision-quality observability as approved on 2026-10-08.

## Accepted decision

1. Permit Cash to participate in the **decision-quality evidence framework only**, with the same >=30 distinct pinned market-day threshold, >=80% pre-registered selection coverage, 100% expected-net-return assessment, and conditional realized-return completeness reporting.
2. Keep the `provenance_and_semantics` historical gate in force. Keep `economics_gate=disabled`, and require another human approval before any numeric qualification, expected-return, or realized-return gate.
3. Separate `evidence_requirements_met` from `enabled` and `decision_quality_ready`. Satisfying factual requirements does not imply human authorization.
4. Report Cash expiry cohorts and actual holding-period distributions to expose horizon variation and non-independent market observations; no annualized returns or market-wide opportunity rate inference.
5. Continue pre-registering acquisition dates before observing economics, with emphasis on additional contract expiry cohorts. Prefer >=90 pinned days and multiple expiry periods before proposals for stable economics thresholds.

## Explicitly not approved

- Enabling Cash for decision-quality reporting is approved here; this approval does not extend to any historical economics gate.
- No positive qualification-rate, realized-return, expected-return, minimum-win-rate, or minimum-profitable-case gate is approved.
- No claim is made that 8 fully assessed qualified cases or two expiry cohorts suffice to estimate independent expected performance.
- No existing historical fixture, production strategy rule, contract selection, or funding ADR is changed by this proposal.

## Consequences

- Cash is authorized for Stage-2 decision-quality reporting so long as factual evidence prerequisites remain satisfied.
- The active history gate will remain Stage 1 provenance and deterministic semantics.
- Cash can be observed and compared with Funding without conflating zero qualified cases with zero realized return, and without conflating differing holding horizons.
- Future economic gate choices remain open and must be supported by stronger multi-expiry and out-of-sample evidence.

## Evidence

- `docs/research/cash-stage2-decision-evidence-30-days.md`.
- Historical Smoke run `37747210353`, evidence artifact `11536670411` (digest `sha256:762ef5d6f7f10fc4ccc37e75cf722012af65ad91c383fb260e97c33aca033950`).
- Corpus merge `a5124f804a603731a55125563959e1c6811a10d8`.

## Approval record

- Proposal authored: 2026-10-08.
- Human approval: **granted 2026-10-08**.
- Approved scope: Cash decision-quality observability, with no numerical economics gating.
- Strategy approval provenance: Funding Carry remains ADR-0008; Cash-and-Carry is ADR-0009.
- Approved enabled strategies: Funding Carry and Cash-and-Carry.
- Economics gate and historical gate: remain `disabled` and `provenance_and_semantics` respectively.
- Explicitly not approved: profit-rate, annualized-return, qualification-rate, expected-return or realized-return acceptance thresholds.
