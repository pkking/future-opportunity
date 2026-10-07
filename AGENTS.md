# AGENTS.md

This file is the canonical repository-wide contract for coding agents working on
`future-opportunity`. Treat it as the map, not the encyclopedia.

## 0. Read this first

Before any non-trivial change, read these sources in order:

1. `docs/design-baseline-v0.1.md` — frozen product/domain architecture.
2. `docs/v0-implementation-status.md` — what is actually implemented now.
3. Relevant files under `docs/adr/` — accepted design decisions.
4. `docs/agents/workflow.md` — mandatory agent execution protocol.
5. `docs/agents/testing.md` — CI, E2E, evidence, and observability contract.
6. The active execution plan under `docs/exec-plans/active/` for the task.

If a closer `AGENTS.md` exists below the working directory, follow it in
addition to this file; the closer file may add stricter local rules.

## 1. Non-negotiable product invariants

- V0 is paper trading only. Exchange adapters are read-only.
- Never add authenticated trading, order submission, or write-capable exchange
  calls without a new ADR and explicit human approval.
- Users consume `Opportunity`, not raw exchange responses.
- `StrategyDefinition` and `StrategyPlan` are different concepts.
- Every `StrategyPlan` references the exact `OpportunityObservation` used to
  create it and freezes economics, capital policy, and execution-cost policy.
- `Position` represents the complete arbitrage combination and is derived from
  immutable execution/fill evidence.
- Unknown evidence is `UNASSESSED`; never silently convert unknown to zero.
- Unqualified Opportunities may be observed and persisted but must not execute.
- Returns must be attributable. Risks must be explained by explicit invariants.
- Domain code must not depend on exchange SDKs, HTTP frameworks, or persistence.
- PostgreSQL aggregate changes, domain events, and outbox records must remain
  transactionally consistent.
- Financial calculations use `Decimal`; do not introduce binary floating-point
  into domain economics.

## 2. Mandatory agent workflow

For every non-trivial task:

1. **Inspect** current code, tests, design baseline, ADRs, and active plans.
2. **Plan before editing.** Create or update
   `docs/exec-plans/active/<work-id>.md` from the template.
3. **State acceptance criteria** as observable facts, not intentions.
4. **Identify decision gates.** Stop only for a material product/domain/
   architecture/safety decision. Do not stop for routine implementation choices.
5. **Implement in checkpoint-safe increments.** Each increment should leave a
   coherent repository state and update the execution plan.
6. **Run targeted verification** immediately after the affected slice changes.
7. **Run the complete CI-equivalent validation** before claiming completion.
8. **Record evidence**: commands, CI run URL/ID, artifact paths, important
   metrics, failures, and unresolved evidence.
9. **Move the plan** from `active/` to `completed/` only after all required
   gates pass. If interrupted, leave it in `active/` with an explicit resume
   checkpoint.

Trivial documentation/typo-only changes may skip a full execution plan, but they
still must obey applicable tests and evidence rules.

## 3. Interruptibility and reproducibility

Agent work must be resumable by another agent without relying on chat history.

The active execution plan is the source of truth for work-in-progress and must
contain:

- objective and user-visible outcome;
- current repository/CI state;
- decisions already accepted;
- files changed or expected to change;
- ordered implementation steps with status;
- exact verification commands;
- evidence collected so far;
- blockers or decision gates;
- **Resume from here**: the next concrete action.

Do not keep essential state only in an agent scratchpad, terminal history, or
conversation.

## 4. Testing gates

A change is not complete until the relevant CI gates pass:

- **Static/code quality** — lint and repository architecture/safety guards.
- **Code-level tests** — domain, application, adapter, persistence, migration,
  lifecycle, and regression tests.
- **API contract tests** — REST/OpenAPI behavior and paper-only surface.
- **E2E strategy acceptance** — deterministic replay through the public
  application workflow, checked against versioned strategy targets.
- **Evidence artifacts** — E2E produces machine-readable actual-vs-target
  metrics and test reports that CI uploads even on failure.

See `docs/agents/testing.md` for exact commands and evidence schema.

Never write "tests pass", "strategy works", or "target achieved" unless the
corresponding command/CI evidence exists.

## 5. Strategy E2E rules

E2E tests must validate business outcomes, not only HTTP 200 responses.

At minimum they must prove:

