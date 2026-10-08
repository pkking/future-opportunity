# ADR-0008: Funding Stage-2 Historical Distribution Gate

- Status: Accepted
- Date: 2026-10-08
- Supersedes: none
- Extends: ADR-0007

## Context

ADR-0007 permits a strategy to propose Stage-2 distribution-gate semantics after at least 30 distinct pinned market days, while preferring 90 days before freezing stable thresholds.

Funding Carry now has 32 distinct pinned market days. The current historical report shows:

- 32 evaluated cases;
- 0 qualified cases;
- pinned-case qualification rate = 0;
- expected net return assessed for 32/32 cases;
- no assessed realized-return distribution because no case qualified;
- 29/32 days (90.625%) selected through pre-registered sampling;
- market-wide opportunity arrival rate remains unassessed;
- the active historical gate remains `provenance_and_semantics`;
- deterministic reference targets are not used as historical thresholds.

The 32-day evidence is therefore sufficient to design Stage-2 semantics, but it does not by itself justify a realized-return threshold.

## Decision status

Accepted by explicit human approval on 2026-10-08.

Acceptance is limited to the recommended decision-quality posture in this ADR: Stage 2 may make evidence completeness and historical decision semantics machine-verifiable for Funding Carry, while numerical economics gating remains disabled. No realized-return, expected-return, or minimum qualification-rate threshold is approved by this acceptance.

## Decision

### 1. Aggregation unit and window

Use one validated pinned case per distinct entry-market day as the evidence unit.

Define Stage-2 evaluation windows by evidence count rather than wall-clock continuity:

- proposal-eligible: at least 30 distinct pinned days;
- preferred threshold-freezing basis: at least 90 distinct pinned days.

Do not interpret source-unavailable calendar dates as observed zero-opportunity periods.

### 2. Qualification-rate semantics

Use the explicit metric name `pinned_case_qualification_rate`:

`qualified pinned cases / evaluated pinned cases`.

This metric must not be represented as market-wide opportunity arrival rate.

Rejected / zero-opportunity pinned cases remain in its denominator.

### 3. Realized-return semantics

Do not treat rejected cases as realized-return zero.

Conditional realized-return statistics include only qualified cases whose realized-return evidence is sufficiently complete.

Until an approved minimum qualified-case count is reached, realized-return thresholds remain unavailable rather than zero.

### 4. Evidence completeness

A Stage-2 evaluation window should require:

- all included cases to pass provenance and deterministic replay checks;
- at least 80% of pinned days to have pre-registered selection provenance for proposal review;
- 100% assessment coverage for any statistic used as a numerical gate;
- explicit assessed-count fields for conditional statistics;
- no inference of market-wide opportunity arrival rate from pinned-case sampling.

Threshold freezing should prefer 100% pre-registered provenance or explicitly document remaining legacy cases.

### 5. Current Funding interpretation

Current Funding evidence:

- satisfies the >=30-day proposal threshold;
- satisfies the proposed >=80% pre-registration criterion;
- has complete expected-net-return assessment coverage;
- does not have any qualified-case realized-return sample.

Therefore this proposal does **not** recommend activating a realized-return gate now.

## Deferred product choices

The following are deliberately deferred and require a future explicit human approval before any numerical economics gate is activated:

1. **Gate purpose**
   - A. Implementation/decision-quality gate: historical CI primarily verifies correct qualification/rejection semantics.
   - B. Economic-attractiveness gate: historical CI also requires a minimum frequency or distribution of economically attractive pinned cases.

2. **First Stage-2 numerical statistic**
   - A. Pinned-case qualification rate.
   - B. Expected-net-return distribution across all pinned cases.
   - C. Conditional realized-return distribution, but only after enough qualified cases exist.
   - D. No numerical economics gate yet; keep Stage 1 until the evidence base matures.

3. **Minimum qualified-case count before realized-return gating**
   - Candidate values should be justified statistically and are intentionally not fixed by this draft.

4. **Threshold-freezing evidence level**
   - A. Allow freezing after >=30 days.
   - B. Require ADR-0007's preferred >=90 days.

5. **Pre-registration requirement at threshold freeze**
   - A. >=80%.
   - B. 100%, excluding or separately reporting legacy-untracked cases.

## Recommended approval posture

For the current corpus, the approved posture is:

- gate purpose A: implementation/decision-quality;
- option D for the first economics gate: do not activate a numerical economics threshold yet;
- continue reporting pinned-case qualification rate and expected-net-return distribution;
- wait for qualified-case realized-return evidence and preferably >=90 pinned days before freezing stable economic thresholds.

This recommendation avoids converting a correctly negative 32-day historical sample into an arbitrary passing/failing economic target.

## Consequences

- The existing provenance-and-semantics historical gate remains active; Stage-2 decision-quality readiness is additive observability and does not replace it.
- Historical negative markets remain first-class evidence.
- Zero qualified cases are represented explicitly rather than as zero realized returns.
- The repository can accumulate decision-ready distribution evidence without silently redefining product success.
- Funding may progress independently in design evidence while Cash remains below the 30-day proposal threshold.

## Evidence

See `docs/research/funding-stage2-design-evidence-32-days.md`.

Primary final smoke evidence:

- workflow run `37710601449`;
- artifact `11521697208`;
- digest `sha256:7cbdc484176ae0c167b6c0d8124d107c46a4b89a6d0072e03331bacb31237c5c`.

## Approval record

- Approved: 2026-10-08
- Approved direction: implementation/decision-quality Stage 2 for Funding Carry; no numerical economics gate yet.
- Stable economic threshold preference: continue collecting qualified-case evidence and prefer at least 90 pinned days before freezing thresholds.
- Explicitly not approved: positive qualification-rate thresholds, expected-return thresholds, realized-return thresholds, or market-wide opportunity-arrival claims.
