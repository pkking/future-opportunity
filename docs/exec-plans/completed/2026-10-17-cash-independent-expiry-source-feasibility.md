# Cash-and-Carry independent futures expiry source feasibility

Issue: #86
Status: COMPLETED
Owner: agent
Started: 2026-10-17

## Objective
Find actual source-backed historical order books for **additional
independent expiry contracts**, rather than treating multiple
correlated entry dates within one futures expiry as independent
market outcomes. Validate source feasibility before any new
pre-registered Cash history acquisition.

## User-facing problem and existing evidence
Main historical corpus contains 54 Cash distinct entry days after
the approved Q3/Q4 2025 promotion, across four BTC-USDT FUTURES
expiries: Sep 26 2025, Dec 26 2025, Mar 27 2026,
Jun 26 2026. The preferred 90-day coverage is 36 days short,
but additional dates on the same expiry are highly correlated
in basis/exit regime and must not be treated as independent
maturity trials.

- Source-grounded Q3/Q4 2025: archive runs 39016938121 and
  39018358844, 24 unchanged frozen days; planner 39020272173,
  governed promotion 39021366976, PR #82 main
  ad4790c0c7ec785eb2de9d53704e154515451001.
- `scripts/probe_cash_prior_expiries.py` and
  `cash_expiry_probe.py` freeze four 2025 Sep/Dec probe dates,
  both contracts **already in the pinned corpus**. Rerunning
  this script alone cannot discover a fifth cohort.
- Official OKX module-4 FUTURES L2 archival catalog plus SPOT
  entry/exit evidence is required. Presence in a catalog is
  not proof of a sampled, complete canonical 00:15 book.
- Read `docs/research/stage2-multi-expiry-regime-sampling-protocol.md`
  and `docs/research/cash-2025-q3-q4-source-preflight.md`.

## Constraints and non-goals
- Research is **read-only**; no direct corpus growth or strategy
  replay-based candidate selection. No automatic dispatch,
  acquisition, promotion, or modification of existing 24 days.
- Do not assume quarterly FUTURES expiry IDs, archive members,
  raw digests or spot/exit coverage without official source evidence.
- Verify chain members, exact futures instrument metadata,
  entry/exit pre-expiry UTC ordering and positive, nonempty
  sampled L2 books. Preserve unsupported, missing or malformed
  source observations explicitly.
- Favor independent expiries over raw day counts.
- No economics thresholds, market-wide frequency estimates,
  risk/account claims or live trading changes.

## Acceptance criteria
- [x] Derive the exact four *already pinned* Cash expiry IDs
      from the validated corpus; exclude these from new-cohort
      discovery and verify uniqueness of candidate expiry IDs.
- [x] Pre-register a **fixed set of potential expiry/entry/exit
      source-probe targets** before fetching official archives;
      classify as unassessed, not available, until source proves it.
- [x] Generalize the hardcoded Q3/Q4 probe to separately configured
      target cohorts while retaining original read-only behavior,
      strict identity/date/expiry validation and bounded downloads.
- [x] Emit machine-readable source report for each candidate:
      official catalog identity, spot/futures archive availability
      and SHA-256, chain member match, entry and pre-expiry exit
      sample readiness, and explicit missing/invalid reasons.
- [x] Tests fail closed on stale/cross-contract metadata,
      mistaken duplicate expiry, missing/ambiguous archive member,
      expiry ordering, absent SPOT, malformed data and partial
      source responses. Preserve frozen original probe tests.
- [x] New source probe never invokes strategy returns or existing
      promotion workflows. Only a later, separately reviewed
      selection freeze may propose acquisition.
- [x] PR final-head CI, API/E2E, Agent plan integrity and pinned
      Historical Smoke green. Exact official-source probe run,
      raw digests and source scope must be inspected before
      declaring an additional cohort feasible.

## Implementation slices
- [x] 1. Inventory current 54 Cash fixtures by expiry and
      reconcile four true maturity cohorts.
- [x] 2. Freeze new candidate expiry/date probe design without
      inspecting outcomes, and review source retention boundaries.
- [x] 3. Implement a parameterized read-only source catalog probe,
      report and deterministic tests; retain hardcoded legacy
      regression behavior.
- [x] 4. Validate in final-head CI; collect one real source run
      and publish bounded raw-archive evidence/limitations.
- [x] 5. If at least one **independent** expiry shows verified
      entry/exit availability, create a new operator-approved
      pre-registration Issue/PR, not instant promotion.