- discovery/qualification semantics;
- exact Observation -> Plan traceability;
- paper execution creates delta-neutral Position within target;
- risk invariants have explicit states;
- expected/realized or expected/partial return semantics are correct;
- strategy-specific acceptance targets are met;
- evidence completeness/unassessed components are visible.

CI-gating E2E must be deterministic and offline: use committed, versioned replay
fixtures or synthetic reference scenarios. Live exchange checks may exist as
non-gating diagnostics, never as the only proof.

## 6. No-hallucination / evidence discipline

Agents must distinguish:

- **fact** — supported by repository code, test output, CI, official API docs, or
  a captured artifact;
- **assumption** — explicit and versioned in a plan/ADR/config;
- **unassessed** — evidence is unavailable;
- **proposal** — not yet accepted or implemented.

Never infer successful behavior from code inspection alone when the behavior is
testable. Never convert a failing/flaky external call into a passing conclusion.

For external exchange semantics, prefer official API documentation plus adapter
contract tests. Preserve the normalized domain boundary.

## 7. Change governance

Create a new ADR before changing any frozen boundary listed in
`docs/design-baseline-v0.1.md`, including:

- domain boundaries or Opportunity semantics;
- StrategyDefinition / StrategyPlan separation;
- Position source of truth;
- return or risk models;
- paper/live safety boundary;
- persistence/outbox architecture;
- execution architecture;
- capital/liquidity policy with materially different user semantics;
- new external framework dependencies that affect the architecture.

Routine implementation inside an accepted decision does not need an ADR.

## 8. Commit and review discipline

- One coherent intent per commit.
- Do not rewrite public history.
- Keep migrations append-only after they have been applied; checksum drift is a
  hard error.
- Include tests in the same change that introduces behavior.
- Prefer vertical slices over horizontal framework scaffolding.
- Do not weaken, delete, or bypass a failing safety/architecture test merely to
  make CI green.
- If a test expectation is wrong, explain the changed business fact in the
  execution plan and update the governing ADR/spec when required.

## 9. Repository map

- `src/future_opportunity/domain/` — business concepts and invariants.
- `src/future_opportunity/application/` — use cases and repository/market ports.
- `src/future_opportunity/adapters/` — exchanges, execution, persistence.
- `src/future_opportunity/api.py` — REST boundary.
- `src/future_opportunity/cli.py` — CLI boundary.
- `src/future_opportunity/web/` — basic workbench UI.
- `migrations/` — append-only PostgreSQL schema migrations.
- `tests/` — code/API regression tests.
- `tests/e2e/` — deterministic strategy acceptance tests and local AGENTS rules.
- `docs/adr/` — architectural decisions.
- `docs/exec-plans/` — resumable agent plans and evidence.
- `tests/e2e/strategy-targets.json` — versioned E2E business targets.

## 10. Definition of done

A task is done only when:

- implementation matches the accepted plan and architecture;
- required code/API/E2E tests exist and pass;
- CI is green for the final commit;
- E2E evidence artifact shows actual values against declared targets;
- docs/ADRs are synchronized;
- no critical evidence is left only in chat;
- the execution plan records the final evidence and is moved to `completed/`.

If any item is missing, report the work as partial, blocked, or unassessed.

## 11. GitHub task identity and PR integrity

- GitHub Issues are canonical for task identity; a non-trivial active plan must include a top-level `Issue: #N` pointing to an open, real GitHub Issue.
- Each new non-trivial PR body must include exactly one `Issue: #N` and one `Plan: docs/exec-plans/active/<work-id>.md` line, both referring to the same tracked task.
- Do not treat an Issue status, a commit subject, or an old CI run as evidence of product acceptance. PR checks prove only the tested revision; merge and acceptance remain separate gates.
- `Agent plan integrity` CI checks task traceability. It must not replace static, code, API, E2E, historical replay, or human review requirements.
- Only previously existing PRs #1-#4 that change exclusively committed historical fixture files may use a legacy transition exception. Any new code or workflow modifications require the full contract.
- Before resuming from `Resume from here`, reconcile the plan with the current Git head, PR status, and the CI runs that actually tested it. Resolve any drift before marking steps complete.
- Changes to this governance contract and its validator require careful human review; normal contributor approval is not a substitute for branch Ruleset enforcement.
