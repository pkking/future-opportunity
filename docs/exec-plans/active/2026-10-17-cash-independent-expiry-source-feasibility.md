# Cash-and-Carry independent futures expiry source feasibility

Issue: #86
Status: VERIFYING
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
- [ ] Tests fail closed on stale/cross-contract metadata,
      mistaken duplicate expiry, missing/ambiguous archive member,
      expiry ordering, absent SPOT, malformed data and partial
      source responses. Preserve frozen original probe tests.
- [x] New source probe never invokes strategy returns or existing
      promotion workflows. Only a later, separately reviewed
      selection freeze may propose acquisition.
- [ ] PR final-head CI, API/E2E, Agent plan integrity and pinned
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
- [ ] 4. Validate in final-head CI; collect one real source run
      and publish bounded raw-archive evidence/limitations.
- [ ] 5. If at least one **independent** expiry shows verified
      entry/exit availability, create a new operator-approved
      pre-registration Issue/PR, not instant promotion.

## Verification matrix
| Gate | Evidence | Status |
|---|---|---|
| Baseline | Four expiry cohorts, Cash 54 | Previously verified |
| Pre-registration | Fixed dates/instruments before queries | Pending |
| Probe tests | Coverage/identity/fail-closed negative tests | Pending |
| Source inspection | 39029044125; ZIP digests checked; 2025q2 2/2 futures members, 2026q3 unavailable | Catalog identity verified only; L2 UNASSESSED |
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

## Resume from here
Catalog-only source inspection is complete (run 39029044125): prioritize 2025q2 for **separate, source-only 00:15 four-leg L2** verification; 2026q3 remains unavailable. Validate this implementation PR's final-head CI, and do not infer L2 or acquisition readiness from the catalog scan. Check main branch, current Cash expiry sets, and all available
OKX historical source-probe helpers. Audit existing archival
catalog/retention behavior and the ability to inspect truly
new expiration contracts. Write the new fixed candidate
cohort list **before** source requests or strategy-result inspection.
Keep success, incomplete and unavailable probes distinct.
Plan code changes and negative tests before extending
read-only workflow; do not dispatch old 2025 Q3/Q4 as
if that were a new independent expiry.

## Completion
Pending real independent expiry source verification and
subsequent reviewed workflow updates.
