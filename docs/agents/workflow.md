# Agent Development Workflow

This is the detailed execution protocol referenced by the repository root
`AGENTS.md`.

## Goal

Make agent-driven development:

- plan-first;
- interruptible at any checkpoint;
- reproducible from repository state;
- evidence-driven;
- safe against silent product-semantic drift.

## Work classification

### Trivial

Examples: typo fixes, link repairs, formatting-only documentation changes.

A dedicated execution plan is optional if the change cannot alter runtime,
tests, API contracts, domain semantics, migrations, or architecture.

### Non-trivial

Anything that changes code, tests, API/CLI behavior, persistence, strategy
economics, risk, execution, market normalization, or CI is non-trivial.

A non-trivial task MUST have an active execution plan before implementation.

## Execution-plan state machine

Use one of these states:

```text
PLANNING
  -> IMPLEMENTING
  -> VERIFYING
  -> COMPLETED

Any state
  -> BLOCKED_DECISION
  -> BLOCKED_EVIDENCE
  -> PAUSED
```

The plan lives at:

```text
docs/exec-plans/active/<work-id>.md
```

and moves to:

```text
docs/exec-plans/completed/<work-id>.md
```

only after final CI evidence is recorded.

## Plan-before-code protocol

Before editing code, the agent records:

1. **Objective** — what user/business outcome changes.
2. **Non-goals** — what will not change.
3. **Current facts** — files, current behavior, current CI state.
4. **Constraints** — baseline, ADRs, safety boundary.
5. **Acceptance criteria** — observable pass/fail conditions.
6. **Implementation slices** — ordered, independently verifiable steps.
7. **Verification matrix** — targeted tests and full CI gates.
8. **Decision gates** — only questions requiring human choice.
9. **Evidence plan** — what artifacts prove the result.

Do not write implementation code before this minimum plan exists.

## Checkpoint-safe implementation

Prefer slices such as:

```text
domain model
  -> domain test
  -> application use case
  -> application test
  -> adapter
  -> adapter contract test
  -> API/CLI boundary
  -> API test
  -> E2E scenario
  -> docs
```

After each meaningful slice:

- run the smallest relevant test;
- update the plan step status;
- record unexpected findings;
- record the exact next action.

A new agent should be able to continue from the plan without reconstructing the
reasoning from Git history or chat.

## Decision gates

Stop and ask for a decision only when two or more materially different choices
change one of these:

- product/user semantics;
- domain model;
- architecture boundary;
- safety/risk posture;
- capital allocation/liquidity policy;
- externally visible API compatibility;
- irreversible data migration;
- live-trading capability;
- new strategic dependency with lasting maintenance cost.

Do not stop for naming, local refactoring, routine library usage, or test
implementation when the accepted architecture already determines the answer.

When blocked, record:

```text
Decision:
Options:
Evidence:
Recommendation:
Consequence of each option:
Resume after decision:
```

## Evidence-first debugging

When a test/CI failure occurs:

1. capture the failing command/run;
2. identify the first causal error, not downstream noise;
3. record the finding in the plan;
4. fix the implementation or the governing expectation;
5. rerun the narrow test;
6. rerun the affected CI gate;
7. do not call the task complete until the final commit is green.

Never edit tests only to hide a real behavior regression.

## External API work

For Binance/OKX behavior:

- prefer official documentation;
- normalize venue-specific concepts inside adapters;
- write parser/contract tests for response shapes;
- never leak venue response models into the domain;
- CI-gating tests must not depend on live exchange availability.

If an external fact cannot be verified, mark it unassessed and stop short of a
claim that depends on it.

## Finishing a task

Before moving the plan to `completed/`:

- final diff matches scope;
- targeted tests passed;
- CI gates passed on final commit;
- E2E target evidence exists where strategy behavior changed;
- README/status/ADR updated when behavior changed;
- plan contains CI run URL/ID and evidence artifact names;
- no unresolved decision/evidence block remains.

The completion note should state facts only: what changed, what proved it, and
what remains intentionally unassessed.
