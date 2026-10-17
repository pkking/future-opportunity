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

## Resume from here
PR #101 approved/frozen; PR #102 selection evidence and PR #103 manual acquisition handoff merged with successful main CI. **BLOCKED_DECISION**: obtain explicit, separate operator approval before dispatching the 12-case historical L2 + paper actuals workflow. Do not interpret date selection approval as permission for source acquisition; do not dispatch automatically. Preserve frozen 12 dates, source Artifact 12106828444 and SHA, 54 Cash / 32 Funding pinned corpus.

## Completion
Pending audited 2025Q2 population and reviewed acquisition.
