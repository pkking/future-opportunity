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
- A working NTP time synchronization service: `timedatectl show
  --property=NTPSynchronized --value` must print **`yes`**.
  This property depends on the host's time synchronization stack.
  If using chrony with a different integration, configure your OS's
  time-sync reporting explicitly rather than bypassing the application
  guard. `time-sync.target` alone does not prove NTP is synchronized.
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

**Lockfile note:** As of this version of the repository, `uv.lock` is **not** committed. Therefore do **not** use `uv sync --frozen` or `uv sync --locked` on a clean VPS checkout: both would reject a missing lockfile. The command above resolves the declared constraints and creates a local, untracked `uv.lock`. Pin the reviewed application Git commit, but recognize that dependency resolution is not fully reproducible across new hosts until a reviewed lockfile is committed. The proper follow-up is to version and CI-check a lockfile, then switch production instructions to a lock-enforcing invocation. For this VPS, `--python /usr/bin/python3.12` deliberately selects a system-accessible interpreter so the sandboxed `DynamicUser` can run `.venv/bin/python`; confirm the path exists before enabling the timer.

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

## Per-day behavior and operational inspection

- Timer: `OnCalendar=*-*-* 00:00:10 UTC`,
  `AccuracySec=1s`, `RandomizedDelaySec=0`,
  `Persistent=false`. No restart/retry/catch-up. A delayed timer
  runs only once; the source script rejects any attempt at or after
  **00:15 UTC**.
- One-shot service: `DynamicUser=yes`, `StateDirectory`, read-only
  root tree, no privilege elevation; explicit `NTPSynchronized=yes`
  before first public request. This property is an operational
  sanity check **not** a signed third-party time measurement.
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
