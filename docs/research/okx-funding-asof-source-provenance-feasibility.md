# OKX Funding as-of-publication provenance: official contract and witness feasibility

Status: **RESEARCH / PROPOSAL ONLY — NOT APPROVED FOR SOURCE ADMISSION**  
Review date: 2026-10-24 UTC  
Tracking: [Issue #85](https://github.com/pkking/future-opportunity/issues/85)  
Existing policies: [ADR-0008](../adr/0008-funding-stage2-historical-distribution-gate.md), [V0 baseline](../design-baseline-v0.1.md).

## Current chosen direction — latest correction, 2026-10-25

**Option A is selected.** The user explicitly corrected their previous
statement on 2026-10-25: **"说错了 仍然用 方案 A"** ("I misspoke;
continue with Option A"). This **supersedes** the earlier same-day
"B preferred / A rejected" direction in the historical section below.

Continue the existing, prospectively timed **VPS → immutable GitHub
Release → independent `release.published` audit → GitHub-only
source custody and adjacent-day continuity review**. Prefer incremental
hardening of this path and accumulation of *real*, independently audited
prospective Funding source dates/regimes. **Do not initiate, schedule,
provision or prioritize the Option B observer** without a separate
future request. The B offline-only proof-of-concept and design remain
as archival research, not the chosen implementation direction.

Choosing A does not by itself prove an OKX exchange-signature or the
exchange's independently attested *first publication time*.
Keep `exchange_signed=false`,
`point_in_time_publication_verified=false`,
`acquisition_approved=false` and `promotion_approved=false`;
no historical sample promotion, numerical Stage-2 gate or trading.

## Historical direction update (superseded) — 2026-10-25

The user **initially said they rejected Option A as the preferred forward solution**, but subsequently corrected this and explicitly chose A again for the
independent-as-of-publication proof gap. The earlier "A now" priority below
is retained only as a historical snapshot of the 2026-10-24 assessment and
was **temporarily superseded** for engineering planning by **Option B**, itself superseded by the current Option A direction above
independent observer design and offline validation
([draft design](../design/funding-independent-witness-r2.md)).
This preference does **not** approve a deployed observer, new trust/storage
provider, acquisition-grade R2 evidence or historical sample promotion;
those still require a separate reviewed ADR. Existing R1 collector/Release
audit may operate without being promoted as the answer to the missing
independent-source question.

## Conclusion

The repository can already verify that an exact VPS-origin raw OKX API response
was **placed in an immutable GitHub Release before that day's 00:15 UTC entry**
and was later replayed and checked by an independent `release.published`
auditor. It can also compare the numeric stability of successive immutable
source snapshots. This establishes strong **GitHub source custody**, but it
**cannot independently establish when the upstream OKX venue first offered
those exact data to the public**, that OKX signed the response, or that a
2026-07/08 historical response was available at each earlier entry.

No official response-body signature or independently verifiable
first-dissemination timestamp was identified in the specific public API
response contracts reviewed below. **This is not a claim that OKX has no
other authentication product, archive or legal attestation.** A positive
venue-origin assertion requires a direct, documented, independently verified
mechanism. Do not improvise one from client-side request HMAC, HTTPS, `fundingTime`,
GitHub provenance or the local VPS clock.

**Decision consequence:** continue GitHub-only prospective source collection
and independent custody/continuity checks for operations; leave
`point_in_time_publication_verified=false`, `exchange_signed=false`,
`acquisition_approved=false` and `promotion_approved=false`. Changing
source-admission policy or adding a new independent acquisition/witness
service is a separate architectural/evidence governance decision.

## Official contracts and what each field proves

Sources reviewed October 24, 2026:

1. [Official OKX V5 API guide — Public Data / Get funding rate history](https://www.okx.com/docs-v5/en/), endpoint `GET /api/v5/public/funding-rate-history`.
   The guide describes historical funding data for a recent period of up
   to three months, with `fundingTime`, `fundingRate`,
   `realizedRate`, `instId`, `instType` and optional paging fields.
   `fundingTime` is the **funding settlement event time**, not an
   independently signed timestamp when that record or response was first
   externally published. `realizedRate` is a settled economic input,
   not an attached venue-generated content signature.
2. [Official OKX V5 API guide — Market Data / Candlesticks history](https://www.okx.com/docs-v5/en/),
   endpoint `GET /api/v5/market/history-candles`. The `1Dutc`
   candle's `ts` is the *opening time*, and `confirm=0` denotes a
   still-uncompleted candle while `confirm=1` denotes a completed
   candle. Therefore a candle opened on a source snapshot's current UTC
   day can normally progress 0→1 next day. A previous-day candle
   appearing unconfirmed at the earlier pre-entry snapshot is a separate
   source-completeness anomaly, not automatically the same benign case.
3. [Official OKX V5 API guide — Market Data overview](https://www.okx.com/docs-v5/en/):
   the guide explicitly warns that the multiple serving services have
   **independent caches**, and a subsequent request may return **older
   data** than a previous request. This warning concerns Market Data;
   do **not** casually generalize its exact cache topology to the
   distinct Public Data funding endpoint. Cache non-monotonicity
   strengthens the case for retaining the exact original HTTP bytes and
   request time, not treating a pair of queries or newest timestamp as
   a unique first publication witness.
4. [Official OKX V5 API guide — REST request authentication](https://www.okx.com/docs-v5/en/):
   `OK-ACCESS-SIGN` is an HMAC over client request components for
   **private authenticated requests**. It authenticates the *client's
   request*, not an independently verifiable exchange signature over
   the body of a public funding/candle **response**.

None of those fields alone is a venue-signed publication receipt. A TLS
session authenticates the endpoint for the observing client, but cannot
turn a later saved body into a third-party-verifiable venue-signed raw
response with historical creation time.

## Evidence-level boundaries — keep them distinct

| Level | Proven by | Not proven / permissible interpretation |
| --- | --- | --- |
| R0: retrospective event-time replay | Re-fetched public OKX historical rows, original body and deterministic hashes; reconstructed entry features exclude later event times | Does not prove records or their then-existing values were available when historical entry occurred; **research only** |
| R1: timely GitHub custody of VPS response | Original immutable Release server `published_at` before entry, exact raw ZIP digest, successful separate `release.published` audit, original-replay and continuity results | Verifies **what VPS supplied to GitHub** before entry. Does not authenticate OKX as origin or first publisher; no automatic historical admission |
| R2: independently observed pre-entry public response (**candidate design, not deployed**) | Separate independent trust-domain observer actively reads specified official public OKX endpoints, retains exact response bytes/time and provenance with integrity-protected before-entry third-party receipt; matches relevant features | Adds evidence of a contemporaneous independent view, **not** a signed exchange publication time; value disagreement, cache drift or missing witness remains UNASSESSED |
| R3: venue-authenticated first-publication evidence (**unidentified / not available from reviewed endpoints**) | Explicit documented OKX attestation/signature or independent authoritative publication feed with immutable time and verifiable identity | Only this could directly underpin a venue-signed/source-publisher assertion. Do not assert `exchange_signed=true` until such an instrument is actually identified and cryptographically verified |

**R2 is NOT silently sufficient for historical source admission.**
A separately approved policy must specify accepted independent witness
identity/trust, timeliness, exact comparison semantics, clock and
integrity controls, rejection behavior and whether R2 satisfies the
business's as-of criterion. For now, even a future R2 trial would
remain independent-observation research with `acquisition_approved=false`.

## Candidate paths: technical effectiveness versus operations

| Option | What improves | Limits and failure modes | Cost / decision gate |
| --- | --- | --- | --- |
| A. Continue current VPS→immutable GitHub Release + independent GitHub audits | Directly increases prospective **R1** date/regime inventory and catches accidental source revisions; already operational in two real days | Same VPS-controlled upstream request; GitHub only knows saved bytes and time. Never recovers historical first-publication time or new negative/low regime by decree | **Lowest incremental maintenance; already approved.** Continue without changing economic/sample policy |
| B. Independently operated pre-entry public OKX witness (separate credentialless observer, separate source acquisition and integrity-protected receipt) | May add **R2** corroboration of data observed from a distinct network and process *before the same entry*, with full original bytes and recorded request/response timings | Needs reliable timing before 00:15 UTC, observer independence, trust/clock model, liveness, source-field equality, cache non-monotonicity policy and disagreement handling; cannot guarantee exchange signed a value. GitHub cron is best-effort, therefore not a guaranteed pre-entry witness | **Medium/high ops complexity; requires ADR/human approval for new source/storage/trust boundary before deployment or promotion** |
| C. Independent, existing trustworthy contemporaneous third-party market archive or data feed | Could corroborate historical publication/observability without operating another collector; provenance of older entries might be available | Must demonstrate genuinely earlier immutable archive timestamps, covered instruments/fields and exact source semantics; third-party data may be transformed, delayed, corrected or unverifiable. No concrete qualifying archive verified in this review | **Provider/dataset due diligence, pricing, licensing and provenance policy decision. No third-party archive accepted yet** |
| D. OKX-origin signed/publication evidence via official channel | If documented and verifiable, the strongest native R3 identity/time proof | **No verified public response signature/publication-attestation mechanism from the examined official public endpoints**. Ask OKX support or inspect future official offerings, do not invent a signature | May require provider relationship; new historical evidence policy/verification implementation still separately reviewed |

Priority based on current constraints: **A now**, parallel low-cost technical
discovery of C and D, **B only as a pre-registered proposed experiment**.
Do not install infrastructure, a new schedule or outbound collector as a
by-product of this report.

## Proposed R2 observation contract — not implemented or accepted

If a future decision authorizes an independent contemporaneous witness,
its draft receipt should, at minimum, bind:

- Exact UTC `entry_market_date`, expected `entry_at`, instrument and
  complete public endpoint URI/query semantics for the Funding settlement
  and `1Dutc` spot candles; no ambiguity with projected `fundingRate`.
- Unique independent observer identity, declared trust owner, clock
  synchronization/uncertainty and network context distinct from the VPS;
  raw request-start, response-complete, and witness-upload/receipt
  timestamps. All must be demonstrably **before** entry. A response
  after entry cannot be retroactively trusted.
- Canonical raw response byte SHA-256 **and preservation of unmodified
  raw JSON**; exact asset origin/digest, third-party immutable custody
  witness and an authenticity/integrity mechanism independent of the
  original VPS. Merely adding `observed_at` to VPS JSON is not independence.
- Source validation using existing `_funding_index`, `_spot_index`,
  `validate_preentry_source` and regime rules; exact common
  settlement/candle identities, before-entry 8 completed daily
  candles, no future observed events, no post-entry lookahead.
- In case of divergent cached responses, missing records,
  inconsistent `confirm`, HTTP delay, missing attestation, excessive
  clock uncertainty or interrupted publish: preserve **both original
  responses**, classify R2 corroboration `UNASSESSED` and do not insert
  zero returns or backfill from a later call. Pre-register the
  threshold/equality policy *before* seeing market outcomes.
- A separate approval of whether/how an R2 witness could satisfy a
  historical admission standard. R2 receipt verification must **not**
  itself set `exchange_signed`, `point_in_time_publication_verified`,
  `acquisition_approved` or `promotion_approved` true by default.

Suggested offline-first acceptance tests *if* an R2 design is approved:
same-source independent pre-entry equality, later-than-entry witness,
same-VPS self-witness (reject independence), missing original body,
divergent cache response, untrusted observer/clock, corrupted digest,
missing/discontinuous dates, current-vs-historic `confirm` transitions,
and no credentials/order endpoints. Operational liveness/latency tests
would be **diagnostic only**, not the sole CI business gate.

## Next checkpoints and explicit decision boundary

**Autonomous work not needing a new policy decision:** continue verifying
new genuine prospective `funding-vps-YYYY-MM-DD` immutable Releases,
their successful independent `release.published` audits and the
source-continuity/regime reports; retain missing days and missing
negative Funding/low-volatility cases explicitly. Inspect publicly
available official documentation or third-party existing archives for
*concrete, verifiable* as-of publication receipts and record evidence.

**Human decision is required before:** changing what qualifies as a
historical as-of source; installing a new independent collector/service,
third-party storage or credential/trust model; using a provider feed with
licensing implications; enabling Stage-2 numerical economics gating;
or authenticated exchange trading. Do **not** infer any of these choices
from this note.

Historical Funding pinned **32 / preferred 90** (58 short) and Cash
pinned **66** remain unchanged, no R2/R3 witnessed observations have been
verified, and Issue #85 remains `BLOCKED_EVIDENCE` pending actual new
evidence, not additional diagnostic feature fields.
