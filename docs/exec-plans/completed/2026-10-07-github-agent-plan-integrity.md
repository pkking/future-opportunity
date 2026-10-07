# Phase 1: GitHub-native Agent Plan Integrity

Issue: #6
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Make GitHub Issues the durable task identity, preserve repository-local execution plans as resume checkpoints, and enforce PR-to-Issue-to-Plan traceability through required CI and repository Rulesets.

## Non-goals

- No automatic merge or live trading.
- No claim that traceability alone proves product semantics.
- No weakening of code/API/E2E verification.

## Current facts

- PR #7 is merged on main.
- Ruleset `main` (ID 24626996) is active and has no bypass actor.
- Required checks are Agent plan integrity, Static and architecture safety, Code-level tests, API contract tests and E2E strategy acceptance.
- Main CI after merge passed.

## Acceptance criteria

- [x] Reject missing or mismatched Issue/Plan links.
- [x] Verify referenced Issue is open and is not a PR.
- [x] Keep the legacy #1-#4 exception narrowly limited to historical fixture-only changes.
- [x] Run the integrity gate on pull_request.
- [x] Cover valid, malformed, missing and legacy cases with tests.
- [x] Document canonical Issue/Plan/PR traceability in AGENTS.md.
- [x] Verify active Ruleset enforcement and no bypass actor.
- [x] Preserve existing main CI behavior.

## Implementation slices

- [x] 1. Open tracking Issues #5/#6.
- [x] 2. Create isolated feature branch.
- [x] 3. Add validator, tests and CI gate.
- [x] 4. Update AGENTS.md and task identity.
- [x] 5. Validate PR checks.
- [x] 6. Verify and activate main Ruleset.
- [x] 7. Merge PR #7 and verify main CI.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Plan integrity | PR CI 37568319862 | passed |
| Static | PR CI 37568319862 | passed |
| Code | PR CI 37568319862 | passed |
| API | PR CI 37568319862 | passed |
| E2E | PR CI 37568319862 | passed |
| Ruleset | ID 24626996, active, bypass_actors empty | passed |
| Main integration | CI 37568703347 | passed |

## Decision gates

None. Repository administrator enabled the accepted Ruleset configuration.

## Evidence log

- 2026-10-07: PR #7 final head 72422060e019f48deef444b0d272a65f02d3060a passed CI 37568319862 and Historical Smoke 37568319793.
- 2026-10-07: Ruleset 24626996 verified active on main with required checks and no bypass actors.
- 2026-10-07: PR #7 merged as f917484668ecc869a4d1489850027098502555cb.
- 2026-10-07: main CI 37568703347 passed after merge.

## Deviations and discoveries

The first implementation exposed that completion/archival itself was not yet representable by the validator. Issue #9 addresses that lifecycle gap separately.

## Resume from here

Completed. Use the required Issue/Plan contract for all non-trivial PRs; completion-state handling continues under Issue #9.

## Completion

Final commit: f917484668ecc869a4d1489850027098502555cb
CI run: https://github.com/pkking/future-opportunity/actions/runs/37568703347
Ruleset: 24626996 active on main
Remaining unassessed items: none for Phase 1 traceability and merge gates
