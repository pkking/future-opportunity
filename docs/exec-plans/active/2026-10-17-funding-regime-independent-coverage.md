# Funding Carry point-in-time regime expansion

Issue: #85
Status: VERIFYING
Owner: agent
Started: 2026-10-17

## Objective
Increase evidence diversity for Funding Carry by developing a
reproducible **pre-entry** source-coverage study across different
funding signs and trailing spot volatility regimes. Keep historical
sample selection blind to strategy returns, and distinguish a
retrospective API response from genuinely known-as-of-entry data.

## User-facing problem
The pinned Funding corpus has 32 distinct days and **zero qualified
cases** in the previously accepted analysis. A 7-day raw-source
research probe (2026-09-15..21) found the only populated bucket was
nonnegative Funding + high volatility. This insufficient variety
makes generalized opportunity claims unjustified, even though the
30-day count minimum is already met; preferred 90-day count remains
58 days away.

## Existing assets and verified baseline
- [ADR-0008](../../adr/0008-funding-stage2-historical-distribution-gate.md):
  decision-quality observability accepted, economics gate disabled.
- [Source lineage report](../../research/funding-raw-regime-source-lineage-7-days.md):
  read-only 7-day API capture with official endpoint bodies and explicit
  caveat: historical publication timestamp unverified.
- `scripts/probe_funding_raw_regime_source.py` supports date arguments,
  but `.github/workflows/probe-funding-raw-regime-source.yml` hardcodes
  the single September 15–21 window.
- `funding_raw_feature_lineage.py`: 1..36 hour lagged settled Funding
  history and 7 closed daily spot returns; study maximum 31 days.
- `funding_regime_research.py`: fixed 100 bps volatility boundary,
  four sign/vol buckets, deterministic seed and explicit shortfalls.
- Latest validated baseline after PR #82: Funding 32, Cash 54;
  historical provenance_and_semantics remains active.

## Constraints and non-goals
- No future or post-entry event timestamp can influence features
  attributed to entry time; reject missing/duplicate/out-of-order
  source records.
- Source authenticity and published-as-of-entry status must be
  independently assessed; a query issued in October for September
  records is not proof September availability.
- Keep the exact sign and 100 bps threshold; do not tune on outcomes.
- Do not require balanced 2x2 if actual source evidence has empty
  cells. Record exclusions and shortfalls, not fabricated samples.
- No acquisition, campaign promotion, new profitability targets,
  economics approval, market-wide arrival claims or live orders.

## Acceptance criteria
- [x] Pre-register several independent study **windows and seed**
      before any new source queries; choose windows by calendar and
      stated historical API retention, never observed PnL.
- [x] Generalize read-only GitHub workflow to accept controlled
      explicit study dates or bounded matrix without losing a
      reproducible default; persist exact inputs, OKX raw response
      SHA-256, report, missing evidence and shortfall reasons.
- [ ] Test truncated API retention, source changes, missing candles,
      duplicate funding events, negative/nonnegative signs, volatility
      split, entry timestamp lookahead and fail-closed errors.
- [ ] Produce a machine-readable source-coverage report with actual
      eligible/selected/excluded/missing counts per stratum and
      `source_authentication_status`; do not treat retrospective
      evidence as acquisition-approved provenance.
- [ ] PR final head passes all static/code/API/E2E/plan checks and
      offline Historical Smoke; no corpus additions.
- [ ] Record an exact successful operator/source-probe Run ID
      and inspect its evidence before any future pre-registration
      acquisition proposal. Absent a run or adequate source: keep
      blocker explicit, do not invent data.

## Implementation slices
- [x] 1. Freeze window design before observation. Start with
      at least two separate pre-specified 7-day windows within
      officially documented source retention, plus the existing
      Sep 15–21 comparator; verify no interaction with strategy PnL.
- [ ] 2. Build source-only report, deterministic aggregation and
      negative/empty-source tests.
- [x] 3. Extend workflow safely for explicit dispatch inputs,
      bounded fan-out or one window per dispatch; no permissions
      beyond `contents: read`.
- [ ] 4. CI validation and independent official-source probe
      evidence review, then decide if any regime-balanced
      acquisition is actually feasible.

## Verification matrix
| Gate | Expected evidence | Status |
|---|---|---|
| Offline unit | Source/retention/2x2/anti-lookahead tests | Pending |
| Source run | Exact run and SHA-256, missing windows explicit | Unassessed |
| Static/code/API/E2E | Final-head CI checks | Pending |
| Agent plan | Issue #85 open, canonical active plan | Pending |
| Historical Smoke | Pinned corpus unchanged and smoke pass | Pending |

## Decision gates
No trade or strategy approval here. A later decision is needed only
if actual source-validated, point-in-time features support a new
pre-registered Funding acquisition proposal. Never automatically
promote research-only records or enable a numeric economics gate.

## 2026-10-17 pre-registered multi-window implementation

The windows were frozen in source-control **before implementation queries**:
[PR #90](https://github.com/pkking/future-opportunity/pull/90) merged
`51707ffd1eb5203269b0c2a3d082329c6b6a0236`. Registry:
`docs/historical-acquisition-plans/funding-2026-sep-oct-regime-source-windows-v1.json`
defines 2026-09-01..07, 2026-09-15..21, 2026-10-01..07,
each with immutable seed and quota 2 per frozen 2x2 stratum.

This PR constrains the probe to exact committed `window_id`, adds
positive schema/anti-overlap/future-date checks, writes a per-window
`coverage-summary.json` with source SHA-256, raw-source
publication caveat, missing dates, signed-rate 2x2 eligible and
selected counts, and adapts the read-only workflow to
three bounded, isolated jobs with `fail-fast: false`.
No acquisition or corpus mutation is introduced. Whether
the official public APIs still expose sufficient rows for each
window remains **UNASSESSED** until observing a completed source
run. Source authentication at historical publication time is
not solved by a retrospective capture.

## Resume from here
Inspect this implementation PR's exact final head, CI results and auto-triggered read-only probe run; verify actual source availability for every frozen window and report exact missing regimes.
Read `scripts/probe_funding_raw_regime_source.py`, the existing
read-only workflow, `funding_raw_feature_lineage.py`, and tests;
The three window dates/seeds are already frozen by PR #90; do not revise based on returns.
Make source-coverage changes in small PR slices and require
GitHub source evidence with full SHA-256. Do not interpret missing
negative-funding periods as a failing investment or as permission
to alter the frozen sampling design.

## Completion
Probe implementation requires final CI and independent true-source evidence. Do not move
to completed until CI and evidence are recorded.
