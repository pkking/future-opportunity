# ADR-0010: VPS-local prospective Funding source scheduler

- Status: Accepted (architecture choice explicitly approved 2026-10-19)
- Date: 2026-10-19
- Extends: ADR-0006, ADR-0008
- Issue: #85

## Context

Funding Stage-2 retrospective evidence remains unverified as-of-entry and its
negative-Funding/low-volatility regime is unobserved. To collect
prospective UTC 00:00–00:15 observations, prior PRs #121–#126
implemented a strict read-only OKX source collector, future-day GitHub
Actions manual and scheduled workflows, and artifact/signature review.

The first scheduled event [#39186235557](https://github.com/pkking/future-opportunity/actions/runs/39186235557)
was created at `2026-10-19 01:37:54 UTC`, about two hours late versus
the immediately preceding intended `23:37 UTC` trigger. GitHub Actions
`schedule` is explicitly best effort. This makes GitHub unsuitable as
the primary mechanism for guaranteeing even an attempted pre-entry
observation on each day.

The user approved option B on 2026-10-19: use a VPS `systemd timer`
as primary capture scheduling, preserving existing safety gates.
No VPS address, runtime/OS inventory or secure off-host evidence
destination was supplied to the implementation agent.

## Decision

1. Use a small root-owned code checkout and sandboxed, non-root
   `systemd` one-shot service, triggered daily at **00:00:10 UTC**
   (`AccuracySec=1s`, `Persistent=false`, `Restart=no`).
   A missed/late systemd firing is **not** rescued by a timestamp
   override or next-day backfill.
2. Reuse the original `capture_today` completely unchanged. It remains
   exactly two bounded unauthenticated public GETs, both completed before
   strict UTC 00:15. Require operational NTP sync status before any GET.
3. Locally spool at most one immutable dated receipt per UTC day,
   either the original three capture JSON files in a ZIP with a
   successful deterministic replay, or one `UNASSESSED` error file.
   Record only locally created SHA-256s; never label them independent,
   GitHub-signed, or exchange-authenticated source provenance.
4. Existing GitHub Actions remains responsible for repository CI and
   the **GitHub-origin** source workflow's own signed evidence audit.
   Leave GitHub's scheduled capture active for diagnostic/fallback use,
   with separate origin identities and **no automatic mixing or promotion**.
5. VPS-to-GitHub or other durable off-host transport is a **separate**
   security/data-trust boundary. Do not install new personal tokens,
   storage credentials or a receiver on an unconfigured host.
   Define a transport and retention policy before automating an
   externally verified VPS artifact and any second-party digest witness.
6. Stage-2 economics, research sample promotion, frozen historical
   corpus (Funding 32, Cash 66), capital/risk permissions and live
   trading remain unchanged.

## Rejected alternatives

- Relaxing UTC cutoff or labeling a missed GitHub run as historical
  opportunity data: violates time-of-knowledge boundaries.
- Keeping GitHub Actions as sole primary timer: first real cron
  attempt missed by two hours; no schedule SLO.
- Putting long-lived GitHub PAT/exchange keys in the VPS unit to
  fake GitHub-origin artifact/signatures: expands attack surface and
  falsely upgrades VPS local observations to trusted publication time.
- Automatically uploading raw market responses into a Git repo:
  violates raw dataset retention and review policy.

## Consequences and validation

A VPS timer removes dependence on GitHub runner scheduling, but
systemd and NTP do not provide hard-real-time execution or external
cryptographic source timestamps. DNS/OKX availability, VPS uptime
and clock trust remain separately assessed. Offline tests validate
timer policies, UTC gate, no retries, read-only paths, local
hashes/ZIP replay and missing/failed observation semantics.
A verified host-level installation and first successful real source
receipt are required before declaring operational success.

See [VPS operations runbook](../operations/funding-vps-systemd-capture.md)
and [prospective capture evidence contract](../research/funding-prospective-point-in-time-capture-contract.md).
