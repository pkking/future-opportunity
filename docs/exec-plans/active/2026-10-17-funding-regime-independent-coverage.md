# Funding Carry point-in-time regime expansion

Issue: #85
Status: IMPLEMENTING
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
- [x] Record an exact successful operator/source-probe Run ID
      and inspect its evidence before any future pre-registration
      acquisition proposal. Absent a run or adequate source: keep
      blocker explicit, do not invent data.

## Implementation slices
- [x] 1. Freeze window design before observation. Start with
      at least two separate pre-specified 7-day windows within
      officially documented source retention, plus the existing
      Sep 15–21 comparator; verify no interaction with strategy PnL.
- [x] 2. Build source-only report, deterministic aggregation and
      negative/empty-source tests.
- [x] 3. Extend workflow safely for explicit dispatch inputs,
      bounded fan-out or one window per dispatch; no permissions
      beyond `contents: read`.
- [x] 4. CI validation and independent official-source probe
      evidence review, then decide if any regime-balanced
      acquisition is actually feasible.

## Verification matrix
| Gate | Expected evidence | Status |
|---|---|---|
| Offline unit | Source/retention/2x2/anti-lookahead tests | Pending |
| Source run | 39028716478, 3/3 jobs; 3 ZIP SHA-256 match | VERIFIED, retrospective publication remains unassessed |
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

## 2026-10-17 real three-window operator-free read-only source evidence

[Source research run 39028716478](https://github.com/pkking/future-opportunity/actions/runs/39028716478)
completed SUCCESS for every **pre-registered** window on source
implementation commit `1f1e55ef74c58f453bc75afd096cd65a5329c5ad`.
Three exact GitHub Actions ZIPs were downloaded and SHA-256 verified,
and their coverage summaries independently inspected:

| Window | Artifact ID | ZIP SHA-256 | Valid days | Negative low | Negative high | Nonnegative low | Nonnegative high |
|---|---:|---|---:|---:|---:|---:|---:|
| Sep 01–07 | 12098539844 | abb40c18c6dafa46788fa8885c7eab9acb6843f79e09f2f747309c6434d83d64 | 7 | 0 | 1 | 0 | 3 |
| Sep 15–21 | 12098994902 | c21e8dd95cb370158bf1d586915aebb13a49fd27c6556809aee190b1fdc3b941 | 7 | 0 | 0 | 0 | 7 |
| Oct 01–07 | 12099183403 | 8d55695814c9842255db1c7964465396caaf2b374a5739827fbc53732b05a9fe | 7 | 0 | 0 | 6 | 1 |

Total **21 independently preselected dates, 21 reconstructed
pre-entry feature rows**, no missing source/candle dates within the
selected windows; population covers only **3/4** frozen
2×2 strata, *negative + low volatility remains empty*. The
strict research planner's per-stratum quota remains unfilled.
Across the windows the sampled buckets include 1 negative/high,
6 nonnegative/low and 11 nonnegative/high; selected dates
per-stratum are quota-limited, so do not conflate these
population counts with the selected list.

All three reports state `point_in_time_publication_verified=false`,
`source_authentication_status=requires_independent_review`,
`quota_fully_met=false`, `acquisition_approved=false`,
`promotion_approved=false`. This is retrospective official
API source reconstruction, **not** proof records were published as-of
entry, not a 90-day sample, not sufficient 2×2 coverage, and
not a market-wide market-state distribution.

## 2026-10-18 next independent research slice — July/August pre-registration

Decision context: The [read-only three-window run 39028716478](https://github.com/pkking/future-opportunity/actions/runs/39028716478) covered **21/21** eligible Sept/Oct entry days but only **3/4** frozen sign x 100bps volatility strata. In particular negative-Funding/low-volatility has zero observed dates. This is a coverage limit, not permission to mine past returns or adjust threshold. All features were retrospectively retrieved; publication as-of-entry remains **UNASSESSED**.

Objective: freeze **three further calendar-picked seven-day July/August 2026 windows** as a separate new immutable research-only registry *before* any public API fetch. Choose dates by fixed two-week spacing and conservative rolling 100-candle/400-funding-record API capacity, not observed funding sign, spreads, returns or qualification.

Frozen new windows (inclusive, all entry 00:15 UTC):
- `2026-07-27-to-08-02`, seed `funding-2026-07-27to08-02-v1`.
- `2026-08-10-to-16`, seed `funding-2026-08-10to16-v1`.
- `2026-08-24-to-30`, seed `funding-2026-08-24to30-v1`.

Constraints: all 21 dates are distinct from the existing 21 Sept/Oct dates; fixed 100 bps threshold and requested 2 cases per regime; point-in-time publication not implied by historical event timestamps. API retention and availability are *hypotheses*, not sourced facts; record missing/truncated days without substitution. Preserve original registry and its exact three windows unchanged. No change to Funding 32/Cash 66 corpus, approved Stage-2 reporting posture, risk or live-trading boundary.

Implementation plan:
- [ ] Add second frozen `docs/historical-acquisition-plans/funding-2026-jul-aug-regime-source-windows-v1.json` registry, preserving original preregistration untouched.
- [ ] Teach `registered_research_window` to recognize exactly the two immutable registries with strict outcome-blind/governance and unique nonoverlapping IDs/days.
- [ ] Add a **manually dispatched only** new read-only source workflow for exactly the three July/August windows; remove the old source workflow's surprise `push` trigger. No automatic source reads by ordinary code merges.
- [ ] Add regression tests for both fixed manifests, duplicate/overlapping windows, altered source authorization, stale dates, and no automatic source-trigger or archive/promotion write calls.
- [ ] Verify final PR-head static/code/API/E2E/Agent Plan and Historical Smoke; report new actual-source evidence as UNASSESSED until a **separately manually triggered** run has completed and exact ZIPs/digests have been independently audited.

Verification evidence: CI-run URLs and GitHub Actions source artifact IDs+SHA, source statuses and missing dates where available. No source API run is authorized by the PR alone.

## Resume from here

Create the July/August frozen registry and manual-only workflow, generalize the source-window resolver without rewriting the original three-window manifest, add strict offline regressions, then run full final-head CI and Historical Smoke. **Do not** treat the new 21 date hypotheses as observed market states until an independently completed source run is inspected. After reviewed merge, any historical public-source dispatch needs an explicit new operator action; the GitHub connector lacks workflow_dispatch. The missing negative/low Funding stratum and publication-time authentication remain open research.

## Completion

In progress. PR-head CI, historical source reports, publication-as-of evidence, and source validity for July/August remain UNASSESSED. Strategy corpus and economic thresholds remain unchanged.
