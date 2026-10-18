# Funding July/August 2026 — independently replayed retrospective source coverage

Status: **SOURCE-AUDITED, RESEARCH ONLY**. Issue [#85](https://github.com/pkking/future-opportunity/issues/85).

## Immutable GitHub source provenance

The operator manually dispatched the pre-registered [run 39102598192](https://github.com/pkking/future-opportunity/actions/runs/39102598192) at source commit `2228bab91ce74b83abef54ffb544286cc90f29d8` on 2026-10-18 06:02 UTC. All **three distinct matrix jobs succeeded**, publishing three original GitHub Actions ZIPs. All three ZIP byte SHA-256 digests were independently recomputed and matched GitHub's Actions artifact `digest` values. The complete frozen identity table is in [the machine-readable audit](funding-2026-julaug-source-run-audit-v1.json).

| Fixed market-date window | Artifact ID | Actions ZIP SHA256 | Reconstructed days | Already pinned | Selected unpinned days |
|---|---:|---|---:|---:|---:|
| 2026-07-27..08-02 | 12127216329 | `3363e8cb256f293d8fdebcdbda24dbcbde5e74e0fe5fe5ee0e36ef084f311a1c` | 7 | 0 | 3 |
| 2026-08-10..08-16 | 12127506247 | `2587c63913627161c0c8cc98a72410bade896a229275b1a2b9165bd670bfafca` | 7 | 0 | 2 |
| 2026-08-24..08-30 | 12127316983 | `9eec4e3804115f4edf6278a79a1121835ae1d322057aa7ae1342c1ced3620996` | 7 | 1 (Aug 29) | 3 |

The independently audited ZIPs each contain the same **five** source/reconstruction/selection JSON reports. Offline independent recomputation verified, for every candidate entry at 00:15 UTC: original OKX public `realizedRate` event, event lag 1–36h before entry, exactly eight previously closed confirmed `1Dutc` spot candles, seven Decimal daily log returns, seven-return nonannualized standard deviation in bps, canonical raw source hash and each row's source SHA, and exact outcome-blind deterministic selected dates. Every window captured 290 funding API rows and 100 daily candles. **21/21 raw feature rows** match; **0 source-missing days**. August 29 is already in the pinned research index, so **20** previously unpinned days are eligible for further *research selection*; 8 are selected across the four regime quotas. These selections are not acquisition approvals.

## Observed regime coverage (not strategy performance)

| Lagged settled Funding sign / trailing volatility | July 27–Aug 2 | Aug 10–16 | Aug 24–30 | Total **observed** dates |
|---|---:|---:|---:|---:|
| Negative / under 100 bps | 0 | 0 | 0 | **0** |
| Negative / at least 100 bps | 1 | 0 | 1 | **2** |
| Nonnegative / under 100 bps | 0 | 7 | 0 | **7** |
| Nonnegative / at least 100 bps | 6 | 0 | 6 | **12** |

Counts above refer to **all 21 observed raw feature dates**. The downstream eligible population excludes preexisting pinned August 29, reducing nonnegative/high from 12 to 11 and eligible days from 21 to 20. One day must never be quietly dropped from the raw source evidence or double-counted as a new research sample.

The two negative/high cases are **2026-08-02** and **2026-08-28**. Negative/low remains **empty**, including across earlier three Sept/Oct pre-registered windows. The fixed 100bps boundary and deterministic seeds were **not adjusted** after inspecting source market states. Quota is not met; this is an observed sampling limitation, not a strategy/economics failure or reason to fabricate candidates.

## Epistemic and safety limits

- Both July 27–Aug 2 and Aug 24–30 source captures have the same canonical raw-source SHA because the concurrent public API requests returned identical historical data bodies. These are **distinct date windows but not independent upstream data archives**; this is not concealed or counted as separate archive provenance.
- Raw API bodies were captured **2026-10-18**, **after** historical entry dates. Event timestamps and deterministic replay prove only what was *reconstructed*, not that original rates/candles were externally published by each entry instant. `point_in_time_publication_verified=false`; independently contemporaneous archival evidence is still necessary for promotion-grade as-of assertions.
- `source_authentication_status=requires_independent_review`, risk account MarginSafety / VenueExposure `UNASSESSED`. No funding return forecast, realized return distribution, opportunity-arrival probability, live profitability, account risk approval or venue risk can be claimed from this study.
- The historical corpus stays **Funding 32 / Cash 66**. `acquisition_approved=false`, `promotion_approved=false`; Stage-2 numerical economics gating remains off, and live-order execution is forbidden.

## Reproduction

Download the three **exact artifact IDs** from run 39102598192, verify their original ZIP SHA-256 against the audit JSON, then execute the versioned offline checker using the three ZIP paths. The replay script is read-only: it recomputes the expected five JSON reports from the original raw HTTP payloads using the repository's deterministic source-reconstruction/selection implementations. No API calls or source archive downloads occur during replay. Individual source archive bytes are *not* re-fetched from the exchange by this audit; this evidentiary limitation remains explicit.

Next: complete source-authentication research for genuinely published-as-of-entry records and, only if necessary, pre-register **new independent** calendar windows to investigate the missing negative/low regime. Keep empty cells, no retroactive threshold tuning and no automatic promotion.
