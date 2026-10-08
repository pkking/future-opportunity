# Stage-2 evidence expansion: independent Cash expiries and lagged Funding regimes

Status: research infrastructure; no new pinned historical cases and no numerical economics-gate approval.

## Why this change

The accepted decision-quality baseline is Funding 32 pinned days (0 qualified) and Cash 30 pinned days (8 qualified, 8 complete realized-return observations). Cash cases belong to only two expiry cohorts, March and June 2026. Same-expiry cases share exit timing and overlapping holding-period risk, so the eight qualified returns do not represent eight independent investment experiments.

Counting additional calendar days without new contracts or market regimes adds weak evidence. Separate **source readiness**, **feature provenance**, **research selection**, **verified acquisition**, and **reviewed promotion**.

## P0 — Cash: find additional expiry cohorts

The official OKX canonical module-4 BTC-USDT FUTURES chain source is probed on four fixed, *non-performance-selected* dates:

| Earlier expiry cohort | Fixed probe dates | Expected historical future member |
|---|---|---|
| September 2025 | 2025-09-12, 2025-09-19 | BTC-USDT-250926 |
| December 2025 | 2025-12-12, 2025-12-19 | BTC-USDT-251226 |

These dates are **source availability diagnostics only**, NOT automatically selected strategy-evaluation dates. The report requires the exact unique member within the observed archive, a SHA-256 identity, and logs missing/error evidence explicitly. The report deliberately always sets `acquisition_ready=false` even if all four archives are found.

Live results come from `.github/workflows/probe-cash-prior-expiries.yml` and its `cash-prior-expiry-source-readiness` artifact. Until that artifact is inspected, it is incorrect to claim these 2025 archives are available.

Before any new historical acquisition, separately verify:
- actual L2 SPOT/FUTURES entry and pre-expiry exit data (and any applicable settlement/contract metadata requirements);
- faithful quarter-specific contract rule, maturity/exit timing and time zone;
- whether partial/missing Q3/Q4 availability is a source truncation rather than a zero-opportunity day;
- fixed study-date selection with pre-registration provenance, without changing dates based on observed PnL;
- proper distinct expiry group count and conditional realized-return completeness.

When more expiry cohorts are demonstrably available, prioritize breadth across **independent maturity clusters**, not profitable-day selection. Continue to show between-cohort heterogeneity and within-cohort dependence.

## P1 — Funding: conditional 2×2 regime research

`src/future_opportunity/backtest/funding_regime_research.py` accepts a committed, finite, uniquely identified **pre-entry** feature snapshot from OKX BTC-USDT-SWAP with strict schema. Only two inputs classify regimes:

- funding-sign bucket: **negative** versus **nonnegative** *previously observed* 8-hour funding rate;
- 7-day trailing spot volatility: **low** if below 100 bps versus **high** if at least 100 bps.

The **100-bps cut is a versioned exploration design parameter**, not a statistical claim or a strategy acceptance threshold. It must not be moved after viewing outcomes without a new preregistration version.

Every calendar date in the declared window must have an observed feature row or be explicitly marked missing. Existing pinned dates must be listed and are excluded from new research selections. Each 2×2 cell requests a fixed count; when a cell has too few eligible observations the report emits `quota_shortfall` and `quota_fully_met=false` rather than backfilling profitable cases.

Both funding observation time and the trailing-volatility window end must be no later than the feature snapshot timestamp, which must be **strictly earlier** than entry at 00:15 UTC. The sampler rejects any surplus outcome/qualification fields, non-finite numbers, duplicate dates and changes to the versioned contract. Seeded SHA ranking makes output deterministic for the same snapshot identity.

**Source authentication remains a separate prerequisite.** This planner validates the schema and timestamps provided by its caller; it does not independently reconstruct the previous funding rate or trailing 7-day volatility from raw signed market data. An arbitrary JSON file with plausible features is *not* acquisition-grade evidence. The report therefore explicitly sets:
- `source_authentication_status=requires_independent_review`
- `acquisition_approved=false`
- `promotion_approved=false`
- `market_wide_opportunity_arrival_rate=null`

The 2×2 sample is deliberately balanced rather than representative of the market-time distribution. Interpret qualification and realized-return outcomes **conditional on observed regimes only**, with source missingness and rejected cases recorded in denominators appropriate to the study design; do not present a balanced sample rate as a market-wide opportunity rate.

## Operator commands

Run Cash source probe by dispatching `Probe Prior Cash Expiry Cohorts` (also runs on source-probe changes):

```bash
gh workflow run probe-cash-prior-expiries.yml -R pkking/future-opportunity
```

For Funding, first build, independently validate and commit an actual pre-entry features artifact under `docs/historical-acquisition-plans/`. No such authentic feature snapshot is claimed or fabricated by this PR. Once one exists:

```bash
gh workflow run plan-funding-regime-research.yml \
  -R pkking/future-opportunity \
  -f feature_evidence_path=docs/historical-acquisition-plans/VERIFIED-EVIDENCE.json
```

Or run locally:

```bash
uv run python scripts/plan_funding_regime_research.py \
  --input path/to/verified-feature-evidence.json \
  --output artifacts/funding-regime-research/report.json
```

The output is **research-only**, not a valid `HistoricalSelectionProvenance` or acquisition-wave manifest. The next implementation phase must build the raw-feature source validation/lineage bridge, check historical source completeness and seek explicit human review before acquisition. The existing sampling and promotion workflows remain unaffected.

## Next acceptance thresholds (process, not profit)

- Cash: verified official data and actual contract identity for >=1 *additional distinct expiry cohort* with complete entry/exit coverage; freeze date selection separately before any economic evaluation.
- Funding: independent raw-source reconstruction of lagged features with immutable artifact digests, stable 2×2 strata definition, and outcome-blind date selection; only then propose a provenance-compatible acquisition interface.
- Both: existing `provenance_and_semantics` stays active; economic acceptance remains `disabled`. Stage-2 decision-quality approvals under ADR-0008 and ADR-0009 remain unchanged.
