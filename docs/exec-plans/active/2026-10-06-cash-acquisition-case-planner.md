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

- [x] Pure planner model validates explicit Cash template semantics.
- [x] Planner parses discovery reports without trusting filenames alone.
- [x] Matching verified dates generate deterministic explicit cases.
- [x] Mismatched/no-history dates are reported with exclusion reason.
- [x] Duplicate market dates and malformed reports fail closed.
- [x] Entry time, exit, expiry and future suffix are validated.
- [x] Output capped at 31 selected cases.
- [x] CLI consumes discovery report files and emits machine-readable report +
      acquisition-ready `cash_cases`.
- [x] Tests cover selected, excluded, duplicate, malformed and time-bound cases.
- [x] Read-only workflow consumes exact successful discovery run ID.
- [x] Workflow independently verifies/downloads exact discovery artifacts.
- [x] Workflow permissions remain actions:read + contents:read.
- [x] Workflow uploads planning evidence only.
- [x] README/testing docs explain discovery -> case plan -> acquisition boundary.
- [ ] Final CI + workflow self-test green.
- [ ] Archive after verification.

## Evidence log

- 2026-10-06: pure planner validates explicit future/expiry/exit/entry-time
  semantics, discovery status, duplicate market dates, future mismatch,
  no-history exclusions and the 31-case cap.
- 2026-10-06: CLI `plan_cash_acquisition_cases.py` emits machine-readable
  evidence and acquisition-ready `cash_cases`; integration CI through
  37477706405 passed.
- 2026-10-06: read-only workflow run 37477835622 consumed exact discovery run
  37434982233, verified the discovery artifact through Actions API, and produced
  one explicit 2026-06-03 BTC-USDT-260626 case with zero exclusions. Evidence
  artifact 11420145596 has digest
  c4f62580775d1ce2d6ec1ebc8d1798ac5387403f3b3b0efbb8711a9ff153afdc.
- 2026-10-06: README/testing contracts document that holding-period inputs stay
  explicit and that the planner has actions/read + contents/read only.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | planner/CLI commits green through 37477706405; final docs/contract pending |
| Code | planner/CLI tests | passed through 37477706405 |
| API | no regression | passed through 37477706405 |
| Reference E2E | unchanged | passed through 37477706405 |
| Workflow | exact discovery run -> read-only case plan | run 37477835622 success |
| Write boundary | no preparation/corpus/branch/PR mutation | workflow permissions + contract test |

## Decision gates

None. All strategy holding-period inputs remain explicit.

## Resume from here

Wait for the latest README/testing/workflow-contract commits to pass all normal
CI gates. If green, record final run IDs, mark COMPLETED, and archive this plan.
The generated cases remain review-only input for a later explicit acquisition.

## Completion

Final implementation commit: pending final documentation CI
CI run: pending final documentation CI
Workflow evidence: run 37477835622 / artifact 11420145596
Remaining unassessed items: none for case planning; acquisition dispatch remains explicit
