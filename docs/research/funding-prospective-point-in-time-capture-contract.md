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

## Manual-only source observation (future UTC days)

The [manual GitHub workflow](../../.github/workflows/capture-funding-preentry-source.yml) has only `workflow_dispatch` and **no** `push` or `schedule`. The operator must invoke it so Python actually starts **between UTC 00:00 and strictly before UTC 00:15**; starting late fails **before any HTTP call**. The HTTP client makes exactly two bounded, read-only, unauthenticated GETs (OKX public settled Funding history and BTC-USDT 1Dutc candles). If either response is late, missing, incomplete or stale, the job fails and saves `error.json`, never an endorsed success.

On success `raw-api-capture.json`, `http-timing.json` and `preentry-research-evidence.json` are uploaded as read-only artifacts. GitHub's first-party `actions/attest-build-provenance@v2` creates a signed claim for the **raw API capture file**, provided the repository supports it. Evidence retrieval must verify the original raw bytes, workflow repository/ref/commit, GitHub artifact attestation with `gh attestation verify`, original completed HTTP timestamps and signed/retained subject digest. A later attestation does not automatically prove a claimed earlier observation: compare independent GitHub run/log and artifact creation timestamps, detect delays, and refuse ambiguous evidence.

A GitHub schedule cannot substitute for this clock gate; GitHub documents delayed/dropped scheduled jobs. GitHub attestations also cannot establish **exchange cryptographic signatures** for rates and prices. Until a separately reviewed provenance policy is approved, neither local capture nor GitHub attestation changes `point_in_time_publication_verified=false` or authorizes research-case promotion.

## Safety and status

- The original 2026-07/08 research remains retrospective and unverified as-of-entry.
- Missing negative-Funding + low volatility is still a real coverage gap; no backfilled sample can be manufactured.
- Historical corpus remains Funding 32, Cash 66; risk/account MarginSafety and VenueExposure UNASSESSED.
- No new automatic external API polling, experimental ROI targets, capital-policy changes, sample substitutions, authenticated exchange mutations or live orders.
