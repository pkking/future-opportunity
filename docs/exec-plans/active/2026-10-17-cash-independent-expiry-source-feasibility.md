# Cash-and-Carry independent futures expiry source feasibility

Issue: #86
Status: PLANNING
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
- [ ] Derive the exact four *already pinned* Cash expiry IDs
      from the validated corpus; exclude these from new-cohort
      discovery and verify uniqueness of candidate expiry IDs.
- [ ] Pre-register a **fixed set of potential expiry/entry/exit
      source-probe targets** before fetching official archives;
      classify as unassessed, not available, until source proves it.
- [ ] Generalize the hardcoded Q3/Q4 probe to separately configured
      target cohorts while retaining original read-only behavior,
      strict identity/date/expiry validation and bounded downloads.
- [ ] Emit machine-readable source report for each candidate:
      official catalog identity, spot/futures archive availability
      and SHA-256, chain member match, entry and pre-expiry exit
      sample readiness, and explicit missing/invalid reasons.
- [ ] Tests fail closed on stale/cross-contract metadata,
      mistaken duplicate expiry, missing/ambiguous archive member,
      expiry ordering, absent SPOT, malformed data and partial
      source responses. Preserve frozen original probe tests.
- [ ] New source probe never invokes strategy returns or existing
      promotion workflows. Only a later, separately reviewed
      selection freeze may propose acquisition.
- [ ] PR final-head CI, API/E2E, Agent plan integrity and pinned
      Historical Smoke green. Exact official-source probe run,
      raw digests and source scope must be inspected before
      declaring an additional cohort feasible.

## Implementation slices
- [ ] 1. Inventory current 54 Cash fixtures by expiry and
      reconcile four true maturity cohorts.
- [ ] 2. Freeze new candidate expiry/date probe design without
      inspecting outcomes, and review source retention boundaries.
- [ ] 3. Implement a parameterized read-only source catalog probe,
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
| Source inspection | Exact Actions Run, digests, L2 readiness | Unassessed |
| Static/code/API/E2E | Final-head CI | Pending |
| Pinned historical smoke | No changes to corpus or strategy semantics | Pending |

## Decision gates
If official OKX archives cannot substantiate another cohort,
record a source-limited conclusion without relaxing criteria.
Only a future proposal selecting actually evidenced sample
dates is subject to the usual explicit human/operator
acquisition and promotion controls. Existing ADR-0009
decision-quality approval is **not** an economics approval.

## Resume from here
Check main branch, current Cash expiry sets, and all available
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
