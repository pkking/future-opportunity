# Funding regime source-lineage research — retrospective OKX proof-of-concept

Status: **research evidence only**, not approved for historical acquisition or strategy economics gating.

## Why this exists

The approved Funding Stage-2 framework needs pre-entry market regime coverage, not a balanced sample chosen after inspecting returns. The original 2×2 research planner validates caller-supplied feature JSON but does not authenticate its funding/volatility inputs. This phase reconstructs inputs directly from archived raw official API response bodies, retaining raw source and per-row hashes for independent review.

## Fixed recent study

- Frozen research window: 2026-09-15 through 2026-09-21 (7 entry days, each at 00:15 UTC).
- Funding: OKX public `/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=400`.
- Spot: OKX public `/api/v5/market/history-candles?instId=BTC-USDT&bar=1Dutc&limit=100`.
- Last eligible settled funding record: `realizedRate`, timestamp at least 1 hour and at most 36 hours before entry. The exact last settled record may be at 16:00 UTC on the preceding day.
- Trailing volatility: population standard deviation of **seven daily log close-to-close returns** over eight confirmed, fully closed UTC daily BTC-USDT spot candles; expressed in basis points. **Not annualized**.
- Every calendar day is either a reconstructed feature row or a clearly marked missing date. No outcomes or qualification status are legal inputs.

Official OKX API docs describe approximately three months of funding history; this fixed recent study is deliberately within that scope. It does **not** establish availability of older historical funding events.

## Actual probe evidence (2026-10-08 UTC)

Initial read-only probe run `37808540222` captured 305 funding rows and 100 daily candles, but reconstructed 0/7 features because the first implementation incorrectly anchored daily candle opens at 00:15 instead of UTC 00:00. This was a local window-alignment defect, **not confirmed OKX historical source missingness**. The defect was corrected without changing the seven research dates.

Corrected run: [37808770909](https://github.com/pkking/future-opportunity/actions/runs/37808770909) — success.

- Artifact: `funding-raw-regime-source-research`; ID `11564166495`.
- Artifact digest: `sha256:41c75db5daefb07f9eea49033193f5cffb41483ccca47b34513ce62b46dcecf3`.
- Captured raw payload canonical SHA-256: `9a05ef96c8a0e780a2f8316d463612fc5b11e235958d4951b5ba85676fdbfda3`.
- Response counts: **305 funding settlement-history rows**, **100 spot daily candles**.
- Reconstructed features: **7/7** complete; 0 missing.
- Outcomes inspected or used in selection: **none**.
- This was captured retrospectively and is not independently authenticated publication-time evidence.

### Actual ex-ante event-time feature observations

| Entry date | Historical settled Funding event | Lagged realized funding rate | Trailing 7-return spot vol (bps) |
|---|---|---:|---:|
| 2026-09-15 | 2026-09-14 16:00 UTC | +0.0000462428221831 | 117.52 |
| 2026-09-16 | 2026-09-15 16:00 UTC | +0.0000825809944941 | 161.67 |
| 2026-09-17 | 2026-09-16 16:00 UTC | +0.0000399717187267 | 167.57 |
| 2026-09-18 | 2026-09-17 16:00 UTC | +0.0000888704148709 | 150.20 |
| 2026-09-19 | 2026-09-18 16:00 UTC | +0.0000898885586635 | 252.10 |
| 2026-09-20 | 2026-09-19 16:00 UTC | +0.0001 | 251.19 |
| 2026-09-21 | 2026-09-20 16:00 UTC | +0.0000785786760489 | 248.24 |

Research design uses a **predeclared** volatility threshold of 100 bps, not derived from outcomes.

| Frozen research regime | Eligible | Selected | Quota shortfall (2 each) |
|---|---:|---:|---:|
| Negative Funding, low volatility | 0 | 0 | 2 |
| Negative Funding, high volatility | 0 | 0 | 2 |
| Nonnegative Funding, low volatility | 0 | 0 | 2 |
| Nonnegative Funding, high volatility | 7 | 2 | 0 |

The deterministic research sampler selected 2026-09-16 and 2026-09-18 from the fourth cell, using seed `2026-09-funding-raw-probe-v1`. This is a **coverage shortfall**, not a failure of the research method, and must **not** cause post-hoc threshold changes or substitution of profitable dates.

## What the source hashes prove — and do not prove

1. The GitHub workflow captured responses served from the official HTTPS endpoints at the recorded capture time, and saved the raw response JSON with a canonical source SHA-256.
2. The reconstruction is deterministic from those captured bodies: each selected settlement funding event and eight spot candles have a per-record SHA-256, making an independent replay possible.
3. API results retrieved in October 2026 cannot themselves establish that those values were publicly available at each September entry instant. The 1-hour Funding event-lag and use of completed spot candles are **conservative event-time controls**, not cryptographic proof of actual dissemination time.
4. The artifact is neither exchange-signed nor independently cross-validated against immutable capture-at-time data; **`source_authentication_status=requires_independent_review`**, **`acquisition_approved=false`**, **`promotion_approved=false`**.
5. The balanced 2×2 sample is **not** a market-wide or independent representative opportunity-arrival study.

## How to reproduce

```bash
uv run python scripts/probe_funding_raw_regime_source.py \
  --start-date 2026-09-15 --end-date 2026-09-21 \
  --output-dir artifacts/funding-raw-regime-source
```

The output includes `raw-api-capture.json`, `reconstructed-features.json`, `planner-input.json` and `research-selection.json`. The scheduled-by-source-change and manually dispatchable workflow `.github/workflows/probe-funding-raw-regime-source.yml` uploads the same read-only artifacts. Capture hashes will differ if the API response changes; that is recorded, not hidden.

## Next evidence gate

- **Cash:** operator explicitly runs the separately approved Q3/Q4 2025 12-case preparations, inspects valid complete 00:15 entry/exit fixtures, then uses the existing Planner -> Promotion -> governed PR path. Do not claim 54 Cash pinned days before review/merge.
- **Funding:** repeat the frozen, outcome-independent source coverage study across more *eligible recent* windows with distinct funding-sign and volatility states, preserving raw response digests and listing empty strata. Cross-check true historical point-in-time availability before any acquisition-grade provenance bridge. If negatives are absent in a window, retain quota shortfalls; do not revise the 100 bps cut based on strategy outcomes.
- **Both:** retain Stage-2 decision-quality approvals, historical `provenance_and_semantics` and disabled economics gates.
