# Cash 2025Q2 additional independent expiry cohort

Issue: #95
Status: BLOCKED_DECISION
Owner: agent
Started: 2026-10-17

## Objective
Advance from an independently proven **single** BTC-USDT-250627
source book observation to an **outcome-blind historical source
availability population**, then separately freeze candidate dates
and use existing governed acquisition/promotion stages. Never
promote the exploratory 2025-06-12 source-probe date as-is.

## Baseline / user problem
Current Cash pinned corpus has 54 market dates across four
maturity cohorts. More entries within one expiry are correlated;
we need an additional independent maturing contract, but must
not select dates using paper returns or existing results.
- [Issue #86](https://github.com/pkking/future-opportunity/issues/86)
  and PR #94 establish `BTC-USDT-250627` source capability.
- [Official source Run 39029586457](https://github.com/pkking/future-opportunity/actions/runs/39029586457),
  artifact 12100345294 SHA-256
  `692d51599fa7d08ca75a1975b0bca3ceff4d1815a81b9f476476dcb4f6e172b5`:
  4/4 canonical SPOT/FUTURES books at 00:15 UTC for
  2025-06-12/2025-06-26, source max lag 40ms.
  This source-only run has no PnL evaluation, qualified labels
  or sampling provenance and is NOT a promotable case.

## Non-goals and invariants
- No source queries until fixed candidate-calendar bounds are
  committed in main. No selection from price spreads, qualified
  labels, expected or realized outcomes.
- Candidate range 2025-03-29..2025-06-26 (after Q1 expiry,
  before 2025-06-27 expiry); treat dates before actual listing
  as unavailable, never fabricate archived members.
- Exact `BTC-USDT-250627` contract and 2025-06-26 00:15 UTC
  pre-expiry exit; no date substitution based on strategy PnL.
- Catalog date availability is necessary but not sufficient
  evidence of historical complete source L2; actual sampled
  books require independent archive digest/level verification.
- Future promotion remains operator-controlled with reviewed PR,
  no live trading, no automatic Stage-2 economics gate.

## Acceptance criteria
- [x] Freeze source-capacity scope in
      `docs/historical-acquisition-plans/cash-2025q2-source-capacity-study-v1.json`
      before any official OKX catalog queries.
- [x] Implement read-only official module-4 FUTURES/SPOT 90-day
      daily source population scanner; preserve raw-response
      hash, exact date and source identity, missing/error days
      and bounded/retry behavior. No download or PnL during
      calendar population scan.
- [x] Independently verify actual source run/Artifact SHA and
      population; validate separate 2025-06-26 exit evidence. Source-member identity is 90/90; exit 00:15 L2 from run 39029586457, but selected entries remain unverified.
- [x] Apply strict `availability-even-rank-v1` to verified
      eligible population only; pre-register N=12 exact dates
      and source provenance **before** their strategy outcomes,
      in a separate reviewed PR. If coverage insufficient,
      stop without selection.
- [ ] Only upon reviewed frozen selection use original
      preparation/Compact/Actuals workflow, complete content
      audit and read-only planner, then separately reviewed
      corpus promotion. Do not use missing or rejected days
      as automatic replacement.
- [ ] All code/API/E2E/Agent Plan/Historical Smoke pass
      at final PR head; postmerge main CI verified.

## Implementation slices
- [x] 1. Commit immutable scan population and 12-date target,
      no outcomes and no source claims.
- [x] 2. Add bounded, read-only daily catalog scanner and
      offline fail-closed tests.
- [x] 3. Audit true GitHub official-source outputs including
      all 90 dates and unique SPOT/FUTURES availability.
- [x] 4. Freeze verified 12-date selection from historical
      source capacity and create operator-controlled preparation
      handoff.
- [ ] 5. Governed acquisition / review PR / main CI (requires distinct human authorization).
      Do not silently activate thresholds.

## Verification matrix
| Gate | Expected evidence | Status |
|---|---|---|
| Scan preregistration | fixed input before source GET | Verified: PR #96 |
| Source calendar | all 90 dates classified | Verified: run 39038071038; family-level only |
| Exit source | exact verified existing 2025Q2 L2 | Verified: 39029586457 one-source-probe only |
| Selection | 12-date, source bound, before PnL | PR #101 approved, merged 4acf3e9, main CI 39050288482 success |
| Code, API, E2E, static | final head CI | Pending |
| Historical smoke | fixed pinned baseline unchanged | Pending |

## Decision gates
No question is needed to run a read-only, precommitted source
calendar scan. Separate human authorization remains necessary
for operator-controlled acquisition dispatch and governed
promotion PR merge. If complete/independent source population
cannot be proved, do not force a selection or invent availability.

## 2026-10-17 fixed source calendar read-only implementation

[PR #96](https://github.com/pkking/future-opportunity/pull/96)
froze the exact 90-calendar-day 2025Q2 source
population **before** this scanner was authored or executed:
`docs/historical-acquisition-plans/cash-2025q2-source-capacity-study-v1.json`.
This PR adds an official OKX module-4 source-only
`probe-cash-2025q2-source-calendar.yml` workflow:
180 bounded date/source requests, daily raw official response
bodies and separate SHA-256, explicit API error/missing/ambiguous
labels, and a full 90-day report with one-to-one date coverage
checks. No historical member (250627) existence is inferred
from FUTURES family-chain archive catalog; results remain
`contract_member_inside_futures_archive_verified=false`.
No strategy outcome inspected, no selected historical sample
declared, and no promotion or live trade authorized.

The next gate is the exact real official-source run ZIP, all
180 response hashes and source calendar coverage, followed by
separately frozen availability-based date selection. The one
source-only June 12 L2 example remains strictly research-only
and not a selected profitable case.

## 2026-10-17 independent full-calendar artifact audit checkpoint

- PR #97 merged as `1734dae3a8c9ce8d70208a18d17a91b73ba20f22`; final-head CI run [39030211155](https://github.com/pkking/future-opportunity/actions/runs/39030211155) and Historical Smoke run [39030211154](https://github.com/pkking/future-opportunity/actions/runs/39030211154) both succeeded. Post-merge main CI run [39038070997](https://github.com/pkking/future-opportunity/actions/runs/39038070997) succeeded.
- First official source-population run [39030128781](https://github.com/pkking/future-opportunity/actions/runs/39030128781), artifact **12100067444**, ZIP SHA-256 `dba051d06449e1ca0251e65e67a8f44754e177fbe82ac5bcd5b3e8b7593e5307`. Downloaded archive contained exactly two JSON reports, 90 ordered dates, 180 raw API responses, 180 independently recomputed raw hashes matching the summaries, 90/90 paired catalog archive records, and zero API-error dates. Official FUTURES entries are **family-chain**, not `BTC-USDT-250627` members.
- Post-merge source run [39038071038](https://github.com/pkking/future-opportunity/actions/runs/39038071038), artifact **12103210971**, ZIP SHA-256 `1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae`; independently verified the same 90 dates/180 raw API responses and non-promotion flags.
- Add a reusable **offline, fail-closed** audit command and tests for the exact Actions ZIP. Neither result proves per-day FUTURES contract member existence, orderbook snapshot completeness, trading qualification, sample selection, economics or promotion. Do not move the Issue to COMPLETED.

### Audit verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Calendar preregistration before source GET | PR #96 merged before scan | Verified |
| Immutable Actions ZIP provenance | Two exact run/artifact pairs and SHA-256 above | Verified |
| Raw HTTP catalog responses and 90 day reports | Independent recomputation of all 180 hashes and dated rows | Verified |
| Unique SPOT/FUTURES family archives for every date | 90 paired official catalogs; 0 API-error days | Verified (catalog only) |
| `BTC-USDT-250627` member across eligible dates | Requires chain archive member verification, not an API catalog guess | UNASSESSED |
| Complete 00:15 L2 books across frozen selected dates | Must be verified only after independently frozen date sample | UNASSESSED |
| Historical acquisition / corpus promotion | Separate operator-controlled reviewed PR | NOT APPROVED |

### New independently replayable audit slice

- [x] Persist `scripts/audit_cash_2025q2_source_calendar.py` with ZIP digest, raw query identity, response SHA, date, archive URL and report-vs-source consistency checks.
- [x] Add offline positive and corruption/approval-escalation negative tests (11 cases locally passed using `python -m pytest -q`; await final-head CI).
- [x] PR #98 final-head CI/Smoke and post-merge main CI succeeded; main SHA `9b00e900bf22b09216297daacf6148ba43aaf6b8`.
- [x] Complete bounded exact-contract member availability enumeration, all nine archive artifacts audited, preserving 90/90 exact-contract identities without evaluating returns.

## 2026-10-17 next execution slice: bounded exact-contract source population

- Issue: #95; active task branch `agent/cash-2025q2-member-population`. Exact main starting SHA `9b00e900bf22b09216297daacf6148ba43aaf6b8`.
- Facts: PR #97 and #98 merged; CI and Historical Smoke green. The immutable 90-date daily source-calendar ZIP is from main run **39038071038**, artifact **12103210971**, SHA-256 `1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae`.
- Objective: prove whether the exact `BTC-USDT-250627` member is present for **every** preregistered 2025-03-29..2025-06-26 date. Family-level archive presence is insufficient.
- Implement offline-replayable per-day archive member verifier with SHA-256 of downloaded official archive, archive member names, exact date/future validation, explicit `identity_verified` / `unavailable` / `error` statuses; build no quotes/returns.
- Split complete registered calendar into nine immutable contiguous 10-day batches; all 90 days must appear exactly once. Workflow is read-only `actions: read` + `contents: read`, can run on its dedicated agent branch to capture source evidence; no trigger on main.
- Use existing source ZIP auditor before every batch, exact run/artifact/digest pinning; limit individual downloads to 512MiB and bounded HTTP read time. Raw compressed files are transient and never committed.
- Tests: tar member parsing, wrong contract, different date, bad/missing TAR, oversized archive, tampered selection and 10-day partition; final PR static/code/API/E2E/Historical Smoke.
- Governance: selection remains frozen **false**, zero opportunity or PnL computations, sample count stays 54 Cash/32 Funding; any sample freeze is a separately reviewed PR based only on **fully verified** available contract-member dates. If any date is an HTTP/parse error, no sample selection or promotion.
- Resume checkpoint: create worker/script, workflow and offline tests, submit PR and run source-only batch workflow; inspect every batch Actions artifact and independently verify reported SHA/dates/member names before proposing a source-grounded selection.

## 2026-10-17 complete exact-contract source evidence (outcome blind)

- PR #99 [merged](https://github.com/pkking/future-opportunity/pull/99) at `7196746611da611f6a410ed0ae79163f8c6a578e`; final-head CI [39045499828](https://github.com/pkking/future-opportunity/actions/runs/39045499828) and Historical Smoke [39045499795](https://github.com/pkking/future-opportunity/actions/runs/39045499795) passed; postmerge main CI [39045729737](https://github.com/pkking/future-opportunity/actions/runs/39045729737) passed.
- Official [90-date exact contract source run 39045070860](https://github.com/pkking/future-opportunity/actions/runs/39045070860) completed successfully on source workflow SHA `b5980b907d8e698906ef4fe49de18fba6b451cf6`. All 9/9 10-day jobs succeeded and published one Actions artifact each. Compressed source archive bytes are **not** committed.
- Exact 9-artifact source run ID, artifact IDs, ZIP SHA-256 digests: `docs/research/cash-2025q2-member-artifacts-manifest-v1.json` (immutable file SHA-256 `88669cef7860f616b0483723c07edea82040bd86033a61bcc55a51bf4eb41b72`).
- Full independent offline audit of all nine ZIPs against frozen 90-date 180-response official source ZIP (2025-03-29..06-26), exact member names, dated official archive URLs, per-day compressed archive SHA-256, no duplicates, counts, non-trading flags: `docs/research/cash-2025q2-member-population-audit-v1.json` (SHA-256 `6030971d2060c603d6ce78222d68e0ea1f7a040f0c099b108fbf88247a298c6c`).
- Results: **90/90** dates contain unique exact `BTC-USDT-250627` `.data` members; 0 unavailable, 0 ambiguous, 0 source errors. **Still source member only**: only the separately verified exploratory 2025-06-12 entry/2025-06-26 exit has audited canonical 00:15 L2. No frozen strategy selection, outcomes or corpus promotion.
- Chronological eligibility: the source population includes `2025-06-26` to prove the fixed exit book; entry `2025-06-26T00:15:00Z` would equal the required exit and violate `entry < exit < expiry`. Therefore the eligible entry-day population is **89** dates after excluding `2025-06-26` on non-economic grounds. This exclusion must be applied to `availability-even-rank-v1` **before** freezing N=12 in an independently reviewed, separate PR.
- Complete membership doesn't prove sampled historical L2, margin safety, venue exposure, returns, economic approval or live-trading readiness. Keep Cash 54 / Funding 32 pinned baseline.

## 2026-10-17 prospective N=12 selection registration (separate review gate)

- The prior source-bound evidence-only PR #100 merged on `c0d03775edc6f8ef86e8d537d5d1b18c9e4c3184`, postmerge CI [39046454543](https://github.com/pkking/future-opportunity/actions/runs/39046454543) succeeded.
- Source reality: 90/90 FUTURES family archives contain exact BTC-USDT-250627 member, no unverified days; all 9 official source ZIP digests pinned. Exact entry-date eligibility is **89** because the fixed 2025-06-26T00:15:00Z exit is not a strict earlier entry timestamp.
- Existing accepted algorithm `availability-even-rank-v1` with start 2025-03-29, end 2025-06-26, non-economic `excluded_market_dates=[2025-06-26]`, `sample_size=12`, produces selected date SHA-256 `9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37`. This is **prospective**, before any sampled economics.
- A *separate independently reviewed PR* shall pin `docs/historical-acquisition-plans/cash-2025q2-12day-preregistration-v1.json` and provide a reusable fail-closed validator/tests. Do not mark `selected dates frozen` or open acquisition until that review PR is merged.
- [x] Record exact source IDs, SHA, N=12 selected dates, exit-day temporal exclusion in immutable proposed registration.
- [x] Implement fail-closed deterministic replay validator and offline negative tests for input-schema drift, no pinned-day overlap, and all 12 entries strictly before exit; CI pending.
- [x] Initial PR #101 code/API/E2E/static/Agent plan CI [39046731182](https://github.com/pkking/future-opportunity/actions/runs/39046731182) and Historical Smoke [39046731185](https://github.com/pkking/future-opportunity/actions/runs/39046731185) green on `866ac25b0a8d6cf7d2903df97899b4c2aad504e0`; final checkpoint commit must be rerun.
- [ ] Obtain separate independent **human** preregistration review before merging PR #101.
- [ ] After approved freeze only: operator-controlled selected-case full 4-leg L2 acquisition (not authorized by this PR).

### Human review / decision gate

**Decision:** Whether to approve the source-bound, outcome-blind exact 12-date selection in [PR #101](https://github.com/pkking/future-opportunity/pull/101), with 2025-06-26 excluded from entry eligibility because entry_at would equal fixed exit_at.

**Options:** (A) approve this immutable selection and permit reviewed PR merge, after which controlled per-date source preparation can start under the separate acquisition workflow; (B) request corrections with explicit evidence; (C) decline expanding the cohort. No selection replacement based on observed profitability is permitted.

**Evidence:** 90/90 exact contract archive members independently verified; all nine source ZIP SHA digests and 90-day source audit pinned in PR #100; 89 strictly earlier entry candidate dates; existing `availability-even-rank-v1`, 12 proposed dates, evidence SHA `9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37`; PR #101 offline mutation tests and full CI/Smoke.

**Recommendation:** Approve the prospective date selection after independent review; preserve all negative future cases, and do not infer any return/profitability before full selected-day four-book acquisition.

**Resume after decision:** approved PR merge → main CI → operator-controlled prepare/Actuals/Compact for the exact selected dates → audit all canonical L2 sources and rejects → separate corpus promotion PR and review. No live orders or economics gates.

## 2026-10-18 user approval and next read-only control slice

- Explicit user approval obtained for the twelve exactly pre-registered dates and PR #101 merger; approval **only** covers date freeze and merge, not acquisition, promotion, economics gate or live trading.
- PR #101 merged on main: `4acf3e945769d49dd001b686ad1cd114f5bb32f8`. Postmerge main [CI 39050288482](https://github.com/pkking/future-opportunity/actions/runs/39050288482) succeeded.
- New step: reuse accepted availability selection and existing `validate_cash_2025q2_preregistration.py` to emit a reproducible **selection-control artifact** only from the main-merged frozen registry; record immutable PR reference, source member/catalog run IDs and content SHA-256, and strict `sample_selection_frozen=true` while keeping `acquisition_approved=false`, `promotion_approved=false`, `economic_outcomes_evaluated=false`.
- Add a `push: main` and manually repeatable read-only workflow for selection evidence; no source archive downloads, no PnL, no data mutation.
- Implemented new `scripts/freeze_cash_2025q2_selection.py` (reuses existing strict validator), `tests/test_cash_2025q2_selection_control.py`, `.github/workflows/freeze-cash-2025q2-selection.yml`; source-only control reports exactly 12 frozen entries and all acquisition/promotion/economics flags false. PR CI and main artifact pending.
- Obtain exact main-run artifact ID and Actions digest, then prepare a **separate** strictly validated Cash 2025Q2 acquisition control manifest using existing Q3/Q4 mechanisms.
- Operator-controlled full L2 acquisition dispatch remains **BLOCKED_DECISION** pending explicit separate human authorization. Preparation work may proceed without triggering the download job. No sample replacement.
- Acceptance: CI/Smoke final-head+main, frozen 12 dates, source SHA match, negative tests, artifact run SHA and digest observed; no live trade or corpus promotion.

## 2026-10-18 operator-controlled Q2 acquisition handoff (not authorized)

- PR #102 merged as `e37120b326d578a2d10ae00769d7d7d5cdfbb6c7`; [main CI 39050630835](https://github.com/pkking/future-opportunity/actions/runs/39050630835) succeeded.
- Read-only [selection-control Run 39050630845](https://github.com/pkking/future-opportunity/actions/runs/39050630845) succeeded on main SHA `e37120b326d578a2d10ae00769d7d7d5cdfbb6c7`: artifact **12106828444**, Actions ZIP SHA256 `8f29acfacaa71d1e5a59c0a0b28e28eef43257e6613c5cfa4806fea4740c9e36`. Independently downloaded/verified exact ZIP SHA256 and sole control.json, 12 approved days, registry content SHA `0aff5c24a439a12117b6268aac6b57e8de4f6092fd8f11f54fb5060f47a1ccbd`, all non-acquisition flags.
- This next implementation slice builds **only a deterministic operator manifest, offline validator and review handoff** using the existing Q3/Q4 approved `HistoricalAcquisitionManifest` / availability-selection provenance / preparation workflows. No new trading system, no economic selection, no exchange access, no automatic acquisition.
- Freeze `docs/historical-acquisition-plans/cash-2025q2-12day-wave-001.json` containing 12 unchanged cases and immutable selection-control run/artifact digest above, with `funding=null`. Error if manifest source digest/date/release deviates from approved registry.
- Added `scripts/validate_cash_2025q2_preparation_handoff.py` and `tests/test_cash_2025q2_preparation_handoff.py`; offline positive, changed FUTURES ID and changed Actions artifact digest checks. Remaining negative coverage follows CI feedback.
- Implemented manual-only `.github/workflows/prepare-cash-2025q2-wave.yml`, exact authorization phrase guard, reuses existing `acquire-historical-campaign.yml` only when an operator invokes it. Wrapper only audits 12x3 artifact **names/digests presence**, not data contents. A merge of preparation *code* is not authorization to invoke the workflow.
- Gate: user-approved 12-date freeze is recorded. Next material authorization **still needed**: dispatch 12 full 4-leg SPOT+FUTURES historical 00:15 orderbook downloads, per-case actuals/compact fixture artifacts. Promotion and live trading remain separate/unapproved.
- Upon any failure, preserve cases/negative observations and exact status; do not pick replacements using outcomes.

## 2026-10-18 operator-control implementation and authorization gate

- Explicit approval for **date preregistration** did not authorize downloaded L2 source acquisition. The 12 selected dates were frozen by PR #101; no market economic selection was performed.
- PR [#102](https://github.com/pkking/future-opportunity/pull/102) merged at `e37120b326d578a2d10ae00769d7d7d5cdfbb6c7`, postmerge [CI 39050630835](https://github.com/pkking/future-opportunity/actions/runs/39050630835) passed. Its read-only [selection-control Run 39050630845](https://github.com/pkking/future-opportunity/actions/runs/39050630845), artifact **12106828444** (`sha256:8f29acfacaa71d1e5a59c0a0b28e28eef43257e6613c5cfa4806fea4740c9e36`) was independently downloaded and inspected (exact N=12, PR #101 reference, registered selection SHA and all acquisition/promotion gates false).
- PR [#103](https://github.com/pkking/future-opportunity/pull/103) merged at `fc0473cdd47e00316c766796f4cd5143f5196594`, final-head [CI 39051211960](https://github.com/pkking/future-opportunity/actions/runs/39051211960) and [Historical Smoke 39051212068](https://github.com/pkking/future-opportunity/actions/runs/39051212068) passed. Postmerge [main CI 39051301876](https://github.com/pkking/future-opportunity/actions/runs/39051301876) passed. The first CI failure [39051138749](https://github.com/pkking/future-opportunity/actions/runs/39051138749) was a test import path, fixed at `176f88c74fecc82ffc00fd5a78bb75b73c32a5c2` before final gates.
- The exact 12-case offline manifest: `docs/historical-acquisition-plans/cash-2025q2-12day-wave-001.json`; fail-closed validator: `scripts/validate_cash_2025q2_preparation_handoff.py`; manual-only `workflow_dispatch` wrapper: `.github/workflows/prepare-cash-2025q2-wave.yml` (requires distinct operator authorization input; no push/schedule/automatic invocation).
- The wrapper delegates to existing `acquire-historical-campaign.yml`, preparing exactly 12 Cash cases, with `funding=null`, immutable source selection and 2025-06-26T00:15Z close. Each case's existing preparation downloads entry/exit SPOT/FUTURES, writes normalized canonical books, evaluates actuals and uploads prepared/compact/actuals artifacts. The repeated exit-source downloads across cases are an implementation cost, **not** a reason to alter frozen dates.
- This phase only implements future preparation **capacity**. No workflow was dispatched, no selected-day L2 completeness established, no sampled economics assessed, no pinned corpus mutated, no distribution Stage-2 gate activated, and no authenticated live trading enabled. Existing Cash 54 / Funding 32 counts unchanged.

### Decision required before proceeding

**Decision:** authorize or reject **one manually initiated, read-only, historical source preparation run** for exactly the frozen 12 cases. Separate from the already approved *date freeze*. It fetches historical L2 SPOT and FUTURES official archives and calculates paper historical actuals, then uploads bounded, auditable evidence. It does not place market orders, commit new corpus fixtures or promote strategies.

**Options:** (A) authorize the bounded 12-case acquisition workflow with existing immutable manifest, or (B) defer/source-optimize/decline. A failure/negative case is retained with its source status rather than replaced.

**Evidence:** PR #101 + #102 + #103 and final-head/main CI URLs above; exact source artifact SHA and fixed registration SHA `9bd08184a3a0c2487ba57087effdf0e8231db45fb4bf10226290627ed2990b37`.

**Recommendation:** authorize one controlled **research-only** run. Review complete per-case raw SHA/normalized 00:15 L2/actuals/compact artifacts first, and only later separately decide whether to promote a reviewed historical corpus PR.

**Resume after authorization:** an operator runs `prepare-cash-2025q2-wave.yml` with required manual authorization input; inspect its source artifacts, preserve all 12 cases including any failed/missing/negative results. Do not automatically trigger separate promotion or enable live trading.

## 2026-10-17 22:37 UTC — independent source acquisition authorization granted

- User explicitly approved **one** manually initiated research-only 12-case Cash 2025Q2 historical L2 acquisition run, separately from the prior PR #101 *date freeze* approval. The exact scope and source evidence are persisted in [Issue #95, approval comment](https://github.com/pkking/future-opportunity/issues/95#issuecomment-6242443010).
- Current verified main baseline before dispatch: `2c6ed2c1607710fbf162efb30c35001ba815edde`; prior CI [39051482604](https://github.com/pkking/future-opportunity/actions/runs/39051482604) successful. The `prepare-cash-2025q2-wave.yml` workflow retains `workflow_dispatch` only (no push or schedule) and requires an independent operator authorization input.
- **Authorized exact invocation:** `gh workflow run prepare-cash-2025q2-wave.yml --repo pkking/future-opportunity --ref main -f operator_authorization=APPROVE-CASH-2025Q2-N12-SOURCE-PREPARATION`.
- User-approved scope: exact pinned 12 dates; retrieve/normalize entry+exit SPOT/FUTURES books and paper actuals; upload full prepared/compact/actuals/failed-case diagnostics without promoting or changing corpus. No economic-target activation, live trading, date replacements or automatic retries.
- **Execution status: APPROVED / NOT DISPATCHED.** Connected GitHub tool exposes workflow reads and reruns, but no manual `workflow_dispatch` action. Local execution environment has no authenticated `gh` CLI. Thus an operator must execute the quoted command or use the GitHub Actions **Run workflow** form. This is now an operational/evidence dependency, **not** a missing authorization or an invitation to ask for approval again.
- After operator trigger: discover a new `workflow_dispatch` run with exact workflow name, verify `head_sha` and 12-case manifest source, audit all 12 per-case outcomes including failures, compare all 36 expected prepared/compact/actuals artifact names, original SHA/provenance and L2 book consistency. Preserve negative and rejected results; no corpus promotion until separately approved.
- Status remains `BLOCKED_EVIDENCE` until the authorized run ID and artifacts exist; the open Issue #95 and this active plan retain ownership.

## 2026-10-17 23:28 UTC initial authorized run: source archive size guard

- User-authorized, manually triggered [run 39079100154](https://github.com/pkking/future-opportunity/actions/runs/39079100154), expected main `3b2c9660bf0b22827a2c35e5d80b9619f481281a`. Authorization/resolved 12-case controls succeeded; exact original Actions ZIP hashes and 12 selection identities independently audited.
- First failing case: 2025-04-09 [job 117532314621](https://github.com/pkking/future-opportunity/actions/runs/39079100154), error `RuntimeError: raw archive exceeded 600 MiB`. No canonical L2 or Actuals for this date. This is an upload/download capacity boundary, **not** a rejected opportunity or negative return.
- Verified against immutable official module-4 SPOT catalog run 39038071038 artifact 12103210971 SHA256 `1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae`: 2025-04-09 **SPOT 768.01 MB**, FUTURES 350.2 MB. All other 11 selected entry-day SPOT/FUTURES catalog sizes and the fixed 2025-06-26 exit source sizes are under 600 MB. Official declared values do not prove actual compressed sizes or valid L2.
- Remediation is a scoped, **bounded** technical config change: allow the Q2 manually authorized wrapper to forward a 1024 MiB **per-archive** cap through existing reusable acquisition/fixture workflows; preserve other callers' 600 MiB default, check bounds fail-closed, add regression tests. Never disable bounds, rewrite date sampling, or classify missing data as negative returns. 1024 MiB is a preparation capacity limit, not model evidence.
- The **one** operator authorization covered run 39079100154, not a repeat. Source acquisition rerun (after any code fix) must have a distinct explicit human approval and manual trigger. No automatic reruns.
- Existing negative evidence and successful case artifacts remain immutable for this run. Wait for all dates; audit every case separately.

- Implemented Q2-only `cash_max_raw_mb: 1024` through the existing reusable acquisition/Cash fixture workflows, preserving **600 MiB default** for all other callers. The fixture step only accepts `600|1024`. Added `tests/test_cash_q2_source_budget.py` for configuration guards and mocked bounded HTTP streaming/source SHA. PR CI/Smoke pending.

## 2026-10-18 complete first acquisition audit and bounded one-case recovery implementation

- First user-authorized Q2 [run 39079100154](https://github.com/pkking/future-opportunity/actions/runs/39079100154) **completed failure** at immutable main SHA `3b2c9660bf0b22827a2c35e5d80b9619f481281a`. The only failed case is `2025-04-09` (SPOT daily archive 768.01 MB vs hard limit 600 MiB), so its book and historical outcome remain **UNASSESSED**, not zero or unqualified.
- Independently downloaded the remaining **33 ZIPs** (Prepared/Compact/Actuals × 11 dates), checked each against GitHub Actions 35-item pre-summary inventory (33 case artifacts + two immutable controls), original ZIP SHA, exact 4 SPOT/FUTURES books and `.data` identifiers, full source/selection hashes, canonical JSONL SHA, Compact parent hashes and Actuals case IDs. Eight cases qualified, three **valid unqualified** on 2025-06-07, 06-14, 06-22 (`expected_net_return_not_positive`); max canonical source age 164 ms. Risk states MarginSafety/VenueExposure remain unassessed. Reproducible independent audit local JSON SHA-256 `3e45a877c81f705ac25f14aa03c5fc93f1a1ced34016762a18e77022b5a91e9d`; source IDs and results preserved in [Issue #95 comment](https://github.com/pkking/future-opportunity/issues/95#issuecomment-6243260025).
- The failed original run's artifact-summary ZIP **12118472292** SHA256 `4cd7e6cf98e0e7ba13074b782a61dbe04e8b35427dc7516bf98c553af8d7f832` preserves the original source run's artifact inventory and `acquisition_job_result=failure`. The original run itself lists 36 artifacts including this final summary.
- Root-cause remediation PR [#106](https://github.com/pkking/future-opportunity/pull/106) merged `83f653205e67ad0a3c71e444796c9319d71769a0`, final-head [CI 39079932015](https://github.com/pkking/future-opportunity/actions/runs/39079932015) / [Historical Smoke 39079932016](https://github.com/pkking/future-opportunity/actions/runs/39079932016), postmerge main [CI 39080050730](https://github.com/pkking/future-opportunity/actions/runs/39080050730) successful. Bounded 1024 MiB is **Q2 only**; other historical prepares remain at 600 MiB, and generic historical workflow-file pushes no longer trigger source acquisition.
- **Next implementation without invoking source:** a new manual-only single-case repair workflow, locked to failed `2025-04-09`, preserves all 12 preregistered selection dates and provenance, 2025-06-26 fixed exit, BTC-USDT-250627 future, and bounded 1024MiB input. Never rerun the eleven finished cases or select replacement dates.
- Implementation staged: `scripts/resolve_cash_q2_failed_source_repair.py` derives only the 2025-04-09 case after validating original 12-case manifest and exact source artifact; `.github/workflows/repair-cash-q2-2025-04-09-source.yml` requires new, distinct human authorization string and forwards 1024MiB Q2-only bounded cap; `tests/test_cash_q2_failed_source_repair.py` covers replay, tampering, manual gate and no promotion. CI / historical smoke pending; **not dispatched**.
- **Decision gate:** the user authorized **one** 12-case run only, now consumed. A subsequent **single 2025-04-09 source retry** requires fresh distinct human approval after this code passes CI. Corpus promotion, Stage-2 return thresholds and live trading remain explicitly unauthorized.

## 2026-10-18 source-only recovery ready, distinct retry approval pending

- PR [#107](https://github.com/pkking/future-opportunity/pull/107) approved code review checks and merged at `9e0782557893393aab21b5c8954f10bc18bdad26`. Final-head [CI 39080352129](https://github.com/pkking/future-opportunity/actions/runs/39080352129) and [Historical Smoke 39080352158](https://github.com/pkking/future-opportunity/actions/runs/39080352158) both successful; postmerge [main CI 39080396793](https://github.com/pkking/future-opportunity/actions/runs/39080396793) successful.
- The manually triggered dedicated wrapper `.github/workflows/repair-cash-q2-2025-04-09-source.yml` and pure, replayable one-case derivation script `scripts/resolve_cash_q2_failed_source_repair.py` both retain original 12 selected dates in provenance; only the known source-cap failure `2025-04-09` is requested for **new source preparation** (BTC-USDT-250627 entry, fixed 2025-06-26T00:15Z exit, 2025-06-27T08Z expiry). Other eleven downloaded cases, including the 3 unqualified negative market observations, remain untouched.
- Distinct operator-authorization input required for the new one-date workflow: `operator_authorization=APPROVE-CASH-2025Q2-2025-04-09-SOURCE-REPAIR`. Bound per-source download size is 1024MiB from PR #106; this does **not** disable the stream cap or create trading permissions.
- First authorized full Q2 run 39079100154 was concluded **failure** (11 cases source-verified; 8 qualified, 3 correctly rejected; 1 2025-04-09 source-size error). Original run and audit evidence captured in [Issue #95 comment](https://github.com/pkking/future-opportunity/issues/95#issuecomment-6243260025), original run Artifact summary SHA `4cd7e6cf98e0e7ba13074b782a61dbe04e8b35427dc7516bf98c553af8d7f832`, full independently recomputed evidence JSON SHA `3e45a877c81f705ac25f14aa03c5fc93f1a1ced34016762a18e77022b5a91e9d`.
- **Status: BLOCKED_DECISION** — the earlier one-run permission has already been consumed. New explicit user consent is required **only to dispatch the one remaining 2025-04-09 read-only source case**, not to change selection. Connected GitHub plugin cannot invoke workflow_dispatch, so an operator must manually trigger it after approval; the agent will verify exact run ID/head/three artifacts and compare the case against the previous 11, then prepare any *separate reviewed* promotion proposal only after new corpus-promotion approval.
- No synthetic returns, no sample replacement, no automatic reruns/promotions, no main corpus change, no Stage-2 policy change, no authenticated trading.

## 2026-10-17 23:53:22 UTC — separate one-date source-repair approval confirmed

- User explicitly authorized **one** additional read-only source preparation **only for 2025-04-09**, separately from the already-consumed first 12-case acquisition authorization. See immutable [Issue #95 approval note](https://github.com/pkking/future-opportunity/issues/95#issuecomment-6243393601).
- The fixed manual recovery entrypoint is `.github/workflows/repair-cash-q2-2025-04-09-source.yml` on main. Verified baseline `6e96a7b0fd2469108112d3d73b4ad9a65129d26c`. The strict input is `operator_authorization=APPROVE-CASH-2025Q2-2025-04-09-SOURCE-REPAIR`.
- **Current execution state: APPROVED, NOT DISPATCHED.** Existing connector is read-only for new workflow dispatch; there were no matching 2025-04-09 single-case workflow runs in the latest manual Actions inventory at the time of approval. This is an operational trigger dependency (`BLOCKED_EVIDENCE`), **not** an outstanding request for human authorization.
- Exact operator-only command:
  `gh workflow run repair-cash-q2-2025-04-09-source.yml --repo pkking/future-opportunity --ref main -f operator_authorization=APPROVE-CASH-2025Q2-2025-04-09-SOURCE-REPAIR`.
- One immutable failed case `2025-04-09T00:15:00+00:00`; BTC-USDT-250627; exit `2025-06-26T00:15:00+00:00`; expiry `2025-06-27T08:00:00+00:00`; Q2-specific 1024 MiB raw-source bound, original 12-date source-pinned registration, no sample substitution or redownload of other 11 cases.
- Once started, fetch the new exact Actions run ID, SHA, authorization control, only one Prepared+Compact+Actuals group, source archive SHA and member proof, book staleness and actuals. Preserve any source failure or negative economic outcome. **No automatic retry, corpus promotion, economics-target activation or trading.**

## 2026-10-18 research cohort completed across original + one-date repair (12/12)

- User-triggered [single-case research source repair 39091438598](https://github.com/pkking/future-opportunity/actions/runs/39091438598) at approved main SHA `6600b330fd8bb78f3385b89227b7c06eb0749c72` **completed success**. The strict operator authorization and original twelve-date sampling provenance were validated, and the job only prepared `2025-04-09`; the other eleven cases were not resampled or re-downloaded.
- Repaired Prepared ZIP Artifact **12122683921**, SHA256 `6f8024bc2c70b437af4ff7c46fcbdea39a4dc4447caf235e016137f8a8c36dfa`; Compact **12122833427**, SHA256 `aa021128f583c610cee18fffd012c78adbff9a7d44acdd8bbd797401a024e63b`; Actuals **12122554018**, SHA256 `b84a8eb3cb04fe7693ba846ed7f8e7c92ce9fd9290648d3e26571a62fb2c1849`. Repair summary **12122987799**, SHA256 `87a3b97e19c22d671d57dde5cafbe9cc7b0cfc0c9c1609e0d373ce857c0245fb`.
- 2025-04-09 **qualified** paper actuals: `realized_net_return=0.003519902531521683005931941343` (+0.3519903%). Canonical 00:15 entry/exit SPOT/FUTURES books all present, SHA-checked with source metadata/archive member IDs and parent ZIP ancestry, max sample staleness **40 ms**. The source-provenance raw archives were *not* independently re-downloaded by the offline auditor; their metadata-reported SHA/bytes were cross-checked for identity. Exit SPOT/FUTURES archive SHA equal the prior 11-case exit source records. MarginSafety / VenueExposure remain **unassessed**.
- **Frozen 12-date cohort complete** across original [run 39079100154](https://github.com/pkking/future-opportunity/actions/runs/39079100154) and repair [run 39091438598](https://github.com/pkking/future-opportunity/actions/runs/39091438598): **36/36** SHA-verified Prepared/Compact/Actuals ZIPs; **9 qualified** and **3 valid unqualified** cases, specifically 2025-06-07/14/22 (`expected_net_return_not_positive`, no realized return, never represented as zero); missing source **0**; max L2 staleness **164 ms**.
- Offline **complete 12-case independent audit JSON SHA256** `00ac19aa623467d0a1985c1ca9bf7f52a0e0ae46cd6a72374a16d6c68f80901c` (generated conversation artifact), and in-repo machine-readable, audit-only 36-Artifact index at `docs/historical-acquisition-plans/cash-2025q2-12day-cross-run-audit-v1.json` with regression tests. GitHub Issue [#95 completed cohort audit note](https://github.com/pkking/future-opportunity/issues/95#issuecomment-6244944016) preserves source IDs, original and repaired run SHA, per-file SHA and risk caveats.
- Among the nine **executed and qualified paper scenarios only**, conditional mean realized net return `0.00225050806729944181109750239` (+0.22505%), not a 12-date unconditional expectation, not live profitability. These date samples all share one BTC future expiry and a common 2025-06-26 pre-expiry close: they are *not* twelve independent expiries. Their outcomes may be correlated.
- Existing pinned corpus stays **Cash 54 / Funding 32**: no corpus promotion, Stage-2 economic target/gate changes, risk readiness claims, or trading. The two separate operator source permissions have both been exercised and are no longer outstanding.
- **NEXT DISTINCT HUMAN DECISION (BLOCKED_DECISION):** whether to create a separately reviewed **research-corpus promotion** of the complete 12-date Q2 evidence including three rejected observations, without relaxing strategy/risk gates, changing existing corpus baselines silently, or enabling live trading; or defer promotion and study additional contract-expiry cohorts. Do not treat preparation completion as promotion approval.

## Resume from here
Original Q2 run 39079100154 (11 successes, one raw-archive source cap failure) and the separately approved source-only repair run 39091438598 (missing 2025-04-09 success) together yield **12/12 source-audited cases, 36/36 SHA-verified ZIP artifacts, nine qualified, three genuine unqualified**, no missing source. Complete offline audit JSON SHA256 `00ac19aa623467d0a1985c1ca9bf7f52a0e0ae46cd6a72374a16d6c68f80901c`; inspect the in-repo research-only audit index and Issue #95 comment 6244944016 for all immutable IDs. Status is **BLOCKED_DECISION** on whether to promote research evidence through an independently reviewed corpus change. No user permission exists for corpus promotion, economics-gate activation or live trading. Preserve Cash 54 / Funding 32 pinned baseline and the three unqualified cases.

## Completion
Source population and fixed 12-date research acquisition verified complete. Separate corpus-promotion decision and risk/economics readiness remain pending.
