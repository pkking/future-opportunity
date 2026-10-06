# 2026-10-06-cash-acquisition-case-planner: Expand verified Cash discovery into explicit acquisition cases

Status: PLANNING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Remove repetitive manual construction of 20-30 Cash acquisition cases while
preserving the rule that holding-period choices are explicit operator inputs.

Target flow:

```text
successful Cash discovery run
  + explicit future_id
  + explicit expiry_at
  + explicit exit_at
  + explicit UTC entry time
  -> validate every discovery report
  -> select only matching verified future evidence
  -> generate deterministic explicit cash_cases[]
  -> upload read-only planning report
  -> operator copies/reviews cases in acquisition manifest
```

No preparation, promotion, corpus write, branch, PR, or merge.

## Governing contracts

- AGENTS.md and repository workflow/testing contracts.
- ADR-0006 historical provenance.
- ADR-0007 Stage-1/Stage-2 policy.
- Existing Cash discovery and acquisition campaign contracts.
- Cash cases in acquisition remain explicit business facts.

## Non-goals

- No automatic exit-date selection.
- No automatic expiry/future selection.
- No automatic promotion or acquisition dispatch.
- No market-return optimization.
- No raw archive commit.

## Design decisions

- Inputs explicitly include:
  - `future_id`
  - `expiry_at`
  - `exit_at`
  - `entry_time_utc`
- Discovery reports provide only evidence that a market date has the expected
  historical future identity.
- A report with no unique future archive or mismatched future ID is reported as
  excluded, never silently converted to a case.
- Duplicate discovery market dates or schema drift fail closed.
- Generated cases are sorted by entry market date and capped at 31.
- Future ID suffix must agree with explicit expiry date; expiry remains 08:00 UTC.
- Generated `cash_cases` are suitable as acquisition-manifest input but remain
  review-only output.

## Acceptance criteria

- [ ] Pure planner model validates explicit Cash template semantics.
- [ ] Planner parses discovery reports without trusting filenames alone.
- [ ] Matching verified dates generate deterministic explicit cases.
- [ ] Mismatched/no-history dates are reported with exclusion reason.
- [ ] Duplicate market dates and malformed reports fail closed.
- [ ] Entry time, exit, expiry and future suffix are validated.
- [ ] Output capped at 31 selected cases.
- [ ] CLI consumes a directory/list of discovery report files and emits
      machine-readable report + acquisition-ready `cash_cases`.
- [ ] Tests cover selected, excluded, duplicate, malformed and time-bound cases.
- [ ] Read-only workflow consumes exact successful discovery run ID.
- [ ] Workflow independently verifies/downloads exact discovery artifacts.
- [ ] Workflow permissions remain actions:read + contents:read.
- [ ] Workflow uploads planning evidence only.
- [ ] README/testing docs explain discovery -> case plan -> acquisition boundary.
- [ ] Final CI + workflow self-test green.
- [ ] Archive after verification.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | pending |
| Code | planner/CLI tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged | pending |
| Workflow | exact discovery run -> read-only case plan | pending |
| Write boundary | no preparation/corpus/branch/PR mutation | pending |

## Decision gates

None. All strategy holding-period inputs remain explicit.

## Resume from here

Implement pure package code that accepts parsed discovery reports plus an
explicit Cash template and returns selected explicit acquisition cases with
excluded-date diagnostics. Then add CLI and workflow.

## Completion

Final implementation commit:
CI run:
Workflow evidence:
Remaining unassessed items:
