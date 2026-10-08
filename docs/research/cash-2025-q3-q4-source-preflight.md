# Cash 2025 Q3/Q4 source-capacity and paired-exit preflight

Status: read-only source evidence, **not** acquisition readiness or an economic backtest.

## Objective and frozen reference points

Prior source run 37753604956 / artifact 11538678600 proved exact canonical FUTURES BTC-USDT chain members on four fixed 2025 entry dates: 2025-09-12, 2025-09-19 (quarterly future `BTC-USDT-250926`) and 2025-12-12, 2025-12-19 (quarterly future `BTC-USDT-251226`). The source evidence is separate from 2026's already pinned historical cash corpus.

This follow-up verifies availability dimensions that were **not** validated by the initial four identity probes:

| Study component | Scope | Proof level |
|---|---|---|
| 2025 Q3 FUTURES catalog | Daily unique module-4 BTC-USDT chain archive, 2025-07-01..2025-09-25 | Metadata date capacity only |
| 2025 Q4 FUTURES catalog | Daily unique module-4 BTC-USDT chain archive, 2025-09-27..2025-12-25 | Metadata date capacity only |
| SPOT entry | `BTC-USDT` on all four originally fixed entry dates | Exact unique daily catalog source only |
| SPOT exit | `BTC-USDT` on 2025-09-25 and 2025-12-25 | Exact unique daily catalog source only |
| FUTURES exit | Chain archive on 2025-09-25 contains `BTC-USDT-250926`; archive on 2025-12-25 contains `BTC-USDT-251226` | Exact L2 `.data` member identity and SHA-256 |

The quarterly exit timestamp convention, from the existing approved policy, is **00:15 UTC on the previous calendar day** before actual expiry. These probes verify catalog and member identity, **not** the existence of suitable 00:15 bid/ask snapshots or the economics of an actual close.

## Replay

The workflow `.github/workflows/probe-cash-2025-quarter-capacity.yml` runs on code change and supports explicit manual dispatch. It calls the existing historical catalog scanner for the exact six-month range, then the read-only paired-source verifier:

```bash
uv run python scripts/plan_okx_cash_stage2_capacity.py \
  --scan-start 2025-07-01 \
  --scan-end 2025-12-25 \
  --output artifacts/cash-2025-quarter/capacity.json

uv run python scripts/probe_cash_2025_quarter_capacity.py \
  --capacity-report artifacts/cash-2025-quarter/capacity.json \
  --output artifacts/cash-2025-quarter/readiness.json
```

Source statuses are explicit: `unique_catalog_source`, `unavailable`, `error` for SPOT; `identity_verified`, `unavailable`, `error` for FUTURES exit. Daily FUTURES source capacities are `1` unique, `0` missing, `>1` ambiguous or `null` error. Missingness and ambiguity are never imputed as zero-opportunity periods.

The final report always keeps `acquisition_ready=false` and `entry_exit_orderbook_snapshots_verified=false`; a green probe run indicates **the evidence collection workflow completed**, not that every data source was available.

## Next gate (not performed here)

1. Verify actual 00:15 entry/exit SPOT and FUTURES order-book snapshots from these archives and every selected future-market date.
2. Establish source identity, contract-metadata consistency and observation-time completeness independently of outcomes.
3. Pre-register new Q3 and Q4 **market-day selections** without seeing their economics; record all candidates/eligible/missing and no replacement after profitability checks.
4. Prepare each sample as compact artifacts and actuals, run offline semantic acceptance, then use the same explicit promotion Planner -> wave -> PR -> CI/Smoke governance as the previous Cash 5→30 expansion.
5. Recalculate qualification/conditional realized-return distributions per maturity cohort, keeping existing Stage-2 economics gate disabled.

The current Cash 30 and Funding 32 pinned cases are untouched by these read-only probes.
