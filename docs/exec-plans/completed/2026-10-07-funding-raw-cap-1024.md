# 2026-10-07-funding-raw-cap-1024: Raise Funding raw-archive safety cap

Issue: #20
Status: COMPLETED
Owner: agent
Started: 2026-10-07
Last checkpoint: 2026-10-07

## Objective

Raise the Funding historical raw-archive hard limit from 600 MiB to 1024 MiB using measured OKX Wave 002 archive sizes while preserving a finite streaming safety boundary.

## Non-goals

- No research sample changes.
- No Cash raw-size change.
- No removal of archive-size protection.
- No corpus or Stage-2 policy change.

## Current facts

- Wave 002 diagnostic 37591909278 measured max SPOT=368.8 MB and max SWAP=800.48 MB.
- The old 600 MiB limit caused deterministic failures for approved Funding dates with >600 MB SWAP archives.
- PR #21 merged as d47c83abf48919a95859ae571a05398eee2303ff.
- Main CI and both Funding push self-tests passed after merge.

## Acceptance criteria

- [x] Funding script default is 1024 MiB.
- [x] Single-day Funding workflow uses 1024 MiB.
- [x] Funding corpus workflow uses 1024 MiB.
- [x] Streaming hard-limit behavior remains present.
- [x] Cash preparation remains at 600 MiB.
- [x] Contract test locks Funding and Cash boundaries.
- [x] Full required CI gates pass.
- [x] Same pre-registered Wave 002 dates remain eligible for retry without reselection.

## Implementation slices

- [x] 1. Capture Wave 002 failure and measured archive sizes.
- [x] 2. Update Funding script/workflow values.
- [x] 3. Add contract regression coverage.
- [x] 4. Verify PR CI and merge.
- [x] 5. Verify main CI and Funding push self-tests.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Measured capacity | diagnostic 37591909278 | passed |
| Plan integrity | PR #21 CI 37592417046 | passed |
| Static | 37592417046 | passed |
| Code | 37592417046 | passed |
| API | 37592417046 | passed |
| E2E | 37592417046 | passed |
| Historical smoke | 37592416980 | passed |
| Main CI | 37592620292 | passed |
| Single-day Funding self-test | 37592620256 | passed |
| Funding corpus self-test | 37592620235 | passed |

## Decision gates

None. This is an evidence-backed infrastructure capacity correction.

## Evidence log

- Wave 002 source run 37591051064 failed 2026-02-07, 02-23, 03-05 and 03-10 under the old 600 MiB cap.
- Diagnostic 37591909278 measured those Wave 002 source archives and established an 800.48 MB maximum SWAP archive.
- PR #21 required checks all passed.
- Main post-merge CI and both Funding preparation self-tests passed.

## Deviations and discoveries

No research parameters changed. Cash stays independently capped at 600 MiB because no Cash raw-size defect was observed.

## Resume from here

Completed. Return to Issue #19 and rerun the exact approved Wave 002 sample with the 1024 MiB Funding cap; do not resample any dates.

## Completion

Final commit: d47c83abf48919a95859ae571a05398eee2303ff
CI run: https://github.com/pkking/future-opportunity/actions/runs/37592620292
E2E artifact: Funding self-tests 37592620256 and 37592620235
Remaining unassessed items: Wave 002 retry under Issue #19
