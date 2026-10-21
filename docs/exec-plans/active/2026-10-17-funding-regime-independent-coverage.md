# Funding Carry point-in-time regime expansion

Issue: #85
Status: BLOCKED_EVIDENCE
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
- [x] Add second frozen `docs/historical-acquisition-plans/funding-2026-jul-aug-regime-source-windows-v1.json` registry, preserving original preregistration untouched.
- [x] Teach `registered_research_window` to recognize exactly the two immutable registries with strict outcome-blind/governance and unique nonoverlapping IDs/days.
- [x] Add a **manually dispatched only** new read-only source workflow for exactly the three July/August windows; remove the old source workflow's surprise `push` trigger. No automatic source reads by ordinary code merges.
- [x] Add regression tests for both fixed manifests, duplicate/overlapping windows, altered source authorization, stale dates, and no automatic source-trigger or archive/promotion write calls.
- [x] Verify final PR-head static/code/API/E2E/Agent Plan and Historical Smoke; report new actual-source evidence as UNASSESSED until a **separately manually triggered** run has completed and exact ZIPs/digests have been independently audited.

Verification evidence: CI-run URLs and GitHub Actions source artifact IDs+SHA, source statuses and missing dates where available. No source API run is authorized by the PR alone.

## 2026-10-18 code and evidence checkpoint

