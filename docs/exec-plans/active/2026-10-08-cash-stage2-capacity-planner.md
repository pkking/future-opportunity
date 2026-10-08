# 2026-10-08-cash-stage2-capacity-planner

Issue: #45
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Determine whether already-published OKX module-4 FUTURES L2 history can supply the 25 additional Cash-and-Carry pinned days needed to move the strategy from 5 to 30 days, and produce a deterministic pre-registration candidate set without acquiring or promoting data.

## Current facts

- Cash main corpus contains 5 distinct pinned days.
- ADR-0007 requires 30 distinct pinned days for Stage-2 proposal eligibility.
- The fixed Cash readiness monitor watches 28 July-September dates and is currently blocked by the source publication frontier.
- Modules 1/2/4/5/6 agree on a clean frontier ending 2026-06-26 in the previously scanned June-October interval.
- Module 4 is the canonical L2 source for Cash readiness.

## Constraints and invariants

- Read-only source discovery only.
- No automatic acquisition, promotion, or corpus mutation.
- Keep module-4 / FUTURES / BTC-USDT-family evidence semantics.
- Exclude dates already pinned as Cash.
- Select candidate dates using availability only; never inspect returns before selection.
- Candidate selection must be deterministic and reproducible.
- Existing fixed 28-date readiness monitor remains unchanged.

## Acceptance criteria

- [ ] Planner computes remaining days to the 30-day target from corpus state.
- [ ] Planner distinguishes unique-ready, missing, ambiguous, and query-error dates.
- [ ] Planner scans a backward historical window ending at the known publication frontier.
- [ ] Already-pinned Cash dates are excluded.
- [ ] If capacity is sufficient, planner emits exactly the required number of deterministic pre-registration candidates.
- [ ] Selection is spread across the usable interval rather than cherry-picked by economics.
- [ ] Report records exact source query semantics and pinned-corpus SHA/context.
- [ ] Workflow uploads a read-only capacity-plan artifact and summary.
- [ ] Unit tests cover capacity, insufficiency, duplicate/ambiguous dates, and deterministic selection.
- [ ] Full repository CI and Historical Smoke pass.

## Implementation slices

- [x] 1. Create Issue/branch/plan and inspect existing readiness/frontier code.
- [ ] 2. Implement pure capacity planning and deterministic date selection.
- [ ] 3. Implement live read-only OKX catalog probe script.
- [ ] 4. Add workflow and tests.
- [ ] 5. Use workflow evidence to decide whether Cash can reach 30 from already-published history.
- [ ] 6. Archive/merge; if capacity is sufficient, create a separate explicit acquisition-wave task.

## Verification matrix

| Gate | Expected |
|---|---|
| Current Cash pinned count | 5 |
| Target | 30 |
| Needed | 25 |
| Canonical source | module 4 / FUTURES / BTC-USDT / daily |
| Selection input | source availability + pinned dates only |
| Acquisition side effects | none |
| CI / Smoke | all green |

## Resume from here

Implement the read-only planner. The first live artifact must answer whether at least 25 unique unpinned module-4 archive days exist in the backward scan window. If yes, freeze those exact dates as a later acquisition handoff; if no, report the shortfall and extend source investigation rather than silently lowering evidence requirements.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: backward source capacity and exact candidate dates