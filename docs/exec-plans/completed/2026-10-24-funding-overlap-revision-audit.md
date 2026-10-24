# Funding prospective original-source cross-day revision audit

Issue: #85
Status: COMPLETED
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
- [x] Final PR-head five CI jobs + Historical Backtest Smoke success; merge and check postmerge main CI + actual GitHub-only diagnostic run; archive plan separately.

## Implementation slices

- [x] 1. Build audited-original GitHub pair comparison module and report.
- [x] 2. Add no-network tests including end-to-end original ZIP identity and fail-closed cases.
- [x] 3. Add manual GitHub-only workflow and operator documentation.
- [x] 4. Final-head verification, merge, inspect actual original results, record Issue checkpoint and archive.

## Verification matrix

| Gate | Command/evidence | Status |
| --- | --- | --- |
| Targeted | Included in CI code-level tests #40101759024 on implementation head `adfa596` | PASS |
| Static | CI #40101759024 static architecture safety | PASS |
| Code/API/E2E/plan | PR #145 final HEAD `873b6fd` CI #40101850764 five SUCCESS; postmerge main #40101910821 SUCCESS | PASS |
| Historical | Final head #40101850768 SUCCESS | PASS |
| Real source | Initial #40101911029 FAILED CLOSED on expected 0→1 confirmation progress; corrected by PR #146, real independent #40102318270 SUCCESS | PASS after fix |

## Decision gates

None for read-only consistency diagnostics. A decision about historical acquisition-grade independent publisher authentication would require a separately reviewed architecture/provenance policy. DO NOT turn a stable source comparison into an exchange signature or an approval.

## Evidence log

- 2026-10-24: PR #145 tested final head `873b6fd0d9b5873bcfdd18efa35b1e29c433b92e`, CI https://github.com/pkking/future-opportunity/actions/runs/40101850764 (5 SUCCESS), Historical https://github.com/pkking/future-opportunity/actions/runs/40101850768 (SUCCESS), squash merge SHA `58d281cc8b129e62f9e1c76e07d704a8b7470c3d`, postmerge main CI #40101910821 SUCCESS. E2E artifact ID `12562997814` / SHA256 `67be18546309b43d79ad82b40d74ba87334266ea7452dfbd987926b7755641ea`; historical ID `12562664599` / SHA256 `519b000174e370811beef14947e257b4d9f6b0dc3d23fa9bc7c4e2114bc167a5`.
- 2026-10-24: REAL original-source rollout audit https://github.com/pkking/future-opportunity/actions/runs/40101911029 reported `SOURCE_REVISION_DETECTED` and failed closed. 284 common funding settlement rates had ZERO revisions; 98 fully-confirmed spot closes had ZERO revisions. Its only conflict was first UTC-day current `1Dutc` candle normally changing 0→1 confirmation (2026-10-23T00:00Z); this was a false positive in the just-introduced classifier, NOT retroactive proof of revised settled data. Original failure artifact ID `12563356664` / SHA256 `5333178399d570d9f02d6a4fc3071974e11c901ccdda9670efa8cac4d8c1f5cb` is retained and never reclassified.
- 2026-10-24: Follow-up PR #146 corrected this in commit `eb43c13e18e3f376ee09a8b8a184c5eecdabefdc`, final-head CI #40102242986 five SUCCESS, Historical #40102242958 SUCCESS; main CI #40102318332 SUCCESS; ACTUAL original same ZIP review https://github.com/pkking/future-opportunity/actions/runs/40102318270 SUCCESS as `OVERLAP_VALUES_CONSISTENT_ONLY`: 284 funding overlap, zero rate changes; 98 previously confirmed candles, zero close changes; exactly one normal 0→1 confirmation advance, zero regressions. Artifact ID `12563576192`, SHA256 `f62a0930352a7db609599e1f818d03603baee3a3d70e4886e7173d289cae7720`. No source/corpus change or new OKX GET.

- 2026-10-24: PR #145 implementation head `adfa5962a934d21a433b30cb685e1cbe502efd20` passed all five CI jobs https://github.com/pkking/future-opportunity/actions/runs/40101759024 and Historical Backtest Smoke https://github.com/pkking/future-opportunity/actions/runs/40101759025. E2E artifact `12562624455` digest `52d5815eda73ff1d8a1c041427651ff07abc6522024beb719883ddf69262fa89`; Historical artifact `12563540128` digest `1ea001638341bca6bf0378c78b5ad3b7d4838bb514dec921f8c694d209704273`. Because this checkpoint changes head, fresh final-head CI and Historical Smoke must be verified before merge.

- 2026-10-24: Implemented original ZIP hash-gated comparison in `scripts/audit_funding_source_revision.py`, no-network MockTransport source/audit failure tests, opt-in `.github/workflows/audit-funding-original-overlap.yml`, operator runbook. Actual CI/source comparison is **not yet verified**. No GitHub Release source, original capture, corpus, trading or economics change.

- 2026-10-24: official repository `audit_github_vps_release.py` original ZIP and `check_funding_release_watch.py` independent release.published verification are available. Historical provenance issue #85 remains BLOCKED_EVIDENCE.

## Resume from here

Development slice completed, including real-source fail-closed false-positive discovery and separately proven follow-up correction PR #146. Resume the parent active Issue #85 plan, not this completed plan: seek independent source-publication evidence and collect additional prospective regimes without backfilling or promoting cases. First-day current-candle 0→1 confirmation is not a source revision.

## Completion

Final commit: `58d281cc8b129e62f9e1c76e07d704a8b7470c3d` (PR #145); corrected subsequent source-classifier commit `eb43c13e18e3f376ee09a8b8a184c5eecdabefdc` (PR #146)
CI run: #40101850764 (5 SUCCESS), Historical #40101850768 SUCCESS, postmerge #40101910821 SUCCESS; corrected recheck #40102318270 SUCCESS
E2E artifact: `12562997814`; Historical artifact: `12562664599`; corrected real-source artifact: `12563576192` (exact digests in evidence log)
Remaining unassessed items: exchange-authenticated publication/as-of timing, other regimes, statistical validity and historical acquisition eligibility.
