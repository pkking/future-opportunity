# 2026-10-08-cash-2025-quarter-preparation-handoff

Issue: #63
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Convert the immutable 2025 Cash Q3/Q4 12+12 outcome-blind selection into exact, replayable preparation manifests and a dispatch-only workflow. This stage **does not** assert valid 00:15 actual market data or authorize promotion.

## Evidence baseline

- Frozen 24 dates merged in PR #62, main 1b4ca2af66946f412edc3a7e3a7443d740a4a87b.
- Official source capacity run 37754484440, artifact 11539801691, 87/87 Q3 FUTURES archives, 90/90 Q4, fixed SPOT 6/6 and futures exits 2/2.
- Selection control run 37755705789; artifact 11539833591 digest sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74.
- Q3 replay SHA 3449f56506669a382dbc6c7290d762a00d518a84bebc9530eb904c03e3ab70cd; Q4 SHA 97c3b6c4f296e5819055eace56b5c396c317e285051ea142be2dcb8799073f8b.

## Frozen policy

- Entry 00:15 UTC on each selected market date.
- Q3 future BTC-USDT-250926; exit 2025-09-25T00:15:00+00:00, planned expiry 2025-09-26T08:00:00+00:00.
- Q4 future BTC-USDT-251226; exit 2025-12-25T00:15:00+00:00, planned expiry 2025-12-26T08:00:00+00:00.
- Future/spot 00:15 source completeness and historical instrument metadata must be independently checked during preparation.
- No outcomes available for frozen dates and no replacement dates permitted.

## Constraints

- Never modify frozen 24 market days, source artifact identity or pre-registration parameters.
- Keep existing Cash 30 pinned / Funding 32 pinned unchanged.
- Use only the canonical, fail-closed historical acquisition manifest format and its selection provenance replay.
- Workflow_dispatch only; no corpus mutation or promotion.
- Individual failures remain explicit. No profitability-driven date substitution.
- Stage-2 economic gate stays disabled.

## Acceptance criteria

- [ ] Q3 and Q4 exact manifests each contain 12 pinned-control dates and approved 2025 quarter future/exit.
- [ ] Selection provenance is valid and deterministically replayable against artifact 11539833591.
- [ ] Q3+Q4 are disjoint and equal exact frozen 24-day selection, no prior pinned overlap.
- [ ] Workflow_dispatch permits exactly q3/q4 and uses existing read-only acquisition framework.
- [ ] Tests enforce source identities, dates, no economics or promotion side effects.
- [ ] Required 5/5 CI and Historical Smoke success at review/final heads.
- [ ] Plan archived, squash merge, main counts unchanged, Issue closed after verification.

## Implementation slices

- [x] 1. Read prior acquisition schema and frozen quarter control, create Issue #63/branch/plan.
- [ ] 2. Add Q3/Q4 exact acquisition manifests with approval provenance.
- [ ] 3. Add dispatch-only workflow and test matrix.
- [ ] 4. Document source preflight gate and manual workflow handoff.
- [ ] 5. PR review, CI/Smoke, archive, final CI/Smoke, merge and verify main.

## Verification matrix

| Gate | Expected |
|---|---|
| Q3 cases | 12, BTC-USDT-250926 |
| Q4 cases | 12, BTC-USDT-251226 |
| Selection control source | 37755705789 / 11539833591 |
| Existing Cash/Funding pinned | 30 / 32 |
| Historical gate | provenance_and_semantics |
| Economics gate | disabled |
| Preparation dispatch | explicit user-controlled q3 and q4 |
| Promotion / pinned corpus mutation | none |
| CI / Smoke | pending |

## Resume from here

Commit two replay-validated manifests and a dispatch-only workflow. Do not dispatch or promote expensive historical preparation on a repository push. When the PR merges, the operator may run q3 and q4 separately; review complete raw source and actuals evidence for every selected date before any campaign planning.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: manifests, workflow, tests, gated merge, live preparation
