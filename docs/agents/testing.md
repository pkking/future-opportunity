# Agent Testing, E2E, and Evidence Contract

## Purpose

Tests are executable evidence. They exist to prevent both software regressions
and agent hallucination.

A strategy is not "working" because code looks plausible. It is working only to
the extent demonstrated by repeatable tests and captured evidence.

## CI gate model

Every change must preserve these gates.

### Gate 1 — static and architecture safety

Required:

```bash
uv run ruff check .
```

Architecture tests enforce boundaries such as read-only V0 exchange adapters.

If strict type checking is added as a required gate later, it must first be made
green on the existing baseline; do not introduce permanently failing gates.

### Gate 2 — code-level tests

Run domain/application/adapter/persistence/regression tests:

```bash
uv run pytest tests \
  --ignore=tests/test_api_smoke.py \
  --ignore=tests/e2e
```

This gate includes PostgreSQL integration tests and therefore requires the CI
PostgreSQL service.

### Gate 3 — API contract tests

```bash
uv run pytest tests/test_api_smoke.py
```

API tests must assert business semantics and safety surface, not only status
codes. The OpenAPI surface must not expose live order/trading endpoints in V0.

### Gate 4 — E2E strategy acceptance

```bash
mkdir -p artifacts/e2e
E2E_EVIDENCE_PATH=artifacts/e2e/strategy-evidence.json \
  uv run pytest tests/e2e -v \
  --junitxml=artifacts/e2e/junit.xml
```

CI uploads `artifacts/e2e/` even when the test fails.

### Historical smoke — pinned real-market replay

Historical smoke is an additional offline evidence layer. It does not replace
Gate 4 reference scenarios.

```bash
uv run python scripts/run_pinned_historical_smoke.py
uv run pytest tests/e2e/test_historical_backtest_acceptance.py -v
```

Rules:

- raw exchange archives stay out of git;
- committed historical fixtures must include provenance and checksums;
- compact derived books must state the frozen capital scenario and prove the
  retained depth covers the required base quantity with the declared margin;
- missing historical evidence remains `unassessed`; it is never synthesized;
- historical negative opportunities are valid evidence when the production
  qualification workflow rejects them for the expected reason;
- the historical evidence artifact must be uploaded with `if: always()`;
- until a historical target policy is approved, deterministic reference targets
  may be displayed for comparison but must not be silently reused as historical
  pass/fail criteria.

## What an E2E scenario must cover

A strategy E2E scenario should exercise the real application workflow rather
than directly testing one formula:

```text
Market fixture/replay
  -> Discover
  -> Qualification
  -> OpportunityObservation
  -> StrategyPlan
  -> Paper Execution
  -> Position
  -> Risk
  -> Refresh/Close when applicable
  -> Return attribution
  -> Expected-vs-current/realized
```

The scenario must assert the relevant business target from
`tests/e2e/strategy-targets.json`.

## Strategy target rules

Targets are versioned repository facts.

Each target declares:

- scenario ID;
- strategy and strategy version;
- capital;
- minimum expected or realized return;
- maximum absolute delta percentage;
- required qualification state;
- required evidence completeness;
- required risk invariant states or allowed unassessed states.

Changing a target to make a failing strategy pass is a product/strategy change,
not a test-only change. It requires justification in the execution plan and an
ADR when the underlying return/risk semantics change.

## Determinism

CI-gating E2E must be offline and deterministic.

Allowed evidence sources:

- committed synthetic reference scenarios;
- committed historical replay fixtures with provenance and checksum;
- deterministic seeded generators when the seed is committed.

Not allowed as the only gating evidence:

- current live market prices;
- network-dependent exchange calls;
- wall-clock-sensitive profitability;
- unpinned remote datasets.

Live exchange validation may run separately as a diagnostic/non-gating workflow.

## E2E observability artifact

Every E2E run writes machine-readable evidence.

Minimum fields per scenario:

```json
{
  "scenario_id": "...",
  "strategy": "...",
  "strategy_version": "...",
  "fixture_id": "...",
  "target": {},
  "actual": {},
  "qualified": true,
  "position_state": "...",
  "risk_invariants": [],
  "return_complete": true,
  "unassessed_components": [],
  "passed": true
}
```

The report must contain actual numeric values, not only pass/fail.

CI also stores JUnit output so failures remain inspectable without reproducing
the agent session.

## Evidence semantics

Use these labels consistently:

- **verified** — a test/CI/artifact directly supports the claim;
- **assumption** — versioned input or explicit policy;
- **unassessed** — evidence is unavailable;
- **diagnostic** — informative but non-gating live/external result.

A passing unit test cannot substitute for an E2E target when the claim is about
strategy outcome.

## Failure behavior

On E2E failure:

- preserve the evidence artifact;
- do not lower the target automatically;
- compare target vs actual;
- identify whether the failure is strategy economics, market fixture,
  execution cost, risk invariant, adapter normalization, or test defect;
- record the diagnosis in the active execution plan.

## Adding a new strategy

A new strategy is incomplete until it has:

- StrategyDefinition;
- deterministic E2E scenario;
- versioned acceptance target;
- return/risk evidence;
- API/CLI path;
- CI evidence artifact.

This requirement applies before any future live-execution discussion.
