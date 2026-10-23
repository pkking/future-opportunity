# Funding VPS GitHub publisher: safe read-only preflight and fault injection

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-10-23

## Objective

Introduce an **operator-invoked, read-only**, secret-safe preflight for the
existing VPS Funding GitHub publisher and deterministic fault-injection tests
for partial GitHub API failures. Operators can diagnose credential-file, host
clock, local source receipt and GitHub read connectivity risks **outside**
the UTC 00:00..00:15 publication window, without capturing, creating a
Release/draft/tag, updating a Token, or modifying immutable source evidence.

## Baseline facts

- Production VPS→Github immutable Release for 2026-10-23 was created
  at UTC 00:00:15 and source original ZIP SHA256
  `bbf7bb90e6d95fd12573d92943ddac682bb5ac2d4c5538fcb9906b97ebff3068`.
- Independent `release.published` audit Run #39875400476 succeeded.
- Missing-day health watcher from PR #136 succeeded for 2026-10-23.
- Existing publisher rejects backfill, uses `LoadCredential`, strictly
  enforces NTP-conditioned upstream collector and GitHub server
  asset/release metadata; original collector and publisher run as
  separate systemd `DynamicUser` one-shots.
- Real VPS runtime credentials and UID namespace cannot be exercised
  by an isolated GitHub Actions runner. Even a valid read-only REST
  request **cannot establish** `Contents:write` authorization or
  future GitHub availability, and repo admin immutability settings
  are not exposed via the current app connection.

## Acceptance criteria

- [x] Add a separate CLI script `scripts/preflight_vps_funding_github_publisher.py`
  which **only** reads owner-protected host metadata / an independently
  chosen already-published source date and performs GitHub HTTPS GET.
  Do not import or invoke any publisher mutating entry points, market
  collector, systemd trigger, GitHub POST, PATCH or DELETE.
- [x] Validate the credential file is a root-owned regular file,
  no symlink, `0600`; use its bytes **only for an authenticated
  read-only GET** to GitHub and never output token, headers, hash or
  length. Confirm repository identity and public visibility.
- [x] Validate current NTP marker freshness with existing function,
  current UTC clock aware, static systemd optional publisher unit /
  `OnSuccess` drop-in config match, and local private state directory.
  Don't claim this proves future runtime UID can access it.
- [x] For a supplied prior UTC entry day, revalidate the exact existing
  published Release with the strict current original-source reviewer,
  without changing/republishing it; require `immutable=true` and
  correct original asset timing. Otherwise report source as UNASSESSED.
- [x] Produce a fixed-size, machine-readable safe report with per-check
  PASS/FAIL/UNASSESSED and no secret values; nonzero on any failure,
  no authorization/trading/research promotion conclusion.
- [x] Run deterministic no-network positive/negative tests including
  credential symlink/mode/owner, stale NTP marker, GitHub 401/403/500
  and transport faults, wrong repo identity, missing source, plus
  policy tests forbidding writes or source-market calls.
- [x] Add negative fault injection to existing publisher's GitHub API
  phases: draft creation failure, first/second asset upload failure,
  POST timeout or PATCH network failure, asset mismatch, clock passes
  00:15 mid-upload. Assert no premature publish/replay, never overwrite
  or retry a missing-day original and no credential leakage.
- [x] Update runbook with **opt-in manual** command, warnings about
  non-proven GitHub write privilege and no automatic systemd change.
- [x] Final-head five CI checks and Historical Smoke, squash merge,
  postmerge main CI; record exact Issue #85 checkpoint.

## Implementation slices

- [x] Read-only host + authenticated public GitHub preflight module.
- [x] Deterministic MockTransport checks and publisher fault-injection tests.
- [x] Operator runbook including no-secret output/security limits.
- [x] PR final-head CI, Historical Smoke, postmerge and checkpoint.

## Verification matrix

| Gate | Evidence | Result |
| --- | --- | --- |
| Preflight no-network tests | `tests/test_funding_vps_publisher_preflight.py` in required code-level CI | PASS |
| Publisher negative phase tests | `tests/test_funding_github_release_faults.py` in required code-level CI | PASS |
| Repo static/code-level checks | PR #138 final-head [CI #39992521987](https://github.com/pkking/future-opportunity/actions/runs/39992521987) | PASS |
| API/E2E/Historical | PR #138 full 5 CI jobs and [Historical Smoke #39992522030](https://github.com/pkking/future-opportunity/actions/runs/39992522030) | PASS |
| Postmerge main | [CI #39992693968](https://github.com/pkking/future-opportunity/actions/runs/39992693968) | PASS |
| Real VPS operator-run preflight | Host runtime and token not available through GitHub integration | UNASSESSED |

## Decision gates

No irreversible user decision; GitHub-only read access and local-file
checks stay within accepted architecture. Do **not** install a new
systemd unit, mutate provider secrets, or create an actual Release.
Any automated VPS rollout is operator-controlled.

## Resume from here

This preflight/fault-injection development slice is complete; owner
may run the **new read-only CLI** after updating the VPS checkout
without changing/restarting any systemd services. Revalidate the
actual GitHub-only daily release health watcher at the next scheduled
UTC 00:41 execution and monitor GitHub cron delays independently.
Issue #85 remains OPEN/BLOCKED_EVIDENCE on OKX first publication,
negative-Funding/low-volatility historical coverage, and Stage 2.

## Completion

Final commit: `f3654f3b40de6b504dd4205556aa5be75527c3b6`
(PR #138 squash merge).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39992521987
(5 required CI checks SUCCESS);
https://github.com/pkking/future-opportunity/actions/runs/39992522030
(Historical Backtest Smoke SUCCESS);
https://github.com/pkking/future-opportunity/actions/runs/39992693968
(postmerge main CI SUCCESS).
Remaining unassessed items: Real VPS invocation of
`scripts/preflight_vps_funding_github_publisher.py` not performed
through GitHub integration; authenticated public GET alone cannot
prove `Contents:write` permission, runtime DynamicUser access, or
future GitHub reliability. Never run a forced source collector or
backdate an immutable Release to test the preflight. GitHub does not
authenticate when OKX independently first published data; Funding
32 and Cash 66 pinned unchanged, and no acquisition/promotion/trading
approval. Parent Issue #85 remains OPEN/BLOCKED_EVIDENCE.
