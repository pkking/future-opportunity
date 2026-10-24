# Funding prospective original-source cross-day revision audit

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Determine whether successive, already independently audited immutable GitHub prospective Funding Release originals show consistent *overlapping* OKX returned settled funding rates and completed spot candle close values. A difference in a previously returned field is a **source-revision diagnostic**, not proof about first exchange publication time. Create a reproducible, source-hash-traceable, GitHub-only offline comparison and real two-day diagnostic.

## Scope and non-goals

- Compare only two **consecutive** fully closed UTC dates in a single independent pair. Do not extrapolate to market-wide behavior, opportunity rates, or profitability.
- Every original must first pass the existing strict `check_day`/Release original ZIP replay and exact matching independently successful `release.published` audit (retained as existing upstream contract).
- Download a second copy of the identical **original ZIP** exclusively from the known immutable GitHub Release URL; enforce the independent audit's SHA-256 digest and bounded exact ZIP schema before deriving comparable raw records.
- Compare exact settled funding `fundingTime` and numeric `realizedRate`, and spot `1Dutc` completed candle open timestamp/close and confirmation status. Emit overlapping counts, revisions, and missing keys distinctly; do not classify snapshots with no common funding or confirmed candles as stable.
- No OKX/API market GETs, no new VPS or GitHub secret, no source storage change, no collection/retry/backfill, no corpus promotion, no trading, no numerical economics gate, and no new recurring workflow. The original `funding-vps-*` immutable Releases remain untouched.

## Current baseline

- main SHA `28ab63bb688794ff77fd4f62ae58e62dc20a2a8c`; no open PRs at start.
- PRs #141–#144 established GitHub custody-only 2x2 inventory and bounded 90-day original/independent-audit ledger, archived after final-head CI/Smoke.
- Production 2026-10-23 and 2026-10-24 Releases were immutable and timely; independent `release.published` audits #39875400476 and #40042736659 and longitudinal live diagnostic #40099438927 succeeded.
- Those two dates both fall in nonnegative/high spot volatility; missing negative/low; historical pinned Funding 32 and Cash 66 remain unchanged.
- The frozen point-in-time source publishing status is still `false` even when immutable GitHub custody has succeeded.

## Acceptance criteria

- [x] Validate consecutive complete UTC days, within rollout, before any GET.
- [x] Both days use existing GitHub Release + independent signed-audit health, strict replay, exact original ZIP digest as independently recorded; reject stale/partial/modified ZIP and malformed source.
- [x] Reuse the existing typed OKX source index validators to classify common funding events and fully confirmed UTC daily spot candles; preserve unique missing/new key counts without calling them revisions.
- [x] Report exact semantic changes in overlapping settled funding rates and confirmed spot closes using `Decimal`, not float; include sorted event keys and source archive hashes.
- [x] Fail closed on actual changed overlapping values or insufficient overlap; never assert exchange-signed publication, acquisition, promotion, profit or trading.
- [x] Deterministic no-network regression covers stable pair, funding revision, candle revision, no overlap, SHA mismatch, missing independent audit and invalid dates; confirm requests remain GitHub-only GET.
- [x] Add a manually dispatchable and one-time main-push-only read-only GitHub diagnostic for actual 2026-10-23/24 evidence; no cron.
- [ ] Final PR-head five CI jobs + Historical Backtest Smoke success; merge and check postmerge main CI + actual GitHub-only diagnostic run; archive plan separately.

## Implementation slices

- [x] 1. Build audited-original GitHub pair comparison module and report.
- [x] 2. Add no-network tests including end-to-end original ZIP identity and fail-closed cases.
- [x] 3. Add manual GitHub-only workflow and operator documentation.
- [ ] 4. Final-head verification, merge, inspect actual original results, record Issue checkpoint and archive.

## Verification matrix

| Gate | Command/evidence | Status |
| --- | --- | --- |
| Targeted | Included in CI code-level tests #40101759024 on implementation head `adfa596` | PASS |
| Static | CI #40101759024 static architecture safety | PASS |
| Code/API/E2E/plan | CI #40101759024 five SUCCESS, implementation head `adfa596`; retest after this evidence-only commit | VERIFYING |
| Historical | #40101759025 SUCCESS on implementation head; retest after this evidence-only commit | VERIFYING |
| Real source | GitHub-only read-only one-time rollout review, actual original Releases | pending |

## Decision gates

None for read-only consistency diagnostics. A decision about historical acquisition-grade independent publisher authentication would require a separately reviewed architecture/provenance policy. DO NOT turn a stable source comparison into an exchange signature or an approval.

## Evidence log

- 2026-10-24: PR #145 implementation head `adfa5962a934d21a433b30cb685e1cbe502efd20` passed all five CI jobs https://github.com/pkking/future-opportunity/actions/runs/40101759024 and Historical Backtest Smoke https://github.com/pkking/future-opportunity/actions/runs/40101759025. E2E artifact `12562624455` digest `52d5815eda73ff1d8a1c041427651ff07abc6522024beb719883ddf69262fa89`; Historical artifact `12563540128` digest `1ea001638341bca6bf0378c78b5ad3b7d4838bb514dec921f8c694d209704273`. Because this checkpoint changes head, fresh final-head CI and Historical Smoke must be verified before merge.

- 2026-10-24: Implemented original ZIP hash-gated comparison in `scripts/audit_funding_source_revision.py`, no-network MockTransport source/audit failure tests, opt-in `.github/workflows/audit-funding-original-overlap.yml`, operator runbook. Actual CI/source comparison is **not yet verified**. No GitHub Release source, original capture, corpus, trading or economics change.

- 2026-10-24: official repository `audit_github_vps_release.py` original ZIP and `check_funding_release_watch.py` independent release.published verification are available. Historical provenance issue #85 remains BLOCKED_EVIDENCE.

## Resume from here

Confirm the new evidence-only checkpoint final PR #145 head passes all five CI and Historical Smoke, then squash merge with expected SHA. Inspect main CI and the actual GitHub-only 2026-10-23/24 original-source overlap workflow, write real output in Issue #85, then archive completed subplan in a separate checked PR. No source or corpus modifications.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: exchange-authenticated publication/as-of timing, other regimes, statistical validity and historical acquisition eligibility.
