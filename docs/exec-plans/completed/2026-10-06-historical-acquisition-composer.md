# 2026-10-06-historical-acquisition-composer: Compose validated acquisition manifests from reviewed inputs

Status: COMPLETED
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Remove manual JSON copying between the read-only Cash case planner and
`Acquire Historical Campaign`, without weakening the rule that acquisition
dispatch remains explicit.

Target flow:

```text
optional explicit Funding date range
+ exact Cash case-plan artifact
+ acquisition_id
+ planner_campaign_prefix
  -> verify exact successful case-plan run/artifact
  -> validate case-plan report schema/evidence type
  -> compose versioned acquisition JSON
  -> re-run acquisition manifest validation
  -> upload acquisition-ready artifact
  -> operator reviews and explicitly dispatches Acquire Historical Campaign
```

No preparation, acquisition dispatch, planner trigger, promotion, corpus write,
branch, PR, or merge.

## Governing contracts

- AGENTS.md and repository testing/workflow contracts.
- ADR-0006 historical provenance.
- ADR-0007 Stage-1/Stage-2 policy.
- Historical acquisition manifest contract.
- Read-only Cash acquisition case planner contract.

## Non-goals

- No automatic acquisition dispatch.
- No automatic Cash holding-period choice.
- No automatic promotion or merge.
- No Stage-2 activation.
- No raw archive handling.

## Design decisions

- Funding range is optional but must provide both start and end when used.
- Cash case-plan input is optional but, when used, is selected by exact
  successful Actions run ID + exact artifact name.
- At least one Funding day or one selected Cash case is required.
- Composer validates the case-plan report body, not only artifact filename.
- `entry_market_date` is reporting metadata and is stripped when converting
  case-plan rows into acquisition `cash_cases`.
- Final output is passed back through the existing acquisition parser; the
  31-item cap and all UTC/future/expiry checks are therefore reused.
- Composer permissions stay actions:read + contents:read.

## Acceptance criteria

- [x] Pure composer validates Cash case-plan report schema/evidence type.
- [x] Composer accepts Funding-only, Cash-only, or mixed inputs.
- [x] Funding start/end must be supplied together.
- [x] Empty effective acquisition fails closed.
- [x] Final composed JSON round-trips through acquisition parser.
- [x] CLI emits normalized acquisition-ready JSON.
- [x] Tests cover Funding-only, Cash-only, mixed, malformed report and overflow.
- [x] Read-only workflow verifies exact successful Cash case-plan run/artifact.
- [x] Workflow independently verifies Actions artifact digest/expiry.
- [x] Workflow uploads acquisition-ready manifest + source evidence only.
- [x] Workflow permissions remain actions:read + contents:read.
- [x] Workflow self-test uses case-plan run 37477835622 plus explicit Funding day.
- [x] README/testing docs explain compose -> explicit acquisition dispatch boundary.
- [x] Final CI + workflow self-test green.
- [x] Archive after verification.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | passed run 37481309689 |
| Code | composer/CLI/workflow-contract tests | passed run 37481309689 |
| API | no regression | passed run 37481309689 |
| Reference E2E | unchanged | passed run 37481309689 |
| Workflow | exact case-plan artifact -> acquisition JSON | passed run 37479406303, artifact 11420626824 |
| Write boundary | no acquisition/prep/corpus/branch/PR mutation | verified by workflow contract + read-only permissions |

## Decision gates

None. Acquisition execution remains an explicit later action.

## Resume from here

Completed. The composer remains read-only and acquisition execution remains a
separate explicit operator action through Acquire Historical Campaign.

## Completion

Final implementation/docs commit: 6460c736b5c85238696ae7393275ec332be45d30
CI run: 37481309689 passed all required gates
Workflow evidence: run 37479406303; artifact 11420626824; Funding 2026-09-04 + Cash 2026-06-03/BTC-USDT-260626
Remaining unassessed items: none within composer scope; acquisition dispatch remains intentionally explicit

## Evidence log

- 2026-10-06: composer implementation validates case-plan schema/evidence,
  supports Funding-only/Cash-only/mixed inputs, strips reporting-only fields,
  and delegates final semantics to the versioned acquisition parser.
- 2026-10-06: workflow self-test run 37479406303 completed successfully. It
  independently verified planner run 37477835622/artifact
  cash-acquisition-case-plan-37477835622, composed Funding 2026-09-04 plus the
  explicit Cash 2026-06-03 BTC-USDT-260626 case, and uploaded artifact
  11420626824 with SHA-256
  063dafb7f482dfb2a7f181fbea2a43c8a2c9a00e577966c921566fe67cfac259.
- 2026-10-06: final CI run 37481309689 passed Static, Code-level, API contract,
  and E2E strategy acceptance gates. Workflow-contract tests lock the
  actions:read + contents:read boundary and forbid acquisition dispatch, corpus
  mutation, branch push, or PR creation.
