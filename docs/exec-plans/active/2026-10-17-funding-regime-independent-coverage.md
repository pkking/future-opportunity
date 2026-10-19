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

## Resume from here

Verify the **final plan-head** PR #126 CI and Historical Smoke (in addition to implementation-head evidence), then merge only if all succeed; verify postmerge main CI. Record final evidence in Issue #85 and remain BLOCKED_EVIDENCE for actual independent source observation. Retain GitHub schedule best-effort limitation without changing the accepted source clock cutoff.

## Completion

In progress; July/Aug source run succeeded but publication-as-of-entry and full four-regime quota remain **UNASSESSED / NOT MET**, respectively. Funding corpus remains 32 and Cash 66.
