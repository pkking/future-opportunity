# Restore chosen Funding source evidence direction — Option A

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-25
Last checkpoint: 2026-10-25

## Objective

Apply the user's explicit 2026-10-25 correction **"说错了 仍然用 方案 A"**: Option A (existing VPS prospectively observed OKX public responses → immutable GitHub Release → independently checked release.published audit and read-only GitHub custody/continuity diagnostics) remains the selected implementation path. Supersede the earlier mistaken interpretation "反感A" / "B preferred" as a recorded but withdrawn direction, so future agents do not deploy or prioritize the independent-observer B design.

## Facts and scope

- main at start: `483614f4f4d3aae66fde7e476b38d64a9b5c634c`; no open PRs; prior postmerge CI #40192214568 SUCCESS.
- Parent open Issue #85 tracks provenance and four-regime Funding source coverage. Three actual immutable source days exist as last verified 2026-10-25, which remain **GitHub-custody** evidence, not independently signed OKX publication time.
- PRs #154/#155 introduced an **offline-only** B draft validator and documentation. The user now explicitly chooses A. Keep historical PRs and passing tests intact for reproducibility, mark B clearly as unselected/inactive/no production deployment. Do not silently delete evidence or pretend it was never designed.
- No new source or exchange GET, collector, storage, third-party signer, witness deployment, historical pinned fixtures, source acceptance criteria, numerical economic gate or trading.
- Frozen V0 paper-only policy, ADR-0008, and all `exchange_signed` / `point_in_time_publication_verified` / `acquisition_approved` / `promotion_approved` false postures stay unchanged.

## Acceptance criteria

- [x] Research note visibly records the *later correction* restoring Option A, explicitly superseding previous B-first statements without erasing historical decision trace.
- [x] B-only design doc visibly marked **NOT SELECTED / INACTIVE**, offline prototype retained as research artifact; no implicit approval to deploy B.
- [x] Parent active Issue #85 plan's **latest** `Resume from here` directs future agents to A GitHub immutable original custody, valid independent release audits, growing genuine dates and evidence gaps — not a B provider/trust-key decision.
- [x] Issue #85 updated with explicit user correction and full tested merge evidence; issue remains open BLOCKED_EVIDENCE.
- [x] No production code, scheduled collector workflow, source evidence, historical samples, economics or trading changed.
- [x] PR final-head all five CI checks + Historical Backtest Smoke SUCCESS, merge and postmerge main CI SUCCESS, separately archive this plan with proof.

## Implementation slices

- [x] 1. Correct research priority, B design status and parent active recovery checkpoint.
- [x] 2. Verify exact PR-head five CI checks and Historical Backtest Smoke; merge only after success.
- [x] 3. Verify postmerge main CI, archive this completed plan in a separate checked PR, and record issue comment.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Correct latest directive | Research note, B draft and parent active plan updated on branch; implementation unchanged | PASS (reviewed) |
| CI five jobs | PR #156 final head `c0f6de4d` #40196606837 all five SUCCESS; postmerge main #40196675063 SUCCESS | PASS |
| Historical | PR #156 final head #40196606807 SUCCESS | PASS |
| Main | #40196675063 SUCCESS on `c9736807981e6a4c162ef7b29bccae113393960a` | PASS |

## Decision gates

This is already resolved by the user's newer explicit correction: **Option A selected**. There is no new human decision needed. Do not solicit or infer further approval for B or change source admission criteria. The limits of R1 versus true upstream publication authentication remain material evidence gaps.

## Evidence log

- 2026-10-25: [PR #156](https://github.com/pkking/future-opportunity/pull/156) final tested head `c0f6de4d519a600aa14d197a545b42d78814dbad` passed [CI #40196606837](https://github.com/pkking/future-opportunity/actions/runs/40196606837) 5/5 SUCCESS and [Historical Smoke #40196606807](https://github.com/pkking/future-opportunity/actions/runs/40196606807) SUCCESS. Squash merge main commit `c9736807981e6a4c162ef7b29bccae113393960a`; [postmerge main CI #40196675063](https://github.com/pkking/future-opportunity/actions/runs/40196675063) SUCCESS. Final head E2E evidence artifact `12600006899` SHA256 `ea701a121e8de3dff22dfe5d9484387516f25f58609ccba5016771728532daab`; historical artifact `12600586276` SHA256 `6bba55e20406c00f0a9b848d0fdda33892e7af3c1df5b133163c7520142b907c`.
- 2026-10-25: Parent Issue #85 correction comment https://github.com/pkking/future-opportunity/issues/85#issuecomment-6398109215 explicitly records user-selected Option A, B unselected, unchanged trust/strategy boundaries and merge/CI evidence; active parent plan now resumes A only. This completion-only PR archives the corrected implementation plan; do not re-open it as active work.

- 2026-10-25: Corrected the research note with a prominent latest Option A decision and labelled the earlier B-first guidance as withdrawn; marked `docs/design/funding-independent-witness-r2.md` as inactive/unselected; superseded B's parent `Resume from here` with A's existing VPS/immutable Release/independent `release.published` audit and bounded continuity. No runtime change or altered provenance/economic approvals. PR final-head tests and archival still pending.

- 2026-10-25: User superseded prior "反感A" with "说错了 仍然用 方案 A". Current main and no PRs verified. Work is decision-record correction, not technical source promotion.

## Resume from here

Task complete. Follow the parent active `docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md`'s latest `Resume from here`: Option A explicitly selected, B not in active roadmap. Continue genuine VPS immutable Release/audit and continuity research; never imply OKX signature, change historical admission, Stage-2 economics or trading without separate approval.

## Completion

Final commit: `c9736807981e6a4c162ef7b29bccae113393960a` (PR #156 squash; tested head `c0f6de4d519a600aa14d197a545b42d78814dbad`)
CI run: #40196606837 all five SUCCESS, Historical Smoke #40196606807 SUCCESS, main #40196675063 SUCCESS
E2E artifact: `12600006899`, Historical: `12600586276` (SHA256 in Evidence log)
Remaining unassessed items: independently authenticated OKX first-publication time, negative-low regime coverage, Funding 90 preferred pinned days; evidence blockers do not change historical sample policy.
