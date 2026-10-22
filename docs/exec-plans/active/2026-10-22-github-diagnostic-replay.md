# Immutable Funding diagnostic Release — independent GitHub runner replay

Issue: #85
Status: VERIFYING
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

- [ ] Add a distinct GitHub Actions workflow which only uses
      `workflow_dispatch` and a **one-time initial main workflow-file
      push path** trigger, explicit `contents: read`; no Release
      publication, tag push, market capture or new credentials.
      Future `workflow_dispatch` is *read-only*.
- [ ] Workflow pins exact diagnostic tag, GitHub server immutable metadata,
      prerelease and late publication time, exact two original asset
      hashes, server asset times, and expected release target.
- [ ] A GitHub-hosted runner downloads both original assets from the
      old Release. SHA256 verify, `gh release verify`, and
      `gh release verify-asset` for both originals must pass.
- [ ] Run *unchanged* strict original `audit_vps_funding_capture.py`
      on downloaded original ZIP+manifest, write an explicit
      `diagnostic_only_not_preentry` report, never promote.
- [ ] Failure is `UNASSESSED`; derived report alone is a 90-day
      Actions Artifact. Source ZIP persists in existing Release.
- [ ] Deterministic CI regression tests ensure workflow is read-only,
      scoped to the frozen old diagnostic and never changes
      source/publishing production gates.
- [ ] Final PR-head CI 5/5 + Historical Smoke green; squash merge
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
- [ ] Run final-head full CI and Historical Smoke, fix failures.
- [ ] Squash merge, verify postmerge main CI and independently executed
      read-only GitHub hosted diagnostic Release replay.

## Verification matrix

| Gate | Expected evidence | Current status |
| --- | --- | --- |
| Source ZIP SHA256 | Exact VPS SHA-256 and GitHub downloaded bytes | Operator verified; independent GitHub runner pending |
| Manifest SHA256 | Exact known original 825-byte manifest digest | Operator verified; independent GitHub runner pending |
| Immutable Release | GitHub metadata, release+both asset signatures | Operator verified ZIP; GH-hosted both pending |
| Offline replay | `offline_vps_replay_only` from authentic original ZIP | VPS verified; GH-hosted pending |
| Non-promotion | `point_in_time_publication_verified=false` and all approvals false | Deterministic tests added, CI pending |
| Repository PR gates | Five CI jobs + Historical Backtest Smoke | CI pending |
| Post-merge main | CI and separate read-only diagnostic job | Pending |

## Completion

Incomplete: GitHub-hosted runner validation and final merge gate
not yet verified. Never mark this diagnostic as pre-entry proof.
Issue #85 remains OPEN/BLOCKED_EVIDENCE. No acquisition/promotion/trading.

## Resume from here

Add the restricted GitHub-only audit workflow and static guard tests;
create PR linked to this plan, validate final head, merge when green,
inspect actual first GitHub-hosted diagnostic audit run. Keep #85
OPEN/BLOCKED_EVIDENCE irrespective of test success.