- PR [#117](https://github.com/pkking/future-opportunity/pull/117) implements the independently frozen new 21-calendar-date research registry, separate exact-window/seed validation, two read-only manually dispatched workflows, and offline governance/negative tests. Original Sept/Oct frozen 21 dates unchanged.
- First implementation head `6e015c6a20a74ca862db2bb2348f1ec51d0de0af`: [CI 39096979396](https://github.com/pkking/future-opportunity/actions/runs/39096979396) SUCCESS (Static/architecture, Code tests, API, E2E, Agent plan integrity all success); [Historical Smoke 39096979309](https://github.com/pkking/future-opportunity/actions/runs/39096979309) SUCCESS.
- The current plan-only checkpoint update will itself receive a *new* final-head check before PR merge. Research source windows July/August have NOT been queried, no source-run ZIP digest exists and all 21 historical Funding sign/vol classifications remain **UNASSESSED**. Even a later retrospective capture cannot prove historical publication as-of-entry.
- Prior unexpected `push` trigger of the old Funding source workflow removed; new workflow only `workflow_dispatch`. No automatic API source read, historical acquisition, corpus mutation, economic-target activation or trading.

## 2026-10-18 merged PR and main verification

- [PR #117](https://github.com/pkking/future-opportunity/pull/117) **merged** at `97791a41155766d601548550c4938b466d93589f`. Immutable July/Aug 21-date registry, exact-window resolver, manual-only source workflows and offline negative tests are now on main.
- Final PR head `29cce44e4aa9ece7ba1aefe13ef6a870f859d8ca` validated by [CI 39097071765](https://github.com/pkking/future-opportunity/actions/runs/39097071765) with Static/Architecture, Code, API, E2E and Agent Plan Integrity **5/5 success**, and [Historical Smoke 39097071704](https://github.com/pkking/future-opportunity/actions/runs/39097071704) **success**.
- Post-merge main [CI 39097116292](https://github.com/pkking/future-opportunity/actions/runs/39097116292) **success** (static/code/API/E2E; plan integrity skipped for push by CI design).
- Confirmed new `.github/workflows/probe-funding-jul-aug-regime-source.yml` is present on main with `workflow_dispatch` only. Old Funding raw probe also has no `push` trigger. **No July/Aug source dispatch/run or source artifact exists** from this task; missing-stratum and publication-as-of-entry evidence remain unassessed.
- Corpus remains Funding 32, Cash 66, Stage-2 numerical economics gating disabled, no authenticated trading or capital-policy changes.

## 2026-10-18 source evidence audit — operator-run completed, independent review

Issue: #85 remains the canonical task. Human independently triggered **one** read-only GitHub run [39102598192](https://github.com/pkking/future-opportunity/actions/runs/39102598192) at source head `2228bab91ce74b83abef54ffb544286cc90f29d8` (workflow_dispatch, all 3 jobs SUCCESS). Code work stays strictly within the frozen preregistration, not outcome-driven sampling.

Audit acceptance:
- [x] Record exact three artifact IDs and original ZIP SHA-256; independently check all archive bytes and five JSON files per ZIP, correct window/seed/head/provenance.
- [x] Replay 21 00:15 UTC entries against raw HTTP funding and confirmed 1Dutc candle evidence; check prior-event 1..36h age, eight closed candles, seven Decimal log-returns, 100bps regime assignment and SHA-256 per row.
- [x] Independently recompute canonical raw source digest, planner input and deterministic selected dates; preserve pinned 2026-08-29 exclusion without removing its observed feature row.
- [x] Publish an immutable, machine-readable audit summary, human-readable report and offline consistency tests; never commit raw fetched archives or strategy outcomes.
- [x] Final-head CI/Agent Plan/Historical Smoke and post-merge main CI verified.
- [ ] Publication-as-of-entry independently authenticated, and four-regime quota fully met. These are **research exit gates**, not items to auto-approve from retrospective data.

Already observed external evidence (to be verified and retained in the reviewed audit PR): 21/21 reconstructable dates, one pinned (2026-08-29) excluded from **new selection**, 20 unpinned candidates. Four raw feature regime populations under frozen sign/100bps taxonomy: negative+low **0**, negative+high **2**, nonnegative+low **7**, nonnegative+high **12**. All three source ZIPs passed initial byte SHA-256 checks; the clean, independent offline replay must be recorded before completion claims. All 21 are retrospective official API responses captured 2026-10-18. Research cannot infer contemporaneous publication, ROI, qualified market opportunities or live trading readiness.

## 2026-10-18 source audit merged and evidence verified

- User-triggered [official public-source research run 39102598192](https://github.com/pkking/future-opportunity/actions/runs/39102598192), **workflow_dispatch** on `main` at `2228bab91ce74b83abef54ffb544286cc90f29d8`. All 3 jobs succeeded.
- The three exact original GitHub Actions artifact ZIPs **12127216329** (SHA `3363e8cb256f293d8fdebcdbda24dbcbde5e74e0fe5fe5ee0e36ef084f311a1c`), **12127506247** (`2587c63913627161c0c8cc98a72410bade896a229275b1a2b9165bd670bfafca`) and **12127316983** (`9eec4e3804115f4edf6278a79a1121835ae1d322057aa7ae1342c1ced3620996`) were downloaded and byte-SHA verified against GitHub's published checksums.
- Independent local replay recomputed raw canonical source SHA, each selected original funding event and eight confirmed spot daily candles, seven-return Decimal log volatility, one-hour pre-entry lag, row SHA and deterministic dates. **21/21 raw feature rows verified**, 0 source-missing; 2026-08-29 is already pinned, leaving **20 unpinned eligible**; fixed selected research population of **8** (not authorized promotion cases).
- Complete frozen audit JSON at `docs/research/funding-2026-julaug-source-run-audit-v1.json`, human explanation at `docs/research/funding-2026-julaug-source-run-audit.md`, reusable offline ZIP replayer `scripts/audit_funding_julaug_source_artifacts.py` and offline regression tests at `tests/test_funding_julaug_source_audit.py`.
- Audited **raw observed** regime counts: negative/low **0**, negative/high **2**, nonnegative/low **7**, nonnegative/high **12**. One previously pinned nonnegative/high day is excluded from prospective eligible populations, but retained in raw 21-day denominator. Never select extra dates based on strategy returns.
- [PR #119](https://github.com/pkking/future-opportunity/pull/119) merged at `369ddb04bb66b428423437544faa0f1b4adec00f`; final-head [CI 39103175660](https://github.com/pkking/future-opportunity/actions/runs/39103175660) all five required jobs SUCCESS, [Historical Smoke 39103175638](https://github.com/pkking/future-opportunity/actions/runs/39103175638) SUCCESS. Main follow-up CI [39103227714](https://github.com/pkking/future-opportunity/actions/runs/39103227714) to be independently verified at this checkpoint's close.
- Both successful selected raw API acquisitions for July 27 and Aug 24 expose identical source canonical digest `53649680be1e3a5c22acb43443eccd925d1856a6c6947c130a5fba798c5d6dd9` (response bytes reused across fixed windows); this does not establish independent archive publishers.
- **Remaining blockers**: Negative Funding below 100 bps trailing spot volatility **not observed**, plus *retrospective API query cannot prove publication as-of historical entry*. Policy `point_in_time_publication_verified=false`; source provenance therefore is not acquisition/promotion-grade evidence. MarginSafety / VenueExposure UNASSESSED. Original Funding 32 / Cash 66 pinned corpus and disabled Stage-2 economics gate unchanged.

## 2026-10-18 next implementation slice — prospective as-of source observation

This slice addresses only the **time authenticity** blocker of Issue #85. Historical July/August 2026 responses from October cannot be backdated into point-in-time evidence; the existing 21 observed dates and all source artifacts stay unchanged.

**Acceptance scope**:
- [x] Implement an independently testable single-day UTC 00:15 Funding observation gate: both public API requests must **start after UTC midnight and finish strictly before 00:15 UTC**, be tied to the identical target day, and have complete confirmed previous daily candles and a settled funding event at least 1h old. Any clock/window mismatch or missing source fails closed.
- [x] Reuse existing `reconstruct_funding_regime_features` and `plan_funding_regime_research`, preserving Decimal, original official raw source SHA, exact per-observation SHA and event-time rules. No duplicate strategy selection/threshold implementation.
- [x] Add a **manual-only**, no secret or authenticated trading `workflow_dispatch` to capture the *actual UTC day only* and upload raw evidence; add GitHub official artifact provenance attestation, **not** exchange-side signed rates. No schedule, push, automatic source fetch or historical backfill.
- [x] Distinguish `local_http_completed_before_entry` from independently GitHub Sigstore attestation-verified and exchange-published data; recorded as-of result remains **UNASSESSED** until separately signed provenance is verified. Never infer past availability from an after-the-fact run.
- [x] Negative tests for after-entry capture, before-daily-close capture, swapped API receive times, missing daily candle, stale funding, corrupted raw digests, missing row hashes, and audit/read-only workflow contracts. CI remains deterministic and offline.
- [x] Final-head static/code/API/E2E/Agent Plan/Historical Smoke and postmerge main CI recorded; no source workflow executed without human action.

**Decision constraints**: No change to Cash 66 / Funding 32 historical corpus, strategy economics, Stage-2 gate, sample selection dates, existing retrospective evidence or live trading. This is new *future-day evidence capability*, not a retrospective proof for missing negative/low Funding. GitHub cron is best effort and may be delayed; do not schedule unattended exact-time data capture here. SLSA GitHub artifact attestation proves the workflow origin only after verification, not exchange source integrity or economic qualification.

**Resume action**: implement the new narrow observer/validator, manual workflow, tests, and evidence contract documentation; run CI and leave the plan `BLOCKED_EVIDENCE` until independently captured and provenance-verified future-day inputs exist. Do not request the user to retrigger July/Aug source scans.

## 2026-10-18 prospective point-in-time observer verification checkpoint

- [PR #121](https://github.com/pkking/future-opportunity/pull/121) implements an independent, **future-day-only**, two-public-GET, manual-source-capture capability with exact UTC 00:15 boundary. `scripts/capture_funding_preentry_source.py` rejects requests started before midnight or after entry, late/malformed HTTP response, wrong entry date, stale settled Funding or unconfirmed/missing candles. The pure validator also rejects **any future-dated raw funding settlement or prematurely confirmed daily candle anywhere in the response**, even when a lagged selected row itself looks valid.
- Uses existing Funding feature reconstruction + frozen 100bps planner; preserves raw source and per-row checksums, UTC request/receive times, `UNASSESSED` failure artifacts, and `point_in_time_publication_verified=false` output. The action has `workflow_dispatch` **only**, read-only public exchange API with bounded 5s HTTP timeout, GitHub `attest-build-provenance@v2` subject-path of the raw response, and no automatic scheduling or sampling/promotion.
- [Final implementation-head CI 39112004681](https://github.com/pkking/future-opportunity/actions/runs/39112004681) verified all **five** PR jobs successful (static, code, API, E2E, agent plan) after fixing test import F821 from earlier failed runs. [Historical Smoke 39112004678](https://github.com/pkking/future-opportunity/actions/runs/39112004678) successful on the same implementation SHA `ca51b116cb93a33e305233b803bb5efa69500671`. The plan-checkpoint commit will receive another final-head CI/Smoke before merge.
- Evidence specification: [Prospective point-in-time capture contract](../../research/funding-prospective-point-in-time-capture-contract.md). GitHub Signed Artifact provenance does not certify **exchange** publication time; this code never marks as-of historically independently verified. No prospective capture has yet been dispatched. 2026-07/08 21-day retrospective evidence and still-empty negative+low regime remain unchanged.

## 2026-10-18 merged pre-entry observer CI and evidence checkpoint

- [PR #121](https://github.com/pkking/future-opportunity/pull/121) merged `ac021970f7cbaa4f1fbdcdff074a1f8dfb479668` after final-head `8596e48138150debb2582e937b66570ccc9fd77f` passed [CI 39112099810](https://github.com/pkking/future-opportunity/actions/runs/39112099810) **5/5** (static, code, API, E2E, agent-plan integrity) and [Historical Smoke 39112099737](https://github.com/pkking/future-opportunity/actions/runs/39112099737) **success**. Main [CI 39112151112](https://github.com/pkking/future-opportunity/actions/runs/39112151112), [Historical Smoke 39112151103](https://github.com/pkking/future-opportunity/actions/runs/39112151103), and [Evaluate Prepared Historical Fixture 39112151167](https://github.com/pkking/future-opportunity/actions/runs/39112151167) all **success** at the merged SHA.
- New manual workflow: [Capture Prospective Funding Pre-Entry Source](https://github.com/pkking/future-opportunity/actions/workflows/capture-funding-preentry-source.yml). It has *no* `push` or `schedule` trigger and was **not dispatched** here. A valid call must actually begin in UTC 00:00–00:15, with both official public GET results complete before UTC 00:15. Late/absent data stays UNASSESSED. First-party GitHub provenance attests the raw captured file; it never signs on behalf of OKX.
- Source-only implementation reuses existing anti-lookahead settled-funding and eight-closed-daily-candle reconstruction and 100bps research planner. Pure validator rejects raw responses with any future-dated event or prematurely confirmed daily candle. Output always has `point_in_time_publication_verified=false` and acquisition/promotion disabled until independent provenance assessment.
- Old retrospective July/August samples **cannot be upgraded** to as-of historical publication by this future observation capability. Their previously audited 21/21 feature rows, unfilled negative/low cell, and full source hashes remain unchanged. Funding 32/Cash 66 corpus, Stage-2 economic gate disabled, account MarginSafety/VenueExposure UNASSESSED, no live trading.

## 2026-10-18 offline prospective evidence audit readiness (Issue #85)

**Engineering scope, not evidence completion.** The original prospective raw capture has
not been run. A reviewer currently lacks a small repeatable offline entrypoint to
check an original downloaded Actions ZIP against an independently recorded archive
digest and re-run the exact pre-entry feature validation. This slice makes a future
capture auditable without granting any new source, acquisition or promotion rights.

Acceptance criteria:
- [x] Purely offline auditor accepts only the three original successful files,
      an independently supplied exact ZIP SHA-256 and an explicit UTC entry day;
      exact raw bytes and source-reconstruction hashes are reported separately.
- [x] Fail closed for wrong original ZIP digest, missing/extra/duplicate ZIP files,
      oversized members, incorrect day, altered timing, altered analysis, late
      source and positive acquisition/verified-publication claims.
- [x] Document **separate** GitHub/Sigstore verification and independent run-time
      review. Internal ZIP checks do NOT authenticate the exchange, runner clock
      or actual as-of dissemination; returned status remains UNASSESSED.
- [x] PR-head CI (static/code/API/E2E/plan) and Historical Smoke succeeded,
      with no scheduled calls, additional historical dates or trading permissions.

Implementation: add one standalone stdlib ZIP audit script reusing the existing
strict backtest validator, an offline test suite and a review procedure.
Verification: `uv run pytest tests/test_funding_preentry_source_audit.py -v`,
`uv run ruff check .`, repository CI and Historical Backtest Smoke.

Evidence checkpoint: main `ea69203deb6b220e7bf2d851cc63d9b76f38c2fd`
([CI 39112320029](https://github.com/pkking/future-opportunity/actions/runs/39112320029)
SUCCESS), no open PR at start, Issue #85 OPEN / BLOCKED_EVIDENCE.
The only missing external fact remains independently authenticated future-day
source publication. The audit cannot retroactively prove July/August data timing.

## 2026-10-18 implementation checkpoint — awaiting PR evidence

The review branch `agent/funding-preentry-offline-audit` contains the offline audit script,
standalone negative tests and the manual provenance-verification procedure.
The check accepts only original ZIP bytes plus independently supplied digest
and UTC day, and emits `offline_replay_verified_only`; it does not invoke
OKX, GitHub or the exchange trading API. **CI not yet confirmed** as of this
checkpoint; the open Issue #85 retains its external evidence blocker.

## 2026-10-18 offline-audit implementation verification (PR #123)

- [PR #123](https://github.com/pkking/future-opportunity/pull/123)
  initial tested head `b23f7f06bb926128bf02ae65248275684d6c5e86`:
  [CI 39113460207](https://github.com/pkking/future-opportunity/actions/runs/39113460207)
  five checks **SUCCESS**: static architecture, code-level including
  `tests/test_funding_preentry_source_audit.py`, API, E2E and agent-plan;
  [Historical Backtest Smoke 39113460257](https://github.com/pkking/future-opportunity/actions/runs/39113460257)
  **SUCCESS** on the same SHA.
- Offline ZIP replay code, fail-closed tests and separate Sigstore review
  instructions landed on the review branch. No true pre-entry source has
  been captured, independently verified, or retrospectively authenticated.
- This documentation checkpoint itself requires a **new final-head CI and
  Historical Smoke** before the PR may merge. Record their final run/commit
  against PR #123 or the Issue thread before closing this engineering slice.
- Status returns to `BLOCKED_EVIDENCE` because the Issue's source-authenticity
  and missing negative/low regime evidence are still unresolved. No acquisition,
  corpus promotion, numerical economics gate or live trade is approved.

## 2026-10-18 authorized unattended pre-entry capture (Issue #85)

**Human decision received 2026-10-18:** enable option A, a separate scheduled
GitHub Actions workflow pre-warmed before UTC midnight. This explicitly changes
the earlier manual-only/no-scheduled-capture posture **for prospective source
observation only**; all economic/provenance/trading limits remain unchanged.
The manual workflow stays manual-only and its clock gates remain intact.

Objective: eliminate exact-time operator intervention without weakening any
as-of-entry safety boundary. Reuse existing public-GET collection, signed
GitHub raw subject and offline archive replay (PR #123). GitHub's schedule is
best effort and can delay/drop runs: missed days become explicit missing evidence,
never retrospectively inferred successful samples.

Acceptance criteria:
- [x] New `schedule`-only workflow, daily **23:37 UTC** start (not on the
      high-load hour), pre-installs dependencies, then waits until the *following*
      00:00 UTC or executes promptly if delayed into 00:00..00:15 UTC.
- [x] Finite waiting: refuse unexpected late-day start, crossed UTC 00:15
      cutoff, naive/bad clocks; never sleep to the **next** day's opening after
      a missed window. Runner timeout allows the prewarm window.
- [x] Existing strict capture implementation makes at most two unauthenticated
      GETs, both with completed responses strictly before 00:15 UTC; no
      modification to the canonical source/time/replay validators.
- [x] Failure writes `UNASSESSED` error-only artifact and does not invoke
      signing; success retains the exact original three-file source ZIP,
      GitHub raw-file provenance attestation and read-only 90-day retention.
- [x] Workflow cannot be manually dispatched, has no `push` trigger,
      prevents concurrent auto-capture and excludes rerun attempts; manual
      diagnostic workflow stays unchanged.
- [x] Offline tests cover both sides of midnight, GitHub delay, deadline,
      malformed/rolled-back clocks, and static workflow permissions/triggers.
- [ ] Final-head static/code/API/E2E/plan + Historical Smoke all SUCCESS;
      postmerge main CI SUCCESS. Record exact run IDs, no automatic
      fixture acquisition/promotion, Stage-2 economics or exchange trading.

Implementation slices:
1. Pure, deterministic UTC wait/guard helper + offline tests.
2. Scheduled Actions shell with minimal permissions and `if: always()`
   failure receipt; separate signed raw source only on successful capture.
3. Document scheduling risk, as-of provenance limitations and operational
   verification; PR review and complete CI before merge.

Baseline: `db35d8d0e0b636ce357b2bf9921755fbffac945a`,
[main CI 39113607582](https://github.com/pkking/future-opportunity/actions/runs/39113607582) SUCCESS.
Manual runs [39113998331](https://github.com/pkking/future-opportunity/actions/runs/39113998331)
and [39115074084](https://github.com/pkking/future-opportunity/actions/runs/39115074084)
failed **as designed** outside UTC window with one error-only artifact each.
No original prospective market-response ZIP exists yet.

Safety: keep Funding 32, Cash 66, 100bps regime threshold, four buckets,
all previously fixed historical dates, historical economics gate OFF and live
trading OFF. Scheduled success still reports `point_in_time_publication_verified=false`
until independent external verification. Decision was only to automate capture,
**not** to approve an economic opportunity.

### Implementation checkpoint (before PR final-head CI)

- New: `.github/workflows/capture-funding-preentry-scheduled.yml`,
  `scripts/wait_for_funding_preentry_window.py`,
  `tests/test_funding_preentry_scheduled_window.py`.
- Updated: `docs/research/funding-prospective-point-in-time-capture-contract.md`.
- No modification to manual-only source workflow or its independent bounded GET
  validator. Scheduled GitHub runner re-runs are disabled and no event except
  `schedule` can start the new workflow.
- Static and offline unit tests are authored; **test success not asserted before
  CI runs**. Need final-head five CI checks and Historical Smoke on this revision.
- True prospective event evidence still **UNASSESSED**, and Issue #85 cannot
  be closed merely because the schedule is configured.


### 2026-10-18 PR #124 implementation-head verification

- [PR #124](https://github.com/pkking/future-opportunity/pull/124)
  implementation head `a48111e72454d0a90f6aa6a0ddd00076cca35957`:
  [CI #39116716764](https://github.com/pkking/future-opportunity/actions/runs/39116716764)
  **5/5 SUCCESS** (static, code-level including new scheduler tests,
  API, E2E, agent-plan);
  [Historical Backtest Smoke #39116716755](https://github.com/pkking/future-opportunity/actions/runs/39116716755)
  **SUCCESS** on that same commit.
- New pure bounded wait guard, cron-only pipeline, UTC timing/failure tests,
  and documented provenance boundary validated by repository CI. No scheduled
  job has fired yet and no public source has been captured under this design.
- Record final **documentation-head** PR CI/Smoke after this checkpoint commit,
  then merge. The Issue remains `BLOCKED_EVIDENCE` because exchange publication
  time and negative/low regime observation are not independently proven.

## 2026-10-18 automated read-only review of scheduled captures (Issue #85)

**Decision scope**: continue user-approved option-A unattended *prospective*
source-observation infrastructure. This slice adds a second, independently
started GitHub job to check the scheduled workflow's exact immutable artifact,
replay the offline source validator and verify first-party GitHub provenance.
It never treats this as OKX publication authentication or changes the accepted
research/economics/trading policy.

Problem: PR #124 captures and uploads only. Every future run would still need
an operator to download the original ZIP, check its GitHub-issued digest,
recompute features and inspect its signed file. Failures must remain visible
rather than being silently accepted as empty market regimes.

Acceptance criteria:
- [x] A follow-on read-only audit job runs after scheduled capture, even on
      capture failure. It downloads the **original** (not repacked) Actions ZIP,
      checks a separately fetched artifact ID/digest owned by that same run,
      and refuses wrong-run, duplicate or missing artifact metadata.
- [x] Existing `audit_funding_preentry_source_artifact.audit_zip` runs
      unchanged for successful attempts and requires exact observed UTC day;
      offline replay cannot be claimed without raw/time/research agreement.
- [x] The original raw JSON file is checked using official `gh attestation
      verify` with constrained repository, signer workflow, main ref, commit
      SHA and raw subject digest; verification errors fail closed.
- [x] Failed capture with `error.json` is reported `UNASSESSED` with explicit
      reason; no attestation success claimed. Strictly reject forged status
      flags, malformed JSON or unusual ZIP members even for failure receipts.
- [x] Any success says GitHub provenance validated only, **not** exchange-
      authenticated historical availability; no change to `point_in_time_publication_verified=false`,
      no promotion/acquisition/economics/live orders.
- [x] Deterministic, fully offline tests for all positive/negative paths,
      including mocked GitHub CLI and ZIP identity, with documented review
      metadata schema. Final-head PR CI 5/5 + Historical Smoke and postmerge
      main CI recorded before calling engineering slice complete.

Implementation:
1. Write a pure-input audit orchestrator for Actions ZIP + immutable run
   metadata and a verifier injection boundary (no network from unit tests).
2. Wire `needs: capture` read-only audit job in the approved **scheduled**
   workflow, using first-party artifact download with original ZIP option,
   `gh api` run metadata and `gh attestation verify`.
3. Publish machine-readable review/error artifact, tests and documentation.

Current baseline: `1a1e21cc67ec66eeea7605b597a58f592342826c`,
[main CI 39116878803](https://github.com/pkking/future-opportunity/actions/runs/39116878803) SUCCESS.
Issue #85 OPEN, no prior successful scheduled capture to audit. Independent
pre-entry OKX source-publication claim stays **UNASSESSED**.

### Implementation checkpoint before PR validation

- Pure orchestration `scripts/audit_scheduled_funding_capture.py` consumes
  exactly matching Actions run metadata, original ZIP and immutable artifact
  digest; it reuses existing independent `audit_zip` and GitHub CLI signature
  policy and generates an explicit machine-readable result or failure.
- New `audit` job on the existing *scheduled-only* workflow uses first-party
  ZIP download without decompressing, `gh api` run/artifact identity and
  bounded read-only `gh attestation verify`. A failed capture receives
  `UNASSESSED` without requiring any nonexistent attestation.
- Added offline unit tests and source evidence contract documentation.
  **Tests not yet run at this checkpoint**: require final PR-head normal CI,
  historical smoke, and postmerge main CI; no actual scheduled source received.
- No change to historical corpus, Funding regimes, strategy outcomes, order
  routes or Stage-2 economics approval.


### PR #125 implementation-head verified (2026-10-18)

- [PR #125](https://github.com/pkking/future-opportunity/pull/125)
  initial implementation head `6f3774ed0d662a0fb243eb07b91138dc05903f97`:
  [CI #39118649398](https://github.com/pkking/future-opportunity/actions/runs/39118649398)
  **5/5 SUCCESS** (Static, code-level including new audit tests, API,
  E2E, agent-plan integrity),
  [Historical Smoke #39118649404](https://github.com/pkking/future-opportunity/actions/runs/39118649404)
  **SUCCESS**.
- Follow-on audit job uses GitHub-signed subject identity and the same offline
  validator, but neither metadata nor attestation alone verifies OKX's
  historical publication. A prospective scheduled observation has not yet run.
- This **documentation checkpoint** requires final-head CI and Smoke before
  merge, then postmerge main CI. No acquisition or quantitative economics gate.

## 2026-10-19 first scheduled production-run recovery (#85)

**Observed production facts before implementation:**
- [Run 39186235557](https://github.com/pkking/future-opportunity/actions/runs/39186235557), `event=schedule`, SHA `8f72aac5394712b49e9c60fffbe9dcec146dbb5a`,
  created **2026-10-19T01:37:54Z** versus committed daily cron `23:37 UTC`.
  This first execution was around **2h00m54s late** (assuming the intended
  immediately preceding scheduled slot). GitHub's documented best-effort
  delivery does not guarantee an observed run for every scheduled occurrence.
- Capture job 117849148647 failed at its before-GET guard at 01:38:02Z:
  `scheduled preentry runner missed current UTC window`. The original
  `capture_funding_preentry_source.py` and OKX GET were not reached.
- Read-only audit job 117849187922 downloaded the original source error-only
  ZIP but then failed in `_identity` because it incorrectly called the
  **successful-capture-only** `target_midnight()` admission function for a
  failed capture. This is a genuine loss of useful failure classification, not
  a failed market observation or a safe reason to relax capture deadlines.
- Immutable source error artifact 12158480804 digest
  `sha256:9b08b29645b22cbcecedc94094d7461be5e4c7ac7ef883d2384bb1fd7111f5a2`;
  audit error artifact 12158406450 digest
  `sha256:dc541a389c59af85100ac5be8abd5dfbf26e5158e43c7f35e764ba0629868333`.
  Neither is market-source data.

Objective: make the audit accept an **honestly failed** late/dropped schedule
and verify its original ZIP/digest/error-only receipt, preserving the missing
observation as `UNASSESSED`. Do not weaken admission of successful captures.

Acceptance criteria:
- [x] The same missed 01:37 UTC recorded run can be represented by an offline
  deterministic regression case, yielding `failed_capture_unassessed` and
  `entry_market_date=null`, not a fabricated historical date.
- [x] Failed capture still requires valid UTC-aware run timestamp, exact
  repository/workflow/commit/schedule identity and independent ZIP digest,
  single safe error receipt, no GitHub attestation claim.
- [x] Successful capture at an invalid/late time remains fail-closed;
  legitimately created, prewarmed/within-window successful captures continue
  their original three-file replay + independent signed subject verification.
- [x] Machine-readable review records actual run creation time and whether
  its admission window was eligible/missed, without claiming exact scheduled
  delivery timestamps unavailable in the GitHub API.
- [x] Targeted offline tests + final five CI gates and Historical Smoke
  succeed; final PR commit and postmerge main CI recorded.

Explicit scope limits: no additional auto-polling, no change to cron,
no price/funding/regime threshold changes, no historical acquisition or
promotion, no economic gate and no live exchange order path. **Option A
cannot guarantee a timely run when GitHub delays a schedule by hours**;
consider an externally timed source only via a new architecture/operational
approval, and never backdate this failed run.

### 2026-10-19 implementation checkpoint before PR CI

- Modified `scripts/audit_scheduled_funding_capture.py` to continue
  fail-closed ZIP/run/digest/error receipt validation for failed runs created
  after the 00:15 UTC cutoff; success path retains original strict admission.
  Failed runs now record actual created time and the clock admissibility state
  with `entry_market_date=null` and without signed-source claims.
- Extended `tests/test_funding_preentry_auto_audit.py` with a frozen run
  `39186235557` regression identity, success-time rejection, malformed UTC
  clocks, tampered artifacts and formerly eligible failed-run checks.
- Documented the actual two job logs and the independent ZIP digests.
- Verification not yet asserted: PR static/code/API/E2E/plan CI and historical
  smoke plus postmerge main CI must all pass. Production capture still has no
  admitted market data; do not automatically enable a different scheduler.

### 2026-10-19 PR #126 implementation-head evidence

- [PR #126](https://github.com/pkking/future-opportunity/pull/126)
  implementation SHA `d5108dc8eee3bea2e80e04066a6db44bedf1a9ea`:
  [CI #39277314496](https://github.com/pkking/future-opportunity/actions/runs/39277314496)
  **5/5 SUCCESS**, including new late-run/error-only audit regression tests;
  [Historical Backtest Smoke #39277315089](https://github.com/pkking/future-opportunity/actions/runs/39277315089)
  **SUCCESS**.
- This checkpoint document changes the PR head again: record final-head
  checks separately; do not merge based only on the earlier tested revision.
- Issue #85 remains `BLOCKED_EVIDENCE` for actual source publication as-of-entry
  and missing negative-low regime. GitHub delayed delivery cannot be remedied
  by reinterpreting late errors as market-day observations.

## 2026-10-19 authorized Plan B: VPS systemd source collection (#85)

**Decision received:** replace the GitHub Actions best-effort cron as the
*primary* prospective UTC-window source trigger with a VPS `systemd`
calendar timer. Keep existing GitHub CI and existing scheduled action as
a research-only secondary/diagnostic path. User has approved the architecture;
no VPS credentials, host or storage destination have been supplied, so
installation and a real VPS-produced sample are still UNASSESSED.

Evidence motivating change: [scheduled run #39186235557](https://github.com/pkking/future-opportunity/actions/runs/39186235557)
was created at `2026-10-19T01:37:54Z`, over two hours later than the
configured 23:37 UTC trigger; it failed before any OKX GET. PR #126
fixed the audit outcome and was merged as `3a1b0960a03f4bc2d483b3bba45fe6617df2aed1`;
[postmerge main CI #39277720623](https://github.com/pkking/future-opportunity/actions/runs/39277720623) SUCCESS.

Objective: a deployable least-privilege systemd one-shot source collector,
started after 00:00 UTC, enforcing exact existing 00:15 cutoff and
saving an immutable per-day local spool with original research-only raw
JSON, UTC timing, consistency replay and machine-readable integrity
checksums. Neither root privileges nor Github/exchange tokens are needed
by the collector. GitHub remains the CI/source-review tooling; the VPS
transport to GitHub-hosted immutable artifact/attestation is NOT wired
without an approved secure storage/transport destination.

Acceptance criteria:
- [x] systemd `*.service` and `*.timer`: explicit UTC calendar, narrow
      accuracy, no catch-up on reboot, no restart, non-root dynamic user,
      read-only code tree and writable state dir, NTP synchronization prerequisite.
- [x] Python wrapper invokes the unchanged `capture_today` only once,
      requires trusted *operational* NTP state and matching UTC window,
      atomically retains an immutable per-day success/failure archive,
      source ZIP digest and no duplicates/backdating or overwrite.
- [x] Valid success: existing three files and deterministic local offline
      `audit_zip` replay, with `github_attestation_verified=false`,
      `point_in_time_publication_verified=false`, promotion OFF.
      Error: only explicit UNASSESSED receipt, never partial source data.
- [x] Offline negative tests cover clock guard/unsynchronized NTP,
      duplicate day, failed capture, ZIP replay/corruption, permission and
      timer/service safety, with no external HTTP or real orders.
- [x] Operator playbook contains VPS bootstrap, time-sync verification,
      timer deployment and journal/local evidence commands, secure artifact
      handoff prerequisites, and distinguishes true independent provenance
      from local VPS clock + digest (which can be tampered with).
- [ ] PR CI 5/5 + Historical Smoke and postmerge main CI succeed; record
      exact final-head checks; Issue #85 stays OPEN/BLOCKED_EVIDENCE
      until genuine separately verified prospective source data exists.

Non-goals: no live trading, no authenticated OKX API, no raw source blobs
committed to git, no change to Stage-2 economics, Funding 32 or Cash 66,
no new automatic cloud credentials, no claimed deployed VPS, no force
disabling the existing GitHub workflow before host-level validation,
and no assertion that `systemd` provides hard real-time or trusted
exchange publication time.

Implementation: (1) add independent dated immutable spool wrapper;
(2) unit and integration-style offline tests; (3) systemd units + runbook;
(4) PR CI/merge checkpoint. Stop at verified repo-side handoff if VPS
access and secure destination are not available; this is a deployment
blocker rather than an engineering success claim.

### Plan-B code-ready checkpoint — before CI verification

- New `scripts/run_vps_funding_preentry.py`: reuses existing source capture
  and strict `audit_zip`, checks `timedatectl NTPSynchronized=yes`,
  holds a nonblocking local exclusive lock and publishes a single atomic
  dated ZIP + metadata receipt; neither partial raw output nor a second
  attempt is accepted, no network retry or GitHub token.
- `deploy/systemd/future-opportunity-funding-capture.{service,timer}`:
  sandboxed dynamic user, owner-private persistent state dir, UTC 00:00:10,
  one-shot no catch-up/retry, restrictive code filesystem and no runtime
  credentials. The previous GitHub scheduled collector remains secondary.
- Added offline time/NTP/duplicate/failure/ZIP replay/service contract
  tests in `tests/test_funding_vps_collector.py`,
  [ADR-0010](../../adr/0010-vps-funding-prospective-scheduler.md),
  [VPS deployment runbook](../../operations/funding-vps-systemd-capture.md),
  README and source evidence contract.
- **CI not yet run** at this checkpoint; final PR-head five CI gates and
  Historical Smoke plus postmerge main CI remain required.
- **Deployment blocked by missing VPS connection** and destination/provenance
  decision. Repo-side implementation cannot honestly claim an operational
  daily VPS run or signed independent as-of data.

### 2026-10-19 Plan B PR #127 final implementation-head CI evidence

- [PR #127](https://github.com/pkking/future-opportunity/pull/127)
  verified implementation head `477abe70b7d4abd5fceb29b617858fe98eff76b9`:
  [CI #39283471363](https://github.com/pkking/future-opportunity/actions/runs/39283471363)
  **five check-runs SUCCESS**, including VPS offline source tests, static, API,
  E2E and Agent Plan Integrity;
  [Historical Backtest Smoke #39283471425](https://github.com/pkking/future-opportunity/actions/runs/39283471425)
  **SUCCESS** on the same SHA.
- This checkpoint documentation itself changes the PR head. Require new final
  head CI/Smoke before merge and postmerge main CI. The separate production
  host installation is not done and source timing is not independently attested.
- Underlying #85 stays OPEN/BLOCKED_EVIDENCE with zero new externally
  authenticated prospective samples; no promotion or trading.

## 2026-10-20 incident — VPS NTP state inaccessible via sandboxed D-Bus (#85)

**User-observed host and production facts**: VPS `systemd` timer triggered
on 2026-10-20T00:00:10Z, but the actual service reported
`status=UNASSESSED`, `entry_market_date=null`, original error-only
source ZIP digest `52756a4d01ca5edc9a8f0f6e71f9802a4064e5955da1cbc3b5be0614c0da9bd8`,
reason `VPS NTP clock is not confirmed synchronized`, no OKX GET.
Host `timedatectl status` and `timedatectl show -p NTPSynchronized --value`
both report synchronized/yes; `systemd-timesyncd` is active and the
VPS uses KVM virtualization. A sandboxed `systemd-run` probe reproduces
the underlying failure from `timedatectl`: exit 1, no stdout, stderr
`Failed to parse bus message: Transport endpoint is not connected`.
The `systemd-run` wrapper reported success only because the probe Python
process exited 0 after printing diagnostics. Querying `timesyncd` logs
for 2026-10-19T23:45 to 2026-10-20T00:20 produced no entries, which
neither proves nor disproves host clock synchronization in that window.

**Root cause established**: the subprocess' D-Bus query cannot obtain
`timedatectl` status in the restrictive DynamicUser service. Its
all-failures-false path intentionally blocked capture, but incorrectly
coupled a safe clock check to a service-incompatible transport.
Official systemd-timesyncd docs specify a `/run/systemd/timesync/synchronized`
marker touched on each successful synchronization, which can be read
without D-Bus. Official default `PollIntervalMaxSec` is 2048 s.
Use recent marker data only (<=2 h), not bare existence.

**Objective**: check host `systemd-timesyncd` successful NTP
synchronization through a **read-only, age-limited runtime marker** that
works under DynamicUser+ProtectSystem; fail closed if missing, symlink,
non-regular, stale, invalid/future timestamp or inaccessible. Do not
change timer time, sandbox profile, sources or historical evidence.
The marker is a local operational precondition, **not** a third-party
signed source publication timestamp, nor authoritative proof of current
precision. Host-side probe is still required to establish marker exists
and is readable under actual sandbox.

Acceptance criteria:
- [x] Operational NTP gate uses no D-Bus and never returns true on an
      old/unknown/forged marker or time anomaly; default allowed age <=2h
      covers default timesyncd 2048s poll while rejecting stale sync.
- [x] Deterministic offline tests verify fresh/old/missing/symlink/
      non-regular/future/permission errors and service's fail-closed
      source-GET avoidance.
- [x] Unit keeps nonroot DynamicUser and strict sandbox, UTC cutoff,
      no second attempt and research-only provenance flags unchanged.
- [x] Runbook documents proof boundaries, host/sandbox read-only probe
      and patch-deployment steps, including keeping the 2026-10-20
      UNASSESSED receipt immutable. No host deployment claim.
- [ ] Final PR HEAD CI five required checks and Historical Smoke plus
      postmerge main CI verified and recorded in Issue #85.

Non-goals: no new NTP daemon, no `timedatectl set-ntp` policy change,
no NTP check bypass, no root service, no polling/retrospective backfill,
no promotion or order placement. Branch `fix/funding-vps-ntp-sandbox-marker`.
Expected edits: `scripts/run_vps_funding_preentry.py`,
`tests/test_funding_vps_collector.py`,
`docs/operations/funding-vps-systemd-capture.md`, active plan.

### 2026-10-20 NTP sandbox fix ready for CI

- Changed `scripts/run_vps_funding_preentry.py` clock preflight from
  subprocess `timedatectl` D-Bus to reading `/run/systemd/timesync/synchronized`
  via `Path.lstat()` with strict regular-file/no-symlink check and
  `0 <= sync_age <= 7200 seconds`, returning false on missing,
  permissions, invalid clock, stale or future marker. No new credentials,
  dependencies, subprocess, relaxation or retry.
- Deterministic offline tests added for fresh/at-boundary/stale/future
  marker, symlink, directory, nonexistent, PermissionError, naive clock
  and no-OKX-GET `UNASSESSED` on stale sync. Existing success path and
  source provenance remain unchanged.
- Updated VPS operations runbook with the actual first scheduled failure,
  a read-only `systemd-run` sandbox marker probe, pin-to-merge-SHA
  deployment advice and explicit limits of local NTP marker trust. Also
  moved the prior lockfile note outside its mistaken Bash code fence.
- CI and actual sandbox marker probe **not yet verified** at this
  checkpoint. Do not infer VPS host behavior solely from offline tests.

## 2026-10-21 VPS source independent offline handoff / review (#85)

**Observed production evidence:** The first Plan B local SUCCESS at
2026-10-21T00:00:10..00:00:13Z contains the VPS-local original three-file
source ZIP with `local_replay_only` in its dated manifest:
`archive_sha256=6adc7385b4e32aabd886abf27b53446c1ecab1b00ec23f664b69861a149bfd3a`;
`raw_file_sha256=5e753951d8317eb1e32265554d17b13cc515d293dda6108690f7c2f3a4828c0e`,
`canonical_source_sha256=88365202bc78791c4cc8f2339cb356ea44f9fc36551ba065280affbefe813609`,
`regime=nonnegative_low_volatility`, `entry_market_date=2026-10-21`.
The operator provided original `manifest.json`, systemd journal and a
separate local `sha256sum` matching the manifest. Original ZIP bytes are
**not** available to the agent, nor any off-host storage/authentication.
All promotion and independent publication flags remain false.
Separately, GitHub's scheduled [run #39530434373](https://github.com/pkking/future-opportunity/actions/runs/39530434373)
created too late at 01:59:11Z and failed closed; no substitute observation.

**Goal:** build the next *credential-free* verification boundary so an
independent reviewer who securely obtains unmodified VPS files can
deterministically validate (a) an externally supplied ZIP digest, (b)
the exact VPS manifest/source identity and allowed UTC metadata,
(c) success-only three-file original ZIP replay and all expected hashes/
regime, or (d) explicit original one-file UNASSESSED failure receipt,
without using the GitHub-origin scheduled workflow auditor incorrectly.

**Acceptance:**
- [x] Offline reviewer requires independently supplied archive digest and
      UTC day, rejects mismatched original ZIP, forged/invalid/missing
      manifest, duplicate/surplus ZIP members, improper day/source identity,
      conflicting file/hash/regime/status and unsafe failure receipts.
- [x] Reviewer never elevates any self-reported VPS clock or digest into
      independent provenance, never approves acquisition/promotion, trading,
      exchange signature or GitHub-origin attestation; output labels
      `offline_vps_replay_only` vs `failed_capture_unassessed`.
- [x] Reviewer writes an optional *new* read-only review receipt locally
      without overwriting earlier review; receipt time is review time and
      never reinterpreted as original capture time; no network calls.
- [x] Deterministic offline tests cover canonical success, failure-only,
      host/identity tampering, ZIP tampering, manifest flag spoofing,
      wrong regime/hash/date, duplicate members, missing witness and
      exact 2026-10-21 manifest metadata as a frozen case without
      manufacturing actual raw source data.
- [x] Operations runbook documents operator copy out of private VPS
      state, independent SHA witness workflow and precise limitations.
      No long-lived credentials/token or silent transfer destination.
- [ ] Final PR 5/5 CI and Historical Smoke green; merge on final SHA
      and verify postmerge main CI; Issue #85 stays OPEN/BLOCKED_EVIDENCE
      until separately reviewed source publication policy and real
      deficient regime evidence exist.

No premature choice of cloud account/secret/bucket, retention policy,
S3 object lock or automatic remote upload. Transport is a *separate
security decision*. Missing independent historical timestamp is not
retroactively solved by copying the 2026-10-21 archive later.
Code touch list: `scripts/audit_vps_funding_capture.py` (new),
`tests/test_funding_vps_receipt_audit.py` (new),
`docs/operations/funding-vps-systemd-capture.md`,
`docs/research/funding-prospective-point-in-time-capture-contract.md`,
active plan.

### 2026-10-21 offline VPS original evidence review code checkpoint

- New `scripts/audit_vps_funding_capture.py` reads **unmodified**
  VPS manifest + original ZIP with an externally supplied expected SHA256
  and market UTC date, checks bounded regular input files, duplicate
  manifest keys, exact origin/schema/false provenance flags, strict local
  start day, success-only three-file replay, manifest raw/canonical
  hashes and regime, or verified error-only UNASSESSED.
  It never passes VPS bytes to a GitHub-origin run auditor.
- Optional owner-private independent-host `--receipt-out` creates a
  new JSON review receipt with recorded review time **not** source capture
  time and all external digest authentication/approval flags false.
- Deterministic fixture tests for success/error and forged flags, hashes,
  regime, dates, ZIP member lists, symlinks, size boundaries, duplicate
  JSON keys, and frozen actual 2026-10-21 metadata correctly rejected
  when matched to nonmatching synthetic ZIP bytes.
- VPS operational runbook adds manual encrypted SSH handoff example and
  independent review command with the operator-provided **real** ZIP
  SHA256, emphasizing its known VPS origin. No automated push credentials
  or remote storage choice and no claim of authenticated as-of time.
- CI/Smoke **not yet verified** at this checkpoint; first 2026-10-21
  source original ZIP has not been supplied to the reviewer and
  source publication confidence remains UNASSESSED.

### 2026-10-21 independent offline reviewer implementation CI

- [PR #130](https://github.com/pkking/future-opportunity/pull/130)
  first implementation head `38068cd65ccb8800abfc385c323d3bf99bde60a9`
  [CI #39632822364](https://github.com/pkking/future-opportunity/actions/runs/39632822364)
  failed one new code-level regression: duplicate-key rejection correctly
  failed closed but outer JSON error wrapper did not preserve the
  `duplicate` cause; **667 other tests passed**. No tests were weakened.
- Corrected the actual diagnostic wrapper to retain the rejection cause
  and validated code head `8f56a8a3c596136385766c44f16544f902436ed9`:
  [CI #39633016665](https://github.com/pkking/future-opportunity/actions/runs/39633016665)
  **5/5 SUCCESS** and
  [Historical Backtest Smoke #39633016682](https://github.com/pkking/future-opportunity/actions/runs/39633016682)
  **SUCCESS**.
- **This documentation checkpoint changes the final PR head**;
  rerun and verify fresh 5-job CI + historical smoke for this later
  head before any merge, and verify postmerge main CI afterward.
- Real VPS ZIP bytes, independent source/publishing time evidence and
  immutable external witness are **not yet available**.
  Explicit trusted sink, WORM retention and credentials require a
  separate security/operator decision. Do not report Stage 2 success.

## 2026-10-21 GitHub-only storage/trusted receipt decision (approved scope)

**New explicit constraint:** User rejected external OBS/S3/TSA and requires
**only GitHub's free features for open-source public repositories**.
Do not re-propose third-party object storage or time authorities.
Research of GitHub public docs confirms:
- GitHub Actions standard hosted runners are free for public repos.
- Public Actions Artifacts and logs have **1–90 day retention**, so they
  cannot be the sole indefinite original source archive.
- GitHub Immutable Releases can lock release assets and tag once a draft
  is **published**, automatically creating a GitHub release attestation.
  This is enabled under repo Settings → Releases for **future releases**
  and requires repository admin privilege.
- GitHub REST release asset metadata contains `digest`, `created_at`,
  ID and server URL; published release metadata includes `published_at`
  and `immutable`. A draft release is editable and not yet immutable.
- GitHub REST write requires a repo-scoped Contents:write token issued
  to an authorized uploader. **No actual token/installation was provided**.

**Goal**: Build a GitHub-native, fail-closed **prospective** evidence
publisher from the VPS's *already completed* source ZIP to a per-day
immutable GitHub Release, plus an independent no-secrets public GitHub
receipt verifier. It must complete before UTC 00:15 with no new OKX calls
and no existing historical source rewrite. Deployment must remain
DISABLED until an approved GitHub credential and repository
"Enable release immutability" setting are available.

Strict acceptance:
- [ ] Publisher runs only for the **current** UTC day after local
      `status=local_replay_only`; it verifies local ZIP SHA256 and
      identity before outbound GitHub writes; UTC <00:15 is rechecked
      at each phase. Does not backfill 2026-10-20 or -21.
- [ ] REST sequence: create one daily **draft** release, upload exactly
      `original-source.zip` and `manifest.json` without repacking,
      confirm GitHub server-provided asset digest/created_at for both,
      publish before 00:15; require `published_at` <00:15 and
      `immutable=true` (else UNASSESSED, never falsely promote).
      No delete, asset overwrite, release substitution, retry after
      deadline or Github tag collision overwrite.
- [ ] Credentials only injected by **explicitly configured** systemd
      `LoadCredential` to a distinct post-capture publisher. Never
      put token into source collector, repository files, logs,
      release assets, manifest, or CI; narrow scope to GitHub
      Contents:write. No service auto-enabled by PR alone.
- [ ] Public read-only verifier can independently retrieve release
      metadata and original bytes from GitHub and call the existing
      strict VPS offline audit; checks release immutable, GitHub-hosted
      asset digests, asset/server publish time before 00:15,
      exactly two assets and matching UTC date/tag. Does not
      pretend GitHub server creation time proves OKX dissemination.
- [ ] Offline regression suite checks release collisions, duplicate
      or partial uploads, late publish, forged digest/timestamp,
      missing immutability, bad source, credentials missing, expired
      window; no actual public releases or live OKX traffic from CI.
- [ ] Runbook + GitHub-only ADR clarify data is **publicly downloadable**
      and future repository Release immutability needs repository admin
      enabling. Artifacts are ephemeral (<=90d); do not use as
      long-term sole source. No external store/TSA.
- [ ] Final PR head five CI jobs + Historical Backtest Smoke success,
      merge, postmerge main CI, Issue #85 checkpoint. Stage 2 blocked
      until actual verified future-day GitHub witness and independent
      publication decision. No trading.

**Boundary:** This agent can author and test code through GitHub, but
cannot access VPS state, enable admin repository immutability settings
or install a VPS GitHub credential without an operator. The current
2026-10-21 local-only ZIP cannot retroactively gain before-entry
Github server-time evidence.

## Resume from here

Build fail-closed GitHub-only immutable-release evidence publisher and public verifier, deterministic offline tests, on-success unit example and operator handoff; run CI, merge when fully green, archive on #85. Do not auto-enable credentials or release publication. Require explicit admin to enable future Immutable Releases and operator to inject repo-scoped GitHub token before first live upload.

## Completion

In progress; July/Aug source run succeeded but publication-as-of-entry and full four-regime quota remain **UNASSESSED / NOT MET**, respectively. Funding corpus remains 32 and Cash 66.
