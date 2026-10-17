# Cash 2025 Q3/Q4 planner verification

Issue: #69
Status: BLOCKED_DECISION
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
- [ ] Obtain explicit operator authorization to stage the separate corpus promotion proposal.
- [ ] Validate the staged proposal's own CI and historical smoke before human merge.

## Implementation slices

- [x] 1. Inspect actual completed planner Run 39020272173 and downloaded artifact.
- [x] 2. Independently audit inventory and complete 24-item wave.
- [x] 3. Record evidence and exact recovery/decision gate in repository.
- [ ] 4. Separately stage reviewed corpus proposal after operator authorization.

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
Only with explicit operator authorization, dispatch the separate write-capable PR staging workflow:

```bash
gh workflow run promote-planned-historical-wave.yml -R pkking/future-opportunity --ref main \
  -f planner_run_id=39020272173 \
  -f planner_artifact_name=historical-campaign-planner-39020272173 \
  -f wave_file=waves/cash-2025-q3-q4-review-001-wave-001.json
```

This action proposes corpus changes in a review PR, not an approved main merge. Require promotion.json, exact 24-source inventory, branch/PR or pr-handoff, normal PR CI, historical smoke, human review and merge, then main verification. Do not dispatch automatically, change source dates, enable live trading, or turn on economic thresholds. Issue #69 remains open.

## Completion

Evidence checkpoint is complete once PR #81 final-head CI passes, it is merged, and main CI is verified. Corpus promotion and the separate human review remain pending. No economic gate or live trading permission is granted.
