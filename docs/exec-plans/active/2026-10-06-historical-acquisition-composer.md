# 2026-10-06-historical-acquisition-composer: Compose validated acquisition manifests from reviewed inputs

Status: PLANNING
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

- [ ] Pure composer validates Cash case-plan report schema/evidence type.
- [ ] Composer accepts Funding-only, Cash-only, or mixed inputs.
- [ ] Funding start/end must be supplied together.
- [ ] Empty effective acquisition fails closed.
- [ ] Final composed JSON round-trips through acquisition parser.
- [ ] CLI emits normalized acquisition-ready JSON.
- [ ] Tests cover Funding-only, Cash-only, mixed, malformed report and overflow.
- [ ] Read-only workflow verifies exact successful Cash case-plan run/artifact.
- [ ] Workflow independently verifies Actions artifact digest/expiry.
- [ ] Workflow uploads acquisition-ready manifest + source evidence only.
- [ ] Workflow permissions remain actions:read + contents:read.
- [ ] Workflow self-test uses case-plan run 37477835622 plus explicit Funding day.
- [ ] README/testing docs explain compose -> explicit acquisition dispatch boundary.
- [ ] Final CI + workflow self-test green.
- [ ] Archive after verification.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | pending |
| Code | composer/CLI tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged | pending |
| Workflow | exact case-plan artifact -> acquisition JSON | pending |
| Write boundary | no acquisition/prep/corpus/branch/PR mutation | pending |

## Decision gates

None. Acquisition execution remains an explicit later action.

## Resume from here

Implement pure composition code that validates a Cash case-plan report and
combines it with an optional Funding range, then delegates final semantics to
the existing acquisition parser.

## Completion

Final implementation commit:
CI run:
Workflow evidence:
Remaining unassessed items:
