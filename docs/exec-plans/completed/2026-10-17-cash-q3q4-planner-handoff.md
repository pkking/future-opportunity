# Cash 2025 Q3/Q4 planner verification

Issue: #69
Status: COMPLETED
Date: 2026-10-17
Scope: read-only evidence checkpoint; no corpus mutation.

## Objective

Record read-only planner and independent evidence so a new agent can safely resume from the exact promotion boundary without altering frozen dates or semantics.

## Source evidence
- [Planner run 39020272173](https://github.com/pkking/future-opportunity/actions/runs/39020272173): SUCCESS, main 1be98b636fc079c08a8c2b5b31b40d0c71dbed18.
- Artifact historical-campaign-planner-39020272173, ID 12096521229, SHA-256 2010f291a71ab32cb10317709c98ff1f006406ebbf5428b6dd91b043970028c9.
- Exact input runs: Q3 39016938121, Q4 39018358844. Each contributes 12 fixed registered dates; 24 distinct.
- Report: status=planned, does_not_promote=true, selected_count=24, excluded_pinned_count=0, wave_count=1.
- Exact wave: waves/cash-2025-q3-q4-review-001-wave-001.json; 24 artifact pairs, below limit 31.
- Independent artifact verification: 24 bundled compact manifests and 96 normalized book SHA-256 values matched, max book age 578 ms (limit 5000 ms); source parent and frozen selection provenance match; no discrepancies.
- Frozen selection SHA-256 values: Q3 015c5b251bade53f10d6cb3f7e361e1dc97483b9116c3e8bde933718b896c32e; Q4 153c2bd18a61e36f87dc80ab4e22fc369a80ca7eefdde6552a0945794486d3f2.
- Current pinned: Cash 30, Funding 32; forecast after separate approved promotion: Cash 54, Funding 32.
- 30-day minimum already met; 90-day preferred not met even after promotion. Economics gates remain disabled.
- Retain unqualified historical examples for the denominator; commit_ready is not profitability approval.

## Acceptance criteria

- [x] Confirm exact successful read-only planner run, source runs and planner artifact digest.
- [x] Validate 24 distinct source-backed candidates, one 24-item wave, no existing pinned collisions.
- [x] Independently validate parent links, two frozen provenance groups, all 96 canonical hashes and 5000ms freshness.
- [x] Preserve 8 properly unqualified samples in the historical qualification denominator.
- [x] Operator dispatched staging run 39021366976.
- [x] PR #82 reviewed and passed final-head CI 39022126155 and Historical Smoke 39022126244; human-approved merge completed.

## Implementation slices

- [x] 1. Inspect actual completed planner Run 39020272173 and downloaded artifact.
- [x] 2. Independently audit inventory and complete 24-item wave.
- [x] 3. Record evidence and exact recovery/decision gate in repository.
- [x] 4. Staged review PR #82 via run 39021366976, verified, human-approved and merged.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Source planner | 39020272173 | SUCCESS |
| Archive digest | GitHub artifact 12096521229 | VERIFIED |
| Canonical checksums | 96 normalized JSONL SHA-256 | VERIFIED |
| PR static/code/API/E2E | PR #81 final synchronized CI | Pending final |
| Historical Smoke | PR #81 final synchronized CI | Pending final |
| Review and promotion | Separate operator action | BLOCKED_DECISION |

## Resume from here

**ARCHIVED / COMPLETED.** Earlier source failures, pending commands and
review-blocked state described above are retained as historical
checkpoints only and are superseded by this closeout. Do not replay
an acquisition, diagnostic, planner or promotion based on a stale
checkpoint in this file.

Issue #69 is closed/completed after the user approved [PR #82](https://github.com/pkking/future-opportunity/pull/82).
The exact frozen Q3 and Q4 12-day preparations were independently
verified (runs [39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
and [39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844));
read-only planner [39020272173](https://github.com/pkking/future-opportunity/actions/runs/39020272173)
and governed staging [39021366976](https://github.com/pkking/future-opportunity/actions/runs/39021366976)
produced the source-bound 24-item review. User-approved PR #82 merged
as `ad4790c0c7ec785eb2de9d53704e154515451001`.
Post-merge main CI and Historical Smoke both succeeded; pinned
corpus is **Cash 54 / Funding 32**, all 24 registered 2025 dates
retained including eight correctly unqualified samples.
For future work start a **new Issue and execution plan**; never
re-use the closed Issue #69. No economics threshold or live trading
was approved.

## Completion

Evidence checkpoint is complete once PR #81 final-head CI passes, it is merged, and main CI is verified. Corpus promotion and the separate human review remain pending. No economic gate or live trading permission is granted.

### Final reconciliation — 2026-10-17

Final commit: `ad4790c0c7ec785eb2de9d53704e154515451001` (PR #82,
human-approved completion of Issue #69, postdating the historical
checkpoints above; this archival move tracked under Issue #83).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39023534155 (main SUCCESS).
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/39023534123 (main SUCCESS).
Source integrity: Q3 39016938121 + Q4 39018358844; planner
39020272173; staged promotion 39021366976; 24/24 unique dates,
Cash 54 / Funding 32, no original fixture replaced.
Remaining unassessed items: The 90-day preferred distinct-day
coverage (Cash needs 36 more, Funding 58 more), more independent
Cash expiry cohorts, stronger Funding pre-entry regime coverage,
account-specific MarginSafety and portfolio-level VenueExposure.
Stage-2 economics and live execution remain DISABLED; these are
new research/ADR scopes, not unfinished tasks under Issue #69.
