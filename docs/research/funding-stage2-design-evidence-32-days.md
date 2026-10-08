# Funding Stage-2 design evidence (32 pinned days)

Status: decision evidence only; does not activate Stage 2.

## Provenance

- Main merge establishing 32 Funding days: `383aa12fa5ef4b6f55d442734db6100a4c5c2b84`.
- Historical Backtest Smoke run: `37710601449`.
- Evidence artifact: `11521697208`.
- Artifact digest: `sha256:7cbdc484176ae0c167b6c0d8124d107c46a4b89a6d0072e03331bacb31237c5c`.
- Active historical gate in the artifact: `provenance_and_semantics`.
- `reference_targets_used_as_thresholds=false`.

## Observed Funding evidence

| Metric | Value | Interpretation |
|---|---:|---|
| Pinned entry-market days | 32 | Meets ADR-0007's per-strategy minimum for proposing Stage-2 design |
| Evaluated cases | 32 | One frozen case per pinned entry-market day |
| Pre-registered days | 29 | 90.625% of Funding corpus |
| Legacy-untracked days | 3 | Validated, but weaker selection provenance |
| Qualified cases | 0 | Current production economics rejected every pinned case |
| Rejected cases | 32 | All rejected |
| Pinned-case qualification rate | 0 | This is not a market-wide opportunity arrival rate |
| Expected-net-return assessed | 32/32 | Distribution is complete for this reporting field |
| Qualified cases with assessed realized return | 0 | No realized-return distribution is available |
| Market-wide opportunity arrival rate | unassessed | Must not be inferred from this corpus |

### Expected net return across all pinned Funding cases

| Statistic | Decimal return | Approx. percent |
|---|---:|---:|
| Minimum | -0.001432718975083680 | -0.1433% |
| P25 | -0.0013358771869091625 | -0.1336% |
| Median | -0.001304108183561355 | -0.1304% |
| Mean | -0.0013090434891949763 | -0.1309% |
| P90 | -0.001239404526487287 | -0.1239% |
| Maximum | -0.001215 | -0.1215% |

All 32 cases fail `expected_net_return_not_positive`; 6 also report `expected_funding_not_positive`.

## What the 32-day corpus supports

1. It supports a statistically explicit statement about the distribution of the scanner's expected-net-return estimate on these pinned cases.
2. It supports a pinned-case qualification-rate statement for the selected evidence corpus.
3. It supports testing that negative / zero-opportunity periods remain stable regression evidence.
4. It does not support a conditional realized-return distribution because there are zero qualified cases.
5. It does not support a market-wide opportunity arrival-rate claim because the sample unit is one frozen case per pinned day, not an exhaustive market scan.
6. It does not yet support stable long-run thresholds at ADR-0007's preferred 90-day evidence level.

## Candidate Stage-2 semantics

### Aggregation window

Recommended: rolling evidence window defined by the latest N eligible, provenance-valid pinned market days per strategy, with N >= 30 for proposal and N >= 90 before freezing stable thresholds.

Why: a count-based window matches ADR-0007's evidence unit and avoids pretending that gaps in source availability are observed zero-opportunity days.

### Qualification-rate semantics

Recommended name: `pinned_case_qualification_rate`.

Definition: qualified pinned cases divided by evaluated pinned cases in the evidence window.

Do not rename or reinterpret it as opportunity arrival rate. With current data it is `0/32 = 0`.

### Return statistic

Current recommendation: do not gate on realized return yet.

Reason: there are zero qualified Funding cases, therefore the conditional realized-return distribution has assessed_count=0. A numerical realized-return threshold would be fabricated.

The only fully observed return-like distribution today is `expected_net_return_all_cases`, but using it as an acceptance threshold would change the question from 'did the strategy behave correctly on history?' to 'did this selected history contain economically attractive opportunities?'. That requires an explicit product decision.

### Zero-opportunity periods

Recommended: keep rejected periods in the denominator of pinned-case qualification rate, but exclude them from conditional realized-return statistics rather than coercing realized return to zero.

### Sample and provenance rules

Recommended minimum proposal rule for Funding:

- >=30 distinct validated pinned days;
- >=80% pre-registered selection provenance;
- 100% expected-net-return assessment coverage if that statistic is used;
- no market-wide opportunity-rate claim;
- realized-return statistic remains unavailable until at least a separately approved minimum number of qualified cases exists.

Current Funding satisfies the first three factual conditions: 32 days, 90.625% pre-registered, 32/32 expected-net-return assessed.

## Decisions that still require human approval

1. Is Stage 2 intended to gate **strategy implementation correctness** or **historical economic attractiveness**? These are different product contracts.
2. Should the first Stage-2 gate be based on pinned-case qualification rate, expected-net-return distribution, or only activate once a conditional realized-return sample exists?
3. What minimum count of qualified cases is required before realized-return statistics become gateable?
4. Is >=80% pre-registered provenance sufficient, or must threshold-freezing wait for 100%?
5. Should threshold freezing wait for ADR-0007's preferred 90 days even if a proposal can be reviewed at 30?

## Recommended decision posture

Keep the active historical gate unchanged for now. Accept the 32-day corpus as sufficient to design and review Stage-2 semantics, but not sufficient to freeze a realized-return threshold. Prefer collecting qualified-case evidence and expanding toward 90 pinned days before stable threshold activation.