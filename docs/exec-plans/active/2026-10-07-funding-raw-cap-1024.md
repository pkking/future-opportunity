# 2026-10-07-funding-raw-cap-1024: Raise Funding raw-archive safety cap

Issue: #20
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Update the Funding historical preparation hard limit from 600 MiB to 1024 MiB based on measured official OKX Wave 002 archive sizes, while preserving a finite streaming safety cap and leaving Cash limits unchanged.

## Non-goals

- No sample/research parameter changes.
- No change to Cash acquisition limits.
- No removal of raw-size protection.
- No corpus promotion or Stage-2 policy change.

## Current facts

- Wave 002 source run 37591051064 is using the approved deterministic sample.
- Funding 2026-02-07 and 2026-02-23 failed with `raw archive exceeded 600 MiB limit`.
- Read-only diagnostic run 37591909278 measured Wave 002 max SPOT=368.8 MB and max SWAP=800.48 MB.
- Existing Funding script default, single-day workflow, and corpus workflow all use 600 MiB.
- 1024 MiB covers the measured maximum with bounded headroom.

## Acceptance criteria

- [ ] Funding script default becomes 1024 MiB.
- [ ] Single-day Funding workflow sets 1024 MiB.
- [ ] Funding corpus workflow sets 1024 MiB.
- [ ] Streaming hard-limit behavior remains present.
- [ ] Cash preparation remains at 600 MiB.
- [ ] Contract test locks the Funding 1024 value and no-write boundary.
- [ ] Full required CI gates pass.
- [ ] Merge before Wave 002 retry; retry retains exact original sample.

## Implementation slices

- [x] 1. Capture Wave 002 failures and official catalog sizes.
- [ ] 2. Update Funding script/workflow values.
- [ ] 3. Add contract regression coverage.
- [ ] 4. Verify PR CI and merge.
- [ ] 5. Return to Wave 002 and retry exact pre-registered dates.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Measured capacity | diagnostic 37591909278 | passed |
| Focused contract | pytest | pending |
| Static | CI | pending |
| Code | CI | pending |
| API | CI | pending |
| E2E | CI | pending |

## Decision gates

None. This is an infrastructure capacity correction grounded in measured source sizes.

## Evidence log

- 2026-10-07: Wave 002 Funding 2026-02-07 failed at 600 MiB.
- 2026-10-07: Wave 002 Funding 2026-02-23 failed at 600 MiB.
- 2026-10-07: diagnostic 37591909278 measured max SWAP 800.48 MB and max SPOT 368.8 MB across all 12 approved Funding dates.

## Deviations and discoveries

None yet.

## Resume from here

Change only Funding raw archive limits from 600 to 1024 in the script default and Funding workflows, add contract assertions, then open the required PR.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: Wave 002 retry after merge
