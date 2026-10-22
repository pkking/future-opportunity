# Immutable Funding diagnostic Release — independent GitHub runner replay

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-22

## Objective

Use the **already published** diagnostic Immutable Release
`diagnostic-funding-vps-2026-10-21` to verify the original captured bytes
on a *separate GitHub-hosted runner* without another OKX GET, manual
collection, GitHub Release, tag creation, backfill or change to the
existing production `release.published` workflow.

## Existing evidence and constraints

- Original 2026-10-21 VPS ZIP SHA256:
  `6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a`.
- Original manifest SHA256:
  `96e16bde5e29e4c53360988c0f2a29ce1c0ce3727e2401fa779f16c1228d8fdb`.
- GitHub immutable diagnostic Release published
  **2026-10-22T15:29:02Z**, **later** than the source's
  2026-10-21T00:15:00Z entry boundary.
- Operator successfully ran GitHub `gh release verify`,
  `gh release verify-asset`, SHA256 verification and strict original
  three-file `audit_vps_funding_capture.py` replay on the *original VPS*.
  That did not independently exercise a second host.
- Previously merged PR #133 excludes tag pushes from 31 unrelated
  historical research workflows. Do not publish any new tag.
- GitHub-only/public-free features, no OBS/S3/TSA/other storage.
- `point_in_time_publication_verified=false`,
  `acquisition_approved=false`, `promotion_approved=false` always.
  The accepted 32 Funding/66 Cash research sample totals are unchanged.

## Acceptance criteria

- [x] Add a distinct GitHub Actions workflow which only uses
      `workflow_dispatch` and a **one-time initial main workflow-file
      push path** trigger, explicit `contents: read`; no Release
      publication, tag push, market capture or new credentials.
      Future `workflow_dispatch` is *read-only*.
- [x] Workflow pins exact diagnostic tag, GitHub server immutable metadata,
      prerelease and late publication time, exact two original asset
      hashes, server asset times, and expected release target.
- [x] A GitHub-hosted runner downloads both original assets from the
      old Release. SHA256 verify, `gh release verify`, and
      `gh release verify-asset` for both originals must pass.
- [x] Run *unchanged* strict original `audit_vps_funding_capture.py`
      on downloaded original ZIP+manifest, write an explicit
      `diagnostic_only_github_hosted_offline_replay_verified` receipt, never promote.
- [x] Failure is `UNASSESSED`; derived report alone is a 90-day
      Actions Artifact. Source ZIP persists in existing Release.
- [x] Deterministic CI regression tests ensure workflow is read-only,
      scoped to the frozen old diagnostic and never changes
      source/publishing production gates.
- [x] Final PR-head CI 5/5 + Historical Smoke green; squash merge
      and verify postmerge main CI **and** independent diagnostic
      runner result. Record in #85. Do not report external replay
      successful until it actually succeeds on GitHub-hosted runner.

## Change scope

- `.github/workflows/review-funding-diagnostic-release.yml` (new)
- `tests/test_funding_diagnostic_release_workflow.py` (new)
- This active plan.

## Decision gates

None: existing raw source, signing, GitHub releases and risk policy
already approved. No extra user action needed to test on normal
main branch push; external provider/credentials, new market observations
or promotion would require separate authorization.

## Implementation slices

- [x] Confirm frozen existing diagnostic SHA-256 and GitHub server
      publication strictly later than the 2026-10-21 entry boundary.
- [x] Add read-only `workflow_dispatch` and scoped main-push
      independent GitHub-hosted source/Release attestation checker.
- [x] Reuse unmodified existing original-ZIP offline anti-lookahead
      replay, with separate non-promotable diagnostic-only receipt.
- [x] Add policy regression tests rejecting new market capture,
      tags/releases changes, expanded CI privileges and false promotion.
- [x] Run final-head full CI and Historical Smoke, fix failures.
- [x] Squash merge, verify postmerge main CI and independently executed
      read-only GitHub hosted diagnostic Release replay.

## Verification matrix

| Gate | Independent evidence | Result |
| --- | --- | --- |
| Source ZIP SHA256 | GitHub-hosted runner downloaded original ZIP, checked original SHA256 | SUCCESS |
| Manifest SHA256 | GitHub-hosted runner downloaded original manifest and checked expected SHA256 | SUCCESS |
| Immutable Release | Github server immutable+late timing, `gh release verify`, `verify-asset` for BOTH files | SUCCESS |
| Offline replay | Unmodified `audit_vps_funding_capture.py` on downloaded original bytes | SUCCESS |
| Non-promotion | `github_hosted_preentry_source_verified=false`, `point_in_time_publication_verified=false`, both approvals false | SUCCESS |
| PR gates | [CI #39811638024](https://github.com/pkking/future-opportunity/actions/runs/39811638024) 5/5 and [Historical Smoke #39811638032](https://github.com/pkking/future-opportunity/actions/runs/39811638032) | SUCCESS |
| Post-merge main | [CI #39811808392](https://github.com/pkking/future-opportunity/actions/runs/39811808392) and [independent GitHub diagnostic replay #39811808493](https://github.com/pkking/future-opportunity/actions/runs/39811808493) | SUCCESS |

## Completion

Final commit: `bd2d8ba0276f0aaa31e27b680be3524b23f6ad6a` (squash merge of PR #134).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39811638024 (5/5 PASS); https://github.com/pkking/future-opportunity/actions/runs/39811638032 (Historical Smoke PASS); https://github.com/pkking/future-opportunity/actions/runs/39811808392 (postmerge main PASS).
Independent real-GitHub replay: https://github.com/pkking/future-opportunity/actions/runs/39811808493 (PASS).
Derived review artifact: `funding-vps-existing-diagnostic-replay`, ID `12440307395`, SHA256 `8b3a3f820ad490428c0bc04ac55921b8062c0d9539d8845eb2912dc1e0332a9e`, 90-day retention; original source remains in previously published immutable GitHub Release.
Issue evidence checkpoint: https://github.com/pkking/future-opportunity/issues/85#issuecomment-6345510967.
Remaining unassessed items: The original 2026-10-21 data was published to GitHub only on 2026-10-22T15:29:02Z (late); this proves neither GitHub-hosted pre-entry existence on Oct 21, independent OKX publication time, the production timed OnSuccess release path, nor adequate negative-low Funding regime historical coverage. Funding 32/Cash 66 unchanged; no acquisition/promotion/trading approval. Issue #85 stays OPEN/BLOCKED_EVIDENCE.

## Resume from here

Diagnostic-only independent GitHub-runner replay slice is **complete**. Continue Issue #85 with true future-day timed `funding-vps-YYYY-MM-DD` release/published-event workflow review and missing regime evidence; do not reclassify the late diagnostic as a valid prospective sample.
