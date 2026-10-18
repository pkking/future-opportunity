# Prospective Funding point-in-time source capture contract (research only)

This is a **future-day source observation capability**, not proof for July/August 2026 retrospective records. Issue [#85](https://github.com/pkking/future-opportunity/issues/85), ADR-0008 and the signed-provenance design are unchanged.

## Critical time distinction

| Timestamp | What it can prove | What it cannot prove |
|---|---|---|
| Funding settlement `fundingTime` | Event occurred by stated exchange time | Public result disseminated at that time |
| Historical `1Dutc` candle `ts` and `confirm=1` | Candle was complete according to later response | That response was available then |
| Actual request sent/response received UTC | Local runner saw public HTTPS response before 00:15, **if clock trustworthy** | Exchange signature, trusted independent publication |
| GitHub artifact attestation | After external verification, workflow origin and exact raw subject digest | Exchange publishing time; exchange integrity or profitable opportunity |
| GitHub Actions `schedule` | Attempts at best-effort scheduling | That a job started before the required time |

Official references: [OKX v5 API docs](https://app.okx.com/docs-v5/en), [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations), [GitHub schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Existing machinery reused

`validate_preentry_source` invokes the existing `reconstruct_funding_regime_features` (event-time anti-lookahead, prior funding settlement 1–36h, eight confirmed daily spot candles, seven Decimal log returns and row/source SHA256) and the already accepted regime planner with the **unchanged 100bps** threshold. It also requires both HTTP calls to start after 00:00 UTC and complete before the *same* day's 00:15 UTC entry. The output records `local_capture_not_independently_attested`, `point_in_time_publication_verified=false`, and explicitly disables historical acquisition/promotion.

## Manual diagnostic source observation (future UTC days)

The [manual GitHub workflow](../../.github/workflows/capture-funding-preentry-source.yml) has only `workflow_dispatch` and **no** `push` or `schedule`. The operator must invoke it so Python actually starts **between UTC 00:00 and strictly before UTC 00:15**; starting late fails **before any HTTP call**. The HTTP client makes exactly two bounded, read-only, unauthenticated GETs (OKX public settled Funding history and BTC-USDT 1Dutc candles). If either response is late, missing, incomplete or stale, the job fails and saves `error.json`, never an endorsed success.

On success `raw-api-capture.json`, `http-timing.json` and `preentry-research-evidence.json` are uploaded as read-only artifacts. GitHub's first-party `actions/attest-build-provenance@v2` creates a signed claim for the **raw API capture file**, provided the repository supports it. Evidence retrieval must verify the original raw bytes, workflow repository/ref/commit, GitHub artifact attestation with `gh attestation verify`, original completed HTTP timestamps and signed/retained subject digest. A later attestation does not automatically prove a claimed earlier observation: compare independent GitHub run/log and artifact creation timestamps, detect delays, and refuse ambiguous evidence.

A GitHub schedule cannot substitute for this clock gate; GitHub documents delayed/dropped scheduled jobs. GitHub attestations also cannot establish **exchange cryptographic signatures** for rates and prices. Until a separately reviewed provenance policy is approved, neither local capture nor GitHub attestation changes `point_in_time_publication_verified=false` or authorizes research-case promotion.

## Safety and status

- The original 2026-07/08 research remains retrospective and unverified as-of-entry.
- Missing negative-Funding + low volatility is still a real coverage gap; no backfilled sample can be manufactured.
- Historical corpus remains Funding 32, Cash 66; risk/account MarginSafety and VenueExposure UNASSESSED.
- One approved prospective read-only scheduled observation per UTC day is allowed under Issue #85's 2026-10-18 explicit operator authorization. No other automated polling, experimental ROI targets, capital-policy changes, sample substitutions, authenticated exchange mutations or live orders.

## Offline verification of a prospective artifact (post-capture only)

The offline audit tool does **not** trigger data collection or attest to when OKX
actually published an event. Start from the **original ZIP bytes** downloaded
from a future, genuine UTC-day source workflow run, and independently obtain
the expected artifact ZIP digest from the GitHub Actions artifact metadata.
Do not substitute a repacked directory or calculate the expected digest only
from the file being inspected (that would make identity verification circular).

```bash
uv run python scripts/audit_funding_preentry_source_artifact.py \
  --zip original-prospective-funding-preentry-source.zip \
  --expected-zip-sha256 "<independently obtained original artifact digest>" \
  --entry-date "YYYY-MM-DD"
```

This fail-closed step requires exactly the three successful files, enforces
bounded archive members and UTC timing, reruns the original strict Funding
feature reconstruction, and requires exact agreement with the saved study
result. It reports three **different** digests: the original ZIP SHA-256,
the raw JSON file byte SHA-256, and the canonical source-content SHA-256.
`offline_replay_verified_only` is **not** source authentication.

As a distinct manual verification, extract the original
`raw-api-capture.json` without modifying its bytes and use the official CLI:

```bash
gh attestation verify raw-api-capture.json \
  --repo pkking/future-opportunity --format json
```

Inspect the verified provenance subject digest against the audit's
`raw_file_sha256`, and inspect its repository/workflow/ref/commit identity.
Separately compare original Actions run metadata, job/step logs, artifact
creation time and recorded HTTP request/receive time. An attestation verified
later does **not** prove that the OKX response was available before the
claimed entry, and a local clock timestamp is not a trusted timestamp.
A missing signature, mismatch or ambiguous clock/source timeline leaves
`point_in_time_publication_verified=false` and the claim **UNASSESSED**.
Never use this audit to promote a historical case, fill a frozen regime quota,
approve economics or enable live orders.

## Scheduled UTC prewarm observer (option A, approved 2026-10-18)

[Scheduled workflow](../../.github/workflows/capture-funding-preentry-scheduled.yml)
runs once per UTC calendar day on GitHub Actions, using `37 23 * * *`
(23:37 UTC the **previous** day, which is 16:37 PDT or 15:37 PST
in Los Angeles). It first checks out code and installs dependencies,
then invokes `scripts/wait_for_funding_preentry_window.py`. That
clock guard polls until 00:00 UTC and **only then** hands off to the
unchanged, strict `capture_funding_preentry_source.py` observer.

It also accepts a GitHub queue-delayed runner arriving during the *actual*
00:00..00:15 UTC window; after 00:15 UTC, or for a runner starting at another
unexpected clock time, it fails without trying the next day's window.
The exact entry cutoff is 00:15 UTC (17:15 PDT / 16:15 PST).
Original capture validation independently enforces start/end times of both
public HTTP requests strictly before that cutoff.

The schedule is **best effort, not a reliable exact-time guarantee**:
GitHub explicitly warns that queued `schedule` events can be delayed or
dropped. A missed day yields no research sample and must be reported as
missing evidence, not zero opportunity. The waiting loop has a 30-minute
finite poll cap and a 45-minute runner timeout. `concurrency` suppresses
parallel scheduled executions; an attempted re-run of a scheduled run is
skipped. The existing separate manual diagnostic workflow remains
`workflow_dispatch`-only. An artifact's unique Actions run ID prevents
confusing separate observation attempts; the system does **not** assert
exactly-once collection in the presence of external scheduler behavior.

If waiting fails, `error.json` states `UNASSESSED` and is uploaded with
`if: always()`. No successful raw file exists, so no raw-file attestation
is attempted. If source capture fails its independent cutoff/data validation,
its own failure receipt is uploaded. Only when the actual HTTP responses
and reconstruction succeed do the same three raw/time/evidence files enter
the success ZIP, with a separate GitHub attestation of the raw JSON bytes.
This is **prospective, research-only**; success does not set
`point_in_time_publication_verified=true`, does not cryptographically sign
for OKX, and cannot initiate historical promotion, quantitative economics
gating, exchange orders, or retroactive source inclusion.

Operational review: inspect
[the scheduled Actions runs](https://github.com/pkking/future-opportunity/actions/workflows/capture-funding-preentry-scheduled.yml),
ensure `event=schedule`, examine actual job/step UTC timestamps, check the
per-run artifact/attestation and perform the separately documented offline ZIP
audit. No historical day should be accepted because a cron expression exists.
In public repositories GitHub may disable scheduled Actions after 60 days
without repository activity; verify this separately when observing a long gap.

Official GitHub schedule policy:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

## Automatic scheduled-artifact review (read-only)

The scheduled workflow now includes an **audit job**, running on a separate
Runner after the capture job, including when capture fails. It reuses
`scripts/audit_funding_preentry_source_artifact.py` and runs
`scripts/audit_scheduled_funding_capture.py`:

1. Download the original ZIP **without decompression** using the first-party
   `actions/download-artifact@v8`, with artifact digest verification enabled.
   Independently obtain the originating Actions workflow-run JSON and artifact
   inventory with read-only `gh api`. Match exact run ID, head commit, branch,
   schedule event, workflow path, attempt number and one artifact ID/digest.
2. If capture **failed**, require the ZIP to contain only an explicit
   `error.json` declaring `UNASSESSED`; do not run any signature check or
   infer that the opportunity frequency was zero.
3. If capture **succeeded**, validate exact three-file ZIP identity and
   replay the preentry Funding features and original HTTP timestamps using the
   existing offline auditor. Then invoke the **official** GitHub CLI
   `gh attestation verify` on the original raw JSON **bytes**, constraining
   repository, signer-workflow file, `refs/heads/main`, commit SHA and SHA-256
   subject identity. This proves the indicated GitHub provenance only, not
   exchange publication time.
4. Preserve the structured result as
   `scheduled-funding-evidence-review/scheduled-evidence-review.json`.
   On verification/setup/download failure upload an explicit
   `scheduled-funding-evidence-review/error.json` with
   `status=UNASSESSED`. Reports never contain exchange credentials.

The success status is specifically
`offline_replay_and_github_provenance_verified_only`, **not**
`point_in_time_publication_verified`. A later signed GitHub workflow
attestation alone cannot establish OKX's historical dissemination time.
GitHub scheduled jobs can be skipped, so **absence of a workflow run is
missing evidence**, not a test failure proving a market state; an
independent cadence monitor may be proposed if missing-run alerts are needed.

Before treating any observation as research-quality historical availability,
still independently review GitHub timestamps, runner clock implications,
actual response completeness, source provenance and entry date.
This automation grants **no** historical acquisition/promotion, Stage-2
economics thresholds, or authenticated/live trading capabilities.