## Verification matrix
| Gate | Evidence | Status |
|---|---|---|
| Baseline | Four expiry cohorts, Cash 54 | Previously verified |
| Pre-registration | Fixed dates/instruments before queries | Pending |
| Probe tests | Coverage/identity/fail-closed negative tests | Pending |
| Source inspection | 39029044125 catalog + 39029586457 four L2 books/4 SHA-256, max age 40ms | VERIFIED for 2025q2 fixed source probe; 2026q3 unavailable |
| Static/code/API/E2E | Final-head CI | Pending |
| Pinned historical smoke | No changes to corpus or strategy semantics | Pending |

## Decision gates
If official OKX archives cannot substantiate another cohort,
record a source-limited conclusion without relaxing criteria.
Only a future proposal selecting actually evidenced sample
dates is subject to the usual explicit human/operator
acquisition and promotion controls. Existing ADR-0009
decision-quality approval is **not** an economics approval.

## 2026-10-17 source registry and bounded read-only probe

[PR #91](https://github.com/pkking/future-opportunity/pull/91)
froze two distinct **unverified** contract probe candidates
before new source requests:
- `BTC-USDT-250627`, entry 2025-06-12, pre-expiry exit
  2025-06-26, expiry 2025-06-27 08:00 UTC.
- `BTC-USDT-260925`, entry 2026-09-11, pre-expiry exit
  2026-09-24, expiry 2026-09-25 08:00 UTC.

Both are distinct from the four already pinned contracts; no
source availability is claimed by pre-registering a FUTURES ID.
This PR implements a bounded, read-only, independent
`probe-cash-independent-expiries.yml` with two separate matrix jobs.
The code independently derives the currently pinned contract
identities from 54 manifest files; checks frozen identity and
entry/exit/expiry ordering; uses exact official FUTURES module-4
chain-archive discovery at entry and exit and SPOT catalog identity
at entry and exit; preserves source errors/missing or ambiguous
contracts; uploads JSON reports even on failure.

**Important limitations:** official chain-member and SPOT
catalog existence do **NOT** establish 00:15 sampled L2
completeness, as-of-entry publication, slippage, strategy
profitability or readiness for acquisition. Both
`complete_l2_sample_verified=false` and
`acquisition_approved=false` remain invariant. Even if every
catalog identity passes, a separately reviewed full orderbook
source/metadata probe and frozen acquisition design are needed.

## 2026-10-17 independently verified official source probe outcome

Source-run [39029044125](https://github.com/pkking/future-opportunity/actions/runs/39029044125)
completed both separate bounded research jobs on workflow commit
`614d331637e461fbee4da92fb09976315b4fb5da`.
Both ZIPs downloaded and SHA-256 matched Actions:

- `2025q2` artifact **12099124504**, ZIP digest
  `5ccb4529c064218881a825f0d2d5021710ce88083425441a6ba53eadff664e15`:
  `BTC-USDT-250627` exact L2 FUTURES archive member present on
  entry 2025-06-12 (downloaded archive SHA-256
  `456c0815f2d9d1ba4a227eeb817866f581fcc5f30e922910b4488a6685112c3c`)
  and exit 2025-06-26 (SHA-256
  `f4daf0c1eabe6e35cab3c2dbf506f5e13bf0a9d08419416496edb342c0759090`).
  Official SPOT module-4 catalog has unique matching entries on
  both days, but their archive bytes were not downloaded by this
  identity-only probe. **Candidate can advance to independent
  00:15 SPOT/FUTURES full L2 verification, NOT acquisition.**
- `2026q3` artifact **12100080117**, ZIP digest
  `75fd1d8e3b17b76ae96747e305f81d7fe8bcffdb613b885066700bec78799c33`:
  for `BTC-USDT-260925`, neither entry 2026-09-11 nor
  exit 2026-09-24 returned a unique matching FUTURES chain
  archive, although SPOT catalog entries existed.
  **This frozen candidate remains unavailable**, not replaced
  based on outcomes or market performance.

Both reports unequivocally record
`complete_l2_sample_verified=false`,
`full_orderbook_source_readiness=unassessed`,
`acquisition_approved=false`, `promotion_approved=false`.
A successful job exit does not imply a usable historical strategy
sample. Neither a fifth pinned cohort nor additional day count
exists yet; Cash remains **54**.

## 2026-10-17 complete frozen 2025Q2 sampled L2 source checkpoint

[Research-only source Run 39029586457](https://github.com/pkking/future-opportunity/actions/runs/39029586457)
ran source-reader components only, deliberately skipping strategy
economic backtest, compact fixture and promotion.

Independently downloaded exact [artifact 12100345294](https://github.com/pkking/future-opportunity/actions/runs/39029586457/artifacts/12100345294),
ZIP SHA-256
`692d51599fa7d08ca75a1975b0bca3ceff4d1815a81b9f476476dcb4f6e172b5`,
and verified that **4/4** normalized JSONL bytes match their
manifest SHA-256, one canonical snapshot per book, all strictly
positive non-crossed top-of-book quotes, original SPOT/FUTURES member
identities, entry/exit sample times and 5000ms freshness.

| Component | Sample at UTC | Book age | Original archive SHA-256 |
|---|---|---:|---|
| entry_spot | 2025-06-12 00:15 | 28ms | `057a3d96f87e299bd7a17854045ba3a5b759ecfe90ec5ca4f0d60fec1590438a` |
| entry_future | 2025-06-12 00:15 | 28ms | `456c0815f2d9d1ba4a227eeb817866f581fcc5f30e922910b4488a6685112c3c` |
| exit_spot | 2025-06-26 00:15 | 10ms | `75168b55b3967cb7536008c3010b6807c12ba7dd2fd85f69547d2e2c1c552f7a` |
| exit_future | 2025-06-26 00:15 | 40ms | `f4daf0c1eabe6e35cab3c2dbf506f5e13bf0a9d08419416496edb342c0759090` |

`BTC-USDT-250627` is now independently source-L2-feasible
for **one fixed source-probe date** not used to select on returns.
It is a newly validated *expiry cohort candidate*, NOT a
new qualified trade or a pinned 2025Q2 cohort.

`research-report.json`: `research_only=true`,
`economics_evaluated=false`,
`historical_sampling_provenance=null`,
`complete_acquisition_provenance=false`,
`acquisition_approved=false`,
`promotion_approved=false`. Consequently no corpus
promotion is possible from this artifact. The fixed
2026Q3 candidate remains catalog-unavailable.

**Next independent phase:** determine the full official source
date population and coverage for `BTC-USDT-250627`, then
pre-register an outcome-blind sample (calendar/availability
rather than observed returns), before running the ordinary
governed preparation and promotion stages.
This work requires its own Issue and acceptance plan;
one source-probe date must not become a cherry-picked
historical trading sample.

## 2026-10-18 independent-expiry follow-through

The separately governed next-stage work requested by this research plan was created as [Issue #95](https://github.com/pkking/future-opportunity/issues/95), completed and closed **after** reviewer/CI controls. The observed new contract expiry `BTC-USDT-250627` passed the original four-book source probe (run 39029586457), then the exact source population study (90/90 archives, only 89 chronologically entry-eligible), independent freeze of 12 blind dates, one approved 12-case source preparation (run 39079100154), separately approved one-date source repair (run 39091438598), 36/36 immutable per-case artifacts, and reviewed offline corpus promotion. Rejected cases were **not** swapped for profitable alternatives.

Research-corpus [PR #113](https://github.com/pkking/future-opportunity/pull/113) merged at main `8e4c528167b5fbc40704782688d8645237441721`. Main [CI 39094900964](https://github.com/pkking/future-opportunity/actions/runs/39094900964) and [Historical Smoke 39094900926](https://github.com/pkking/future-opportunity/actions/runs/39094900926) succeeded. Independent [Issue #95 archival PR #115](https://github.com/pkking/future-opportunity/pull/115) merged at `df236155ee195870c701d6aa49e0dea181857dd8`, archival PR CI 39096383239 and Smoke 39096383146 passed, post-merge main CI 39096464284 succeeded.

The original 2026Q3 candidate was unavailable at the frozen probe time and was **not** silently treated as a sixth settlement. The observable corpus is now Cash **66 market dates across five dated-futures expiries**; Funding remains **32**. Each selected Q2 entry day shares one fixed maturity and exit, so there are not 12 independent expiry events. Source probes and PnL are not equivalent to market-wide returns.

## Resume from here

ARCHIVED: Issue #86's goal of identifying and source-proving at least one new independent Cash expiry and preparing a separately governed acquisition proposal is fulfilled via closed Issue #95. Do not automatically run further Cash source jobs. Future expansion toward preferred 90 days or further maturity diversity requires **a new independently pre-registered research scope** with explicit source provenance and approval gates. Continue the separately active Funding market regime problem under Issue #85.

## Completion

Final commit: 8e4c528167b5fbc40704782688d8645237441721 (independent cohort successfully promoted in PR #113; follow-up archived with #95).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39094900964 (SUCCESS).
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/39094900926 (SUCCESS).
Remaining unassessed items: Preferred Cash 90-day count is 24 short; five settlement cohorts do not imply market-wide profitability or truly independent entry outcomes; as-of-evidence caveats remain; Stage-2 economics gate disabled; MarginSafety and VenueExposure UNASSESSED; no live trading.
