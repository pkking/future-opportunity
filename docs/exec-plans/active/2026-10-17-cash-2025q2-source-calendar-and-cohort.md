# Cash 2025Q2 additional independent expiry cohort

Issue: #95
Status: VERIFYING
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
- [ ] Independently verify actual source run/Artifact SHA and
      population; validate separate 2025-06-26 exit evidence.
- [ ] Apply strict `availability-even-rank-v1` to verified
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
- [ ] 4. Freeze verified 12-date selection from historical
      source capacity and create operator-controlled preparation
      handoff.
- [ ] 5. Governed acquisition / review PR / main CI.
      Do not silently activate thresholds.

## Verification matrix
| Gate | Expected evidence | Status |
|---|---|---|
| Scan preregistration | fixed input before source GET | Verified: PR #96 |
| Source calendar | all 90 dates classified | Verified: run 39038071038; family-level only |
| Exit source | exact verified existing 2025Q2 L2 | Verified: 39029586457 one-source-probe only |
| Selection | 12-date, source bound, before PnL | Pending |
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
- [ ] Continue bounded contract-member availability enumeration; do not infer 12 eligible selected dates from the 90 family-level catalogs.

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

## Resume from here
The official 90-day family-archive API catalog population and both independently reverified ZIPs are grounded above. PR #98 is merged and its final-head CI/Smoke and main CI succeeded. Next independently enumerate **all 90 FUTURES archive contract members**, using fixed calendar API evidence from run 39038071038 artifact 12103210971 ZIP sha256 `1b9a4adcb7035ca4abb70e5a9f1823dc3a71f5e9849070ce59c493df205b57ae`. Progress via new read-only matrix workflow (10 days/batch, 9 batches, each archived day bounded to 512MiB), publish raw member identity and SHA-256 per day even for unavailable/error outcomes; fail closed on incompleteness. Never select dates until the entire population has been audited. Then proceed to bounded source archive *member-level* evidence for the exact `BTC-USDT-250627` contract across the frozen calendar, logging missing/ambiguous days. Do not freeze N=12 availability-based samples until exact per-date eligibility is verified from source archives. No automatic acquisition, corpus promotion, economics threshold activation, or live trading.

## Completion
Pending audited 2025Q2 population and reviewed acquisition.
