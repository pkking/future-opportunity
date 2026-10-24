# Plan B — VPS UTC prospective Funding source capture (research only)

Issue: [#85](https://github.com/pkking/future-opportunity/issues/85).
Authorized 2026-10-19 after the first GitHub scheduled source collector was
delayed by more than two hours ([run #39186235557](https://github.com/pkking/future-opportunity/actions/runs/39186235557)).

This runbook is **not** evidence of a successful deployment. It installs
a deliberately small timer + one-shot read-only source recorder. No exchange
or GitHub token is needed and no source is transmitted off the VPS.

## Separation of responsibilities

| Component | Role | Evidence limitation |
| --- | --- | --- |
| Linux VPS + systemd | Primary UTC-day timer and read-only OKX two-GET capture | VPS is not an independent trusted time or OKX signature authority |
| VPS local ZIP + manifest | Original raw response, request/receive timing, deterministic feature replay | Locally generated manifest digest can be changed together with ZIP |
| Existing GitHub scheduled workflow | Secondary/diagnostic fallback (unchanged; best effort) | Its GitHub signature pertains only to **its own** GitHub-run bytes |
| GitHub Actions CI + preentry ZIP auditor | Deterministic tests and verification of an independently supplied archive/digest | GitHub cannot attest that a VPS byte stream existed before entry merely because it later processed it |

The VPS is the **primary** capture timer. The existing GitHub scheduled
workflow intentionally remains enabled as a distinct research-only
fallback. Do not merge these sources blindly: they have different
origin/provenance identities and might both observe the same UTC day.
No retrospective day is promoted, and no numerical economics gate,
acquisition authorization or live trading is activated.

**Pending external handoff**: No VPS host connection, off-host storage
destination, authentication boundary or object retention policy has
been provided. Consequently, **automatic transfer of VPS files to a
GitHub review artifact and any GitHub signature for VPS-collected bytes
is not implemented or asserted**. This is deliberately blocked rather
than putting a long-lived PAT or bucket secret in the repo or VPS unit.
The existing GitHub audit job continues to review only its own Actions
source ZIP. A future approved transport should convey immutable original
ZIP bytes and an independently recorded digest to a separate review job.
That job must identify its provenance as `vps_systemd_local_only`, not
`schedule`-originated GitHub collection; later GitHub attestation of
transferred bytes cannot retroactively establish VPS observation time.

## Prerequisites

- Linux VPS with systemd, a reliable UTC clock, functional network/DNS to
  `https://www.okx.com`, and available `timedatectl`.
- Python **3.12+**, `uv`, Git and outbound HTTPS. Prefer a fixed git SHA
  that has already passed repository CI and reviewed execution-plan tests.
- A working **systemd-timesyncd** service on the VPS. On the **host**,
  `timedatectl show --property=NTPSynchronized --value` must print
  **`yes`**, and `/run/systemd/timesync/synchronized` must exist
  and have been updated **within the past two hours**.
  The root-owned `/run` state is volatile across reboots, and the
  marker is touched on each successful timesyncd synchronization.
  This is a local operational guard, **not** an external timestamp or
  proof of current sub-second offset. The original sandboxed D-Bus
  `timedatectl` subprocess failed under DynamicUser in the first live
  run. The collector now reads the marker directly without using D-Bus.
  If a host uses chrony rather than timesyncd, a separate safe adapter
  must be implemented and reviewed; do **not** bypass NTP verification.
  `time-sync.target` alone does not prove NTP is synchronized.
- A root-owned immutable/read-only code checkout at
  `/opt/future-opportunity`. The service has no shell login,
  exchange secrets or GitHub personal-access token.

## Install (on the actual VPS, performed by its operator)

Review the exact merged commit before deployment. Commands below are
an example for a fresh Debian/Ubuntu VPS with an installed `uv`
binary on `PATH`; adapt package installation to the distribution.

```bash
sudo install -d -o root -g root -m 0755 /opt
sudo git clone https://github.com/pkking/future-opportunity.git /opt/future-opportunity
cd /opt/future-opportunity
# Pin to the reviewed main commit. Replace with the real merged SHA.
REVIEWED_SHA=REPLACE_WITH_VERIFIED_40_CHARACTER_MERGE_COMMIT_SHA
sudo git checkout --detach "$REVIEWED_SHA"
sudo uv sync --python /usr/bin/python3.12 --all-extras --dev
sudo chmod -R a+rX /opt/future-opportunity
```

**Lockfile note:** As of this version of the repository, `uv.lock` is **not** committed. Therefore do **not** use `uv sync --frozen` or `uv sync --locked` on a clean VPS checkout: both would reject a missing lockfile. The command above resolves the declared constraints and creates a local, untracked `uv.lock`. Pin the reviewed application Git commit, but recognize that dependency resolution is not fully reproducible across new hosts until a reviewed lockfile is committed. The proper follow-up is to version and CI-check a lockfile, then switch production instructions to a lock-enforcing invocation. For this VPS, `--python /usr/bin/python3.12` deliberately selects a system-accessible interpreter so the sandboxed `DynamicUser` can run `.venv/bin/python`; confirm the path exists before enabling the timer.

```bash
timedatectl status
timedatectl show --property=NTPSynchronized --value
systemd-analyze calendar --iterations=3 '*-*-* 00:00:10 UTC'

sudo install -m 0644 deploy/systemd/future-opportunity-funding-capture.service /etc/systemd/system/
sudo install -m 0644 deploy/systemd/future-opportunity-funding-capture.timer /etc/systemd/system/
sudo systemd-analyze verify /etc/systemd/system/future-opportunity-funding-capture.service /etc/systemd/system/future-opportunity-funding-capture.timer
sudo systemctl daemon-reload
sudo systemctl enable --now future-opportunity-funding-capture.timer
systemctl list-timers --all future-opportunity-funding-capture.timer
```

Do **not** run `systemctl start future-opportunity-funding-capture.service`
at an arbitrary time as a "smoke test": even an invalid late trigger creates
a durable `UNASSESSED` daily receipt, which is deliberately never overwritten.
Unit syntax and deterministic offline tests are the appropriate preflight.

Before declaring the deployment active, verify the actual `NEXT` time,
time-sync service health, UTC timezone, network resolution, service
sandbox availability and the next day's real journal. Using a VPS does
not provide hard real-time scheduling or prevent clock drift, downtime,
DNS/TLS failures, delayed data dissemination or exchange endpoint changes.

## First-run NTP incident and read-only sandbox preflight

The first VPS timer did fire at **2026-10-20T00:00:10Z**, but the
process reported `UNASSESSED` before either public GET: the original
`timedatectl` D-Bus call failed inside the `DynamicUser` sandbox
(`Failed to parse bus message: Transport endpoint is not connected`).
The host itself reported `NTPSynchronized=yes`. The status log for
that previous UTC interval is empty, which is not a proof of past sync.
The original 2026-10-20 error ZIP/manifest must remain intact.

The corrected gate reads the systemd-timesyncd synchronization marker,
requires an ordinary **non-symlink** file with an mtime no older than
7200 seconds and no future timestamp, and rejects absent, inaccessible
or stale markers *before* contacting OKX. systemd-timesyncd's default
maximum poll interval is 2048 seconds. This freshness guard checks only
local operational time state; it cannot independently authenticate the
clock, exact offset or OKX publication.

Before the next UTC trigger, run a no-source diagnostic on the host:

```bash
timedatectl show -p NTPSynchronized --value
sudo stat -c 'last-sync: %y / permissions: %a' /run/systemd/timesync/synchronized

sudo systemd-run --unit=funding-marker-probe --wait --pipe --collect \
  -p DynamicUser=yes -p ProtectSystem=strict \
  -p ProtectHome=yes -p PrivateTmp=yes -p PrivateDevices=yes \
  -p NoNewPrivileges=yes \
  -p 'RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6' \
  /opt/future-opportunity/.venv/bin/python -c '
import os, stat, time
path = "/run/systemd/timesync/synchronized"
info = os.lstat(path)
age = time.time() - info.st_mtime
ok = stat.S_ISREG(info.st_mode) and 0 <= age <= 7200
print("marker_age_seconds:", round(age), "valid:", ok)
raise SystemExit(0 if ok else 1)
'
```

This read-only diagnostic has **no** source GET, no dated archive write
and no trading. The probe must finish with `valid: True`. If it fails,
inspect `systemctl status systemd-timesyncd`, `timedatectl
timesync-status` and the marker permissions. Do not remove
`DynamicUser` or silently turn off NTP validation.

**Upgrade an installed VPS:** after this PR is merged and all final-head
CI gates pass, check out its **actual squash-merge commit SHA** (do not
guess or pin a branch by name), run the documented dependency
installation if needed, and verify the marker probe. No service unit
change is needed; the existing timer continues automatically. Do not
manually start the one-shot service outside the UTC capture window.
If the previous day has an `UNASSESSED` receipt, preserve it; the
next UTC calendar day remains an independent new attempt.

## Per-day behavior and operational inspection

- Timer: `OnCalendar=*-*-* 00:00:10 UTC`,
  `AccuracySec=1s`, `RandomizedDelaySec=0`,
  `Persistent=false`. No restart/retry/catch-up. A delayed timer
  runs only once; the source script rejects any attempt at or after
  **00:15 UTC**.
- One-shot service: `DynamicUser=yes`, `StateDirectory`, read-only
  root tree, no privilege elevation; **recent systemd-timesyncd marker**
  (no D-Bus) before first public request. This local freshness check is
  **not** a signed third-party time measurement.
- Existing `capture_today`: no credentials, exactly two bounded
  public GETs and strict event/HTTP-time anti-lookahead validation.
  No additional source retries or historical API backfill.
- Every attempted UTC day becomes at most one owner-private directory:
  `/var/lib/future-opportunity-funding/YYYY-MM-DD/` containing
  `original-source.zip` and `manifest.json`. Success ZIP contains
  exactly the original `raw-api-capture.json`, `http-timing.json`,
  `preentry-research-evidence.json`. On any failure it contains
  only `error.json`, and `manifest.status=UNASSESSED`,
  `entry_market_date=null`. Partial source output is discarded.
- Before finalizing a successful day, the wrapper replays the archive
  through the existing `audit_zip` with its exact UTC entry day.
  The calculated ZIP SHA-256, raw-file digest, canonical-source digest
  and immutable local manifest are recorded. This replay checks
  **internal consistency only**; digest and archive are both local.
- Once present, the daily directory may not be replaced or retried.
  If the host is offline all day, there is **no** receipt; absence is
  missing evidence, not a zero. Never backfill that date.

```bash
sudo systemctl status future-opportunity-funding-capture.timer
sudo journalctl -u future-opportunity-funding-capture.service --since yesterday --no-pager
sudo find /var/lib/future-opportunity-funding -mindepth 2 -maxdepth 2 -type f -print
sudo cat /var/lib/future-opportunity-funding/$(date -u +%F)/manifest.json
sudo sha256sum /var/lib/future-opportunity-funding/$(date -u +%F)/original-source.zip
```

For an independently archived copy (after installing suitable encrypted
off-host storage and verifying the transfer policy), retrieve
`original-source.zip` **without modifying or repacking it**. Use a
separately witnessed SHA-256 and UTC day in the existing verifier:

```bash
uv run python scripts/audit_funding_preentry_source_artifact.py \
  --zip original-source.zip \
  --expected-zip-sha256 "<independently obtained SHA-256>" \
  --entry-date "YYYY-MM-DD"
```

Do not promote `local_replay_only` to
`point_in_time_publication_verified=true`: that requires a separately
reviewed cryptographic/provenance policy and genuine exchange publication
proof. Repo CI and GitHub source attestation are different concepts.

## Independent review of VPS-origin evidence (no collector credentials)

The first successful local observation is the **2026-10-21** record; on the
VPS the original ZIP SHA256 printed and recorded separately by the operator is:

```text
6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a
```

This digest came from the **same VPS**, not an independently timestamped
source witness. We have reviewed the user's journal, manifest and local
sha256 output; the agent has **not** downloaded the actual ZIP.

A reviewer on a **different trusted machine** can copy the two original
files after the collection has already completed. For example, with a
pre-established authenticated SSH host key and a locally authorized
operator (who can read the owner-private VPS state), execute on the
**reviewer** machine:

```bash
umask 077
mkdir -p evidence/2026-10-21
scp -p root@YOUR_VPS_HOST:/var/lib/future-opportunity-funding/2026-10-21/manifest.json \
  evidence/2026-10-21/manifest.json
scp -p root@YOUR_VPS_HOST:/var/lib/future-opportunity-funding/2026-10-21/original-source.zip \
  evidence/2026-10-21/original-source.zip
```

The sample uses root SSH only if already authorized and configured; a
dedicated read-only export account/SSH forced command is preferable
for ongoing production operation. Never disable SSH host-key checks,
put private keys in the repo, or copy files into Git history.
Do not recompress, unzip/re-zip or mutate the originals.

In an independent checkout of this repository (Python 3.12+ with installed
project dependencies), review the original VPS ZIP and exact accompanying
manifest **offline**, specifying the UTC day and the expected SHA-256
**from a separately recorded channel**, not reading it back from
the same manifest:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_vps_funding_capture.py \
  --manifest evidence/2026-10-21/manifest.json \
  --zip evidence/2026-10-21/original-source.zip \
  --entry-date 2026-10-21 \
  --expected-zip-sha256 6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a \
  --receipt-out evidence/2026-10-21/offhost-review.json
```

The reviewer replays all three original success JSON files through
the existing anti-lookahead validator, checks exact owner-reported
manifest identity, original ZIP SHA256, raw-file SHA256, canonical source
SHA256 and regime. For any genuine error-only original ZIP, it instead
returns `failed_capture_unassessed`, with null market date. Tampering
with either original bytes or any manifest safety flags fails closed.
`--receipt-out` creates a private JSON file **only if absent**:
it never overwrites a prior independent review. The review includes
`reviewed_at`, which is **the review time**, not the time the VPS first
captured the response; `expected_digest_origin_authenticated=false`
and all signing/publication/acquisition/promotion flags remain false.
This workflow never sends requests to OKX, does not invoke GitHub
attestation, and cannot create a retroactive trusted timestamp.

For a genuinely credible **point-in-time availability witness** on future
UTC days, the original bytes or a cryptographic commitment to them
must reach an independently controlled, authenticated append-only
sink *before* the 00:15 UTC research entry boundary, with externally
verifiable time and retention. A transfer performed hours later
can at best witness availability at **transfer time**, not at the
earlier entry. Off-host storage choice, operator identity,
credential/rotation, WORM retention, timestamp attestation and
failure-recovery policy require their own security review/approval;
they have intentionally not been silently provisioned here.
GitHub's signed attestations to GitHub-origin runs do not authenticate
a distinct VPS-origin HTTP response. In particular, never pass this
VPS ZIP to `audit_scheduled_funding_capture.py` as if it came from
a GitHub `schedule` workflow run.

Until those independent claims and the missing
negative-Funding/low-volatility regime are proven, #85 remains
OPEN/BLOCKED_EVIDENCE; do not pin, promote, or enable trading.

## GitHub-only prospective handoff (optional, operator opt-in)

**Approved constraint:** use only GitHub public/open-source repository
features; **no** OBS/S3, external TSA, other object store or third-party
secret service. GitHub Actions Artifacts expire in at most 90 days for
public repos and cannot be the sole long-term evidence store.

**GitHub-native choice:** one per-day **Immutable Release** named
`funding-vps-YYYY-MM-DD`. A distinct *post-capture* systemd service
starts only upon the source recorder's successful exit; it creates a
**draft** Release, uploads the original exact
`original-source.zip` and `manifest.json`, checks GitHub's returned
server-side `digest`, `created_at`, and `size` for each asset, and
then publishes before the same day's 00:15:00 UTC deadline. The GitHub
`published_at` must be in-window and the published release must report
`immutable=true`. If GitHub replies late/incorrectly, nothing becomes
a valid witnessed pre-entry observation. No source GET is retried, no
previous date is published, and the uploader never deletes/updates a
Release or uploads replacement assets. A partially created **draft**
may remain after failure and requires operator review, not automatic
destructive cleanup or retroactive publication.

**Owner enablement is REQUIRED before installation:**

1. Confirm this repository remains **public** and publication of the
   unauthenticated OKX response ZIP is acceptable. Release assets
   become publicly downloadable.
2. In `pkking/future-opportunity` → **Settings → General → Releases**,
   check **Enable release immutability**. It only applies to future
   Releases. The account/repo owner must do this; an agent without repo
   admin permissions cannot switch it on.
3. Provision a dedicated GitHub-only, repository-restricted credential
   with **Contents:write** and no other privilege, after reviewing how
   it is issued and rotated. A fine-grained token is the simple
   operational option; a narrow GitHub App installation credential is
   preferable when lifecycle automation is available. Do **not**
   place a token in Git, workflow input, environment variables, issue
   comments, the source collector or source ZIP. The example isolated
   systemd publisher reads it via `LoadCredential` only.
   User must authorize/configure this identity; repository code
   **never creates or stores a token**.

**Optional VPS installation after exact reviewed merge SHA:**

```bash
cd /opt/future-opportunity
git rev-parse HEAD
sudo install -d -m 0700 /etc/future-opportunity
# Operator installs an authorized, mode 0600 root-owned GitHub token at:
#   /etc/future-opportunity/github-token
# Do not echo/show/paste that token into command history or chat.
sudo install -m 0644 \
  deploy/systemd/future-opportunity-funding-github-publish.service \
  /etc/systemd/system/future-opportunity-funding-github-publish.service
sudo mkdir -p /etc/systemd/system/future-opportunity-funding-capture.service.d
sudo install -m 0644 \
  deploy/systemd/future-opportunity-funding-capture.service.d/10-github-publish.conf \
  /etc/systemd/system/future-opportunity-funding-capture.service.d/10-github-publish.conf
sudo systemd-analyze verify \
  /etc/systemd/system/future-opportunity-funding-capture.service \
  /etc/systemd/system/future-opportunity-funding-github-publish.service
sudo systemctl daemon-reload
sudo systemctl status future-opportunity-funding-capture.timer
```

**Do not install the opt-in drop-in until all three prerequisites pass.**
There is no `[Install]` section on the publisher; it is not separately
enabled or scheduled. A successful original collector makes systemd
fire `OnSuccess` only after writing the original ZIP. This is an
additional outbound GitHub transfer with a separate `DynamicUser`
and dedicated token; GitHub failures do **not** alter collector
success, trigger source retries, or overwrite the original receipt.
No manual start outside the current-day 00:00–00:15 window.

**Independent GitHub-only public review:**

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_github_vps_release.py \
  --entry-date YYYY-MM-DD

# When gh CLI is installed on the verifier, verify GitHub's automatic
# immutable Release provenance independently (read-only):
gh release verify funding-vps-YYYY-MM-DD --repo pkking/future-opportunity
# Download exact original source ZIP from that specific Release, then:
gh release verify-asset funding-vps-YYYY-MM-DD original-source.zip \
  --repo pkking/future-opportunity
```

The public auditor downloads original assets from the public GitHub
Release, checks the official GitHub asset digest and server
`created_at` for each, requires in-window `published_at` and
`immutable=true`, and runs full original-source offline replay.
The CLI attestation commands are **separate** validation operations;
the Python auditor explicitly reports
`github_release_attestation_verified=false` until a different actor
checks the signed GitHub provenance. Any future verifier must compare
the exact GitHub release/tag/asset content, not merely parse a copied
JSON receipt. GitHub has operational control of its public server
metadata; we trust it only to state that *GitHub* hosted these bytes
before entry, **not** that OKX first disseminated them by then.

Official GitHub docs:
- https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository

**Automatic GitHub-only post-publication review:** after a future
`funding-vps-YYYY-MM-DD` Release is published, the repository's
[`Audit Immutable VPS Funding Evidence Release`](../../.github/workflows/audit-funding-vps-github-release.yml)
workflow triggers on GitHub's `release.published` event. It runs on
a free standard GitHub public-repo runner with **read-only Contents**
permission; fetches the public original ZIP and manifest, checks
server-side immutable status, pre-entry `created_at` and
`published_at`, exact hashes and original-source offline replay,
then separately runs GitHub CLI `gh release verify` and
`verify-asset`. A successful read-only workflow writes a derived
provenance review with GitHub signature checks recorded as passed,
while retaining `point_in_time_publication_verified=false`.
Any error preserves a separate `UNASSESSED` workflow review
artifact for up to 90 days; original bytes remain in the published
Immutable Release. GitHub Actions audit queue delays cannot affect the
original GitHub Release's server-side source receipt timing.
`release.published` itself is best-effort for timely audit execution;
if it is delayed or missed, the original Release remains independently
downloadable for later manual verification. The workflow does not
send market API requests, change the Release or write to the repository.

**No 2026-10-21 retroactive claim:** the original 2026-10-21 source
was locally collected in time, but copying it to GitHub later
cannot certify that a GitHub asset already existed before 00:15.
This new pathway is prospective-only starting with a **future** UTC
day after proper repo admin/credential configuration. Issue #85
remains BLOCKED_EVIDENCE; Funding 32 and Cash 66 do not change.

## Rollback and security

Disable only the VPS timer without deleting evidence:

```bash
sudo systemctl disable --now future-opportunity-funding-capture.timer
```

Retain original owner-private daily directories for audit; arrange
encrypted off-host backup and explicit retention before operational
reliance. Do not send raw responses, SSH private keys, or access tokens
into GitHub issue comments or commit them to the repository.
Restrict VPS outbound access to the public OKX endpoint, OS package
mirrors and update services where feasible; enable disk monitoring and
alert on missing daily directories or `systemctl --failed`.

References: systemd `systemd.timer(5)`, `systemd.exec(5)`;
GitHub Actions `schedule` best-effort documentation and
`docs/research/funding-prospective-point-in-time-capture-contract.md`.


## Daily GitHub-only missing-release and audit-health watch (Issue #85)

A **separate** GitHub Actions
[`Watch Funding VPS Immutable Release Health (Read-only)`](../../.github/workflows/watch-funding-vps-release-health.yml)
checks whether an expected **published** `funding-vps-YYYY-MM-DD`
Immutable Release exists and was uploaded/published within UTC
00:00..00:15. It only uses GitHub's built-in free public repository
features, `contents: read` and `actions: read`. There is **no**
new VPS service, no OKX requests, and no GitHub Release/tag writes.

The watcher also runs the existing **strict original ZIP + manifest
offline replay** from GitHub and requires a **successful**
`Audit Immutable VPS Funding Evidence Release` `release.published`
workflow run matching that **exact same tag**. A Release alone is NOT
enough to claim that independent GitHub attestation checks succeeded.

- `RELEASE_AND_INDEPENDENT_AUDIT_VERIFIED`: complete source and
  independent Release audit evidence, **only** GitHub-side pre-entry
  custody, **not** exchange publication timing.
- `MISSING_PUBLISHED_RELEASE`: public GitHub returned 404 for the
  expected exact tag **after** the 00:15 UTC deadline.
- `INVALID_RELEASE`: existed but original ZIP/manifest replay, hash,
  immutable attribute, or signed server publication-time condition
  failed. A historical late diagnostic tag is NOT a substitute.
- `AUDIT_MISSING`, `AUDIT_PENDING`, `AUDIT_FAILED`: the
  independent `release.published` auditor for the exact tag did
  not exist, had not finished, or failed respectively.
- `UNASSESSED`: GitHub API/transport/permission failure or evidence
  not available yet; **never** silently call that a missing or empty
  market observation.

Scheduled daily at **00:41 UTC**, the watcher examines up to three
recent completed UTC entry days. The first production monitoring day
is **2026-10-23**; earlier diagnostics are explicitly excluded from
missing-day alerts. GitHub Actions cron is best-effort; delayed or
dropped executions remain possible, so the rolling review improves
recovery but does **not** ensure zero undetected gaps when GitHub
itself is unavailable. The full offline verifier can be re-run
manually without market GET or altering source:

```bash
# GitHub Actions → Watch Funding VPS Immutable Release Health (Read-only)
# → Run workflow, optional entry_day: YYYY-MM-DD
# Or from a trusted local checkout using a read-only GH_TOKEN:
PYTHONPATH=src .venv/bin/python scripts/check_funding_release_watch.py \
  --days 3 \
  --output /tmp/funding-release-health.json
```

Each workflow attempt retains a **derived** JSON report, including
explicit `UNASSESSED` on failure, under Actions Artifact
`funding-vps-daily-release-health` for at most 90 days.
**The workflow itself fails** if any target day lacks the required
Release or completed successful independent audit. Look at GitHub
Actions run history and enable repository notification preferences
to see these failures; a new external notification service is
intentionally out of scope. If no GitHub scheduled job starts at
all, this GitHub-only approach cannot send an external alert.

Original immutable ZIPs live in the corresponding GitHub Releases;
neither the watcher nor its report modifies them. The watcher never
changes `point_in_time_publication_verified=false`,
`exchange_signed=false`, `acquisition_approved=false` or
`promotion_approved=false`. No Stage-2 corpus eligibility, trade,
historical backfill, or market-profit inference is authorized.


## Optional, no-write VPS publisher preflight

Before future daily captures, an operator may execute a **read-only**
self-check on the already configured VPS without starting any collector,
publisher or systemd timer, and **without creating a GitHub Draft Release**.

```bash
cd /opt/future-opportunity

# Reads root-owned 0600 /etc/future-opportunity/github-token internally;
# prints a redacted report, never the Token.
sudo env PYTHONPATH=src .venv/bin/python \
  scripts/preflight_vps_funding_github_publisher.py \
  --source-day 2026-10-23
```

The optional `--source-day` must be a **real, already published**
prospective source day. To check host configuration only, omit this
flag. Do **not** pass the historical diagnostic
`diagnostic-funding-vps-2026-10-21`, since its tag and late
publication were not eligible for prospective source qualification.
The check is safe outside the UTC 00:00..00:15 capture window.
No `sudo systemctl start`, replay of missing exchange HTTP data
or manual Release publishing is required.

Preflight is **not enabled as an ExecStartPre or timer dependency**:
the existing proven original collector/OnSuccess runtime is unchanged.
The script verifies:

- recent `/run/systemd/timesync/synchronized` marker using the
  same local NTP freshness guard as the collector (not externally
  authenticated clock evidence);
- a private existing systemd Funding `StateDirectory`, plus local
  publisher unit and `OnSuccess` drop-in configuration files;
- root-owned, ordinary `0600` credential file; missing, symlinked,
  empty, newline-terminated, wrong-owner or over-permissive files
  are rejected. **Never print the Token**;
- an authenticated **HTTPS GET only** to the expected **public**
  GitHub repository with the existing Token; this checks current
  read-only credential acceptance, **NOT** `Contents:write`;
- if requested, independent *public* metadata and original ZIP+
  manifest offline replay of the selected prior immutable Release.

Report status is `PREFLIGHT_READ_ONLY_PASS` only when all required
checks pass. A false/missing prerequisite or unavailable GitHub
API is explicitly `UNASSESSED` and causes a nonzero exit. Every
report conservatively retains
`github_contents_write_permission_verified=false`,
`publisher_dynamic_user_runtime_verified=false`,
`github_release_immutability_setting_verified=false`,
`point_in_time_publication_verified=false` and all acquisition,
promotion and trading approvals disabled. File metadata cannot prove
that systemd has reloaded configurations, the future ephemeral UID
has directory access, GitHub's write grants are valid, or the
next real API call will succeed. Those remain covered by actual
post-capture and independent Release health monitoring.

Separate **offline MockTransport tests** inject GitHub draft,
first/second asset upload, and final publication errors/timeouts,
plus UTC deadline transitions after partial upload. A partially
created GitHub **Draft** may remain on the server after a failure;
it must **not** be confused with an immutable, published, signed
Release, and the collector must not be restarted to backfill it.
The daily [GitHub-only Release health watcher](../../.github/workflows/watch-funding-vps-release-health.yml)
will treat a missing *published* Release as missing evidence after
the cutoff. No automated cleanup, retry, overwrite or promotion
is authorized by the preflight or failure-injection suite.


## Audited prospective Funding 2×2 regime inventory (Issue #85)

The daily `funding-vps-daily-release-health` artifact's `health.json` now includes
`regime_coverage`. It is computed exclusively from the **exact UTC days
checked by that watcher invocation** (three by default, maximum seven).
No market HTTP request is made to assemble the summary.

- `strata` fixes the four existing Funding-sign × 100bps trailing-volatility
  classes. Each bucket contains `count` and exact sorted UTC `dates`.
- `github_audited_day_count` includes a date **only** after original ZIP
  offline replay and a matching successful independent `release.published`
  audit; this is GitHub source custody, **not** OKX-authenticated publication.
- `checked_day_count` and `non_audited_days` preserve dates with missing,
  invalid, pending or failed Release/audit evidence. An unverified regime
  string cannot fill an empty bucket. An unknown verified regime or
  contradictory source flags causes explicit `UNASSESSED`, not HEALTHY.
- `empty_strata` describes *the checked window only*. It is **not**
  evidence of zero market opportunities, nor a stable cross-month regime
  distribution. Dates outside the bounded lookback were not inspected.
- `market_wide_opportunity_arrival_rate=null` and
  `point_in_time_publication_verified=false`, `exchange_signed=false`,
  `acquisition_approved=false`, `promotion_approved=false` remain
  unchanged. Do **not** add these days to pinned Funding history or Stage-2
  readiness using the inventory.

For a specific earlier production day, run the existing read-only watcher
with `--entry-day YYYY-MM-DD`. To inspect a different bounded rolling
window locally, use `--days 1..7`. Both read existing GitHub evidence
only, and neither backfills missing days or changes source evidence.
