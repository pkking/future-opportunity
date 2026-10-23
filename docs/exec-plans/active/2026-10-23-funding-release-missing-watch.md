# Prospective Funding GitHub Release missing-day and audit-failure watch

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-23

## Objective

Close the silent gap when the VPS collector or publisher **does not
produce** a normal `funding-vps-YYYY-MM-DD` GitHub Immutable Release
and the existing `release.published` audit workflow therefore never
fires. Produce a bounded, read-only, GitHub-only daily health result.
No new source capture, Release upload, credential, historical replay
selection, corpus promotion, trading action or external storage.

## Baseline facts

- Real 2026-10-23 local VPS capture succeeded: the original ZIP SHA256
  `bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068`
  matches immutable GitHub Release assets, published at 00:00:15 UTC.
- Read-only `release.published` audit Run #39875400476 SUCCESS
  with real ZIP offline replay and release attestation.
- GitHub's own scheduled collector Run #39886593562 started at
  01:54 UTC and failed **closed**. Its failure must not overwrite
  or contradict the real VPS→Release source success.
- 2026-10-21 old diagnostic Release was published late and cannot
  retroactively count as an independent preentry witness.
- GitHub Actions `schedule` can start late or be skipped. Its
  *execution time* does not prove source publication time. Checking
  multiple recent days mitigates occasional skipped watcher runs, but
  cannot guarantee detection if every GitHub scheduled event is dropped.
- Surveillance begins with 2026-10-23, not retrospective alerts
  for the intentionally absent prospective Releases of prior dates.

## Acceptance criteria

- [ ] New `scripts/check_funding_release_watch.py` supports an
      injectable aware UTC clock, read-only public GitHub client, UTC
      date validation, latest three *completed* entry windows,
      go-live floor of 2026-10-23 and optional fixed day for review.
- [ ] Fetch exact official GitHub Release tag. A genuine Release 404
      means no **published** Release is visible; record
      `MISSING_PUBLISHED_RELEASE` and fail watcher run; never
      silently report a zero-return/no opportunity.
- [ ] Reuse `audit_github_vps_release.verify_release` to enforce
      original ZIP+manifest correct bytes, immutable status and
      GitHub server timestamps before **same-day** 00:15 UTC.
      Late/altered/incomplete source is `INVALID_RELEASE`; transport
      / authentication / API failures are `UNASSESSED`, not missing.
- [ ] Require a `release.published` GitHub Actions audit run
      associated with the **same exact tag** and `success`; report
      `AUDIT_PENDING`, `AUDIT_MISSING`, `AUDIT_FAILED` otherwise.
      Never infer a successful audit from presence of Release.
- [ ] Workflow fires daily at **00:41 UTC** best-effort, and
      `workflow_dispatch`, plus a one-off path-scoped **main branch**
      trigger for first validation; read-only `contents: read`
      and `actions: read`, no GitHub writes, additional secrets,
      source market HTTP, exchange APIs or downloads to source corpus.
- [ ] Each execution writes exact bounded JSON (including failures),
      always uploads **derived** review as 90-day Actions Artifact,
      job nonzero on missing/invalid/pending/failed/unassessed,
      preserving false exchange/signature/source approval flags.
      Workflow job failure can be surfaced via GitHub Actions
      notification preferences, without a separate notification
      provider or automatic Issue writes.
- [ ] Offline deterministic MockTransport tests for legitimate same-day
      GitHub Release+successful audit, absent release, late publish,
      altered ZIP, malformed release, pending/failed/missing audit,
      403/5xx/network errors, premature check, date boundaries,
      3-day late/skipped schedule recovery, and no retrospective
      before-rollout false alert. Static workflow policy tests.
- [ ] PR final-head all five CI checks + Historical Backtest Smoke,
      squash merge, postmerge main CI and genuine read-only
      first-run watcher success against existing 2026-10-23 Release.
      Record results in Issue #85 without claiming OKX first-publication
      time or research corpus graduation.

## Implementation slices

- [ ] New deterministic release + audit state classifier and JSON CLI.
- [ ] Read-only daily/dispatch workflow with safe failure artifact.
- [ ] No-network edge-case and workflow policy tests.
- [ ] Operator runbook and complete validation.
- [ ] Merge, postmerge and live health watcher verification.

## Verification matrix

| Scope | Method | State |
|---|---|---|
| Offline checker | `uv run pytest tests/test_funding_release_watch.py` | Pending |
| GitHub only permissions and event rules | `uv run pytest tests/test_funding_release_watch_workflow.py` | Pending |
| Full static, API, code, E2E, historic | Five CI jobs + Historical Smoke | Pending |
| Published 2026-10-23 health | Real GitHub-hosted watcher on main | Pending |
| Postmerge base | Main CI | Pending |

## Decision gates

None. Only reads from the existing public GitHub repository and
reuses accepted source verification. A separate external watchdog
would be needed to guarantee that no GitHub schedule is ever missed;
out of scope because only GitHub-native capabilities are allowed.

## Resume from here

Implement pure read-only health checker and reproducible tests, wire
safe read-only daily workflow, review final-head CI/Smoke, squash
merge if green and verify the initial real main watcher run. Leave
Issue #85 OPEN/BLOCKED_EVIDENCE: no independently proven OKX
publication time, no negative-funding/low-volatility cohort, no
research sample promotion.

## Completion

In progress. No new API market source request, Release, tag or
original ZIP mutation authorized.
