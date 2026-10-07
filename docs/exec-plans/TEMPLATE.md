# <work-id>: <title>

Issue: #N
Status: PLANNING
Owner: agent
Started: YYYY-MM-DD
Last checkpoint: YYYY-MM-DD

## Objective

What user/business outcome will change?

## Non-goals

What is explicitly out of scope?

## Must-read context

- `AGENTS.md`
- `docs/design-baseline-v0.1.md`
- relevant ADRs
- relevant source/tests

## Current facts

- Current behavior:
- Current CI state:
- Existing implementation:
- Known limitations:

## Constraints and invariants

List applicable product, safety, architecture, persistence, return, and risk
constraints.

## Acceptance criteria

- [ ] Observable criterion 1
- [ ] Observable criterion 2
- [ ] Required code-level test
- [ ] Required API test
- [ ] Required E2E target/evidence
- [ ] Final CI green

## Implementation slices

- [ ] 1. ...
- [ ] 2. ...
- [ ] 3. ...

For each completed slice, add the commit SHA and targeted verification result.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Static | `uv run ruff check .` | zero violations | pending |
| Code | repository code-level test command | pytest result | pending |
| API | API contract command | pytest result | pending |
| E2E | E2E command | JSON + JUnit artifacts | pending |

## Decision gates

None, or:

### Decision: <name>

Options:
Evidence:
Recommendation:
Consequence:
Status: BLOCKED_DECISION

## Evidence log

Record concrete evidence chronologically.

- YYYY-MM-DD: command/run/artifact -> result.

## Deviations and discoveries

Record facts discovered during implementation that changed the plan.

## Resume from here

Exactly one concrete next action that another agent can execute immediately.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending or not applicable
Remaining unassessed items: pending


When finalizing a plan, set `Status: COMPLETED`, check every acceptance criterion and implementation slice, replace pending completion fields with concrete evidence, move the file to `completed/` in a completion PR, and close the GitHub Issue only after that PR merges.
