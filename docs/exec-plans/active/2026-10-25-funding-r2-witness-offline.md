# R2 independent Funding witness — offline evidence verifier (no deployment)

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-25
Last checkpoint: 2026-10-25

## Objective

Respond to the user's explicit rejection of Option A as the preferred way forward. Advance **Option B's design and deterministic offline prototype only**, without installing an independent service, contacting OKX or changing historical source admission. Prove what a *candidate* independent observer's sealed original public response and claimed before-entry times would need to satisfy, and fail closed on mismatched time, body, query, clock uncertainty, insufficient completed spot history and source-data divergence.

## Baseline

- main SHA `4f586bceb6ba5c8afe6ff7aff3370f16cb80c6f2`, no open PR as inspected. Previous PRs #150–153 merged, CI successful.
- New immutable `funding-vps-2026-10-25` Release published UTC `2026-10-25T00:00:15Z`; independent release.published audit run #40144972278 successful. This is third GitHub-custody daily observation, **not an approved independently verified OKX public publication receipt**. Legacy scheduled collector failed #40151260280; do not conflate the two independent workflows.
- `docs/research/okx-funding-asof-source-provenance-feasibility.md` defines R0 retrospective, R1 GitHub pre-entry custody, proposed R2 independent real-time observation and absent R3 venue-signed publication. Official OKX V5 public historical Funding endpoint and spot `1Dutc` API responses have no verified venue signature in reviewed contract.
- Existing `validate_preentry_source` validates internal single-day Funding/spot source observations and explicitly refuses as-of authentication. Existing original release audit and source/continuity code establish R1 GitHub custody only.
- Frozen V0 paper-only; accepted ADR-0008 leaves numerical Stage-2 economics disabled. Funding 32 pinned/90 preferred and Cash 66 pinned unchanged.

## Non-goals

- No actual independent observer implementation/deployment; no extra OKX public API call, account credentials, network, GitHub workflow, external storage, clock service, cryptographic key, provider, pricing/license acceptance, historical fixture pin, source admission, numerical threshold, order or trade.
- No R2 verification or independent third-party attestation *claim* from self-reported IDs/timestamps or saved body hash. Structural checks alone cannot establish trusted witness identity or historical timestamp.
- No revisions to V0 domain, Risk, Opportunity, execution or provenance approval decisions.
- Continue existing R1 collection/watch unchanged as operational baseline, but **Option A is not the proposed solution** to the independent upstream evidence gap.

## Acceptance criteria

- [x] Provide B design with explicit separation of observer operator/network, trust anchor, tamper evidence, independent trusted timestamp, 00:15Z deadline, raw body hash, and prior-to-entry bounded clock error.
- [x] Implement manual **offline-only** `scripts/review_funding_witness_draft.py` accepting separate observer declared receipt, exact raw Funding/spot JSON bytes and existing R1 source JSON. No import of network SDK nor REST GET.
- [x] Require schema-exact declared receipt, rigid official fixed GET endpoint/query, separate declared observer and original collector, canonical UTC entry day, strictly ordered and before-entry bounded request/response/receipt times, zero/finite bounded clock error, binary raw body digest checks, duplicate-key detection and bounded file sizes.
- [x] Reuse `validate_preentry_source` and `_funding_index` / `_spot_index` to independently recompute candidate entry features, compare relevant decision-input semantic evidence with the R1 source. Require a full set of settled prior Funding and eight completed prior UTC daily closes, not merely any overlap; mismatched values, missing records, divergent cache returns or future records result in **UNASSESSED** or **CONFLICT** rather than zero opportunity.
- [x] Even when all offline checks pass, emit `CANDIDATE_MATCH_UNATTESTED` (not R2 verified), with `observer_identity_attested=false`, `trusted_time_attested=false`, `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`. If checks fail, no promotion and nonzero CLI exit, preserve external inputs unchanged.
- [x] Offline deterministic tests for same-source candidate, forged same-operator IDs, late reply/receipt, clock uncertainty straddling entry, changed body, duplicate key, wrong endpoint/query, incomplete candles, funding/close disagreement, missing dates and file permissions. No new exchange GET in CI.
- [x] A self-contained design/operating document records why a *future* real independent receipt, third-party trust authority, unique key ownership and policy approval must be separately deployed and reviewed.
- [ ] Final PR-head five CI checks + Historical Smoke PASS, merge, main CI PASS. Archive completed plan separately and leave Issue #85 OPEN/BLOCKED_EVIDENCE.

## Implementation slices

- [x] 1. Add offline candidate source-integrity + temporal/semantic verifier, no SDK/network.
- [x] 2. Add deterministic offline positive/negative tests and design/ops docs.
- [ ] 3. Final-head CI + Historical Smoke, merge and main CI.
- [ ] 4. Complete plan archive and parent Issue checkpoint.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Targeted | `uv run pytest tests/test_funding_witness_draft.py` | pending |
| Static | `uv run ruff check .` | pending |
| Code, API, E2E and Plan | exact final PR head full CI 5/5 | pending |
| Historical | exact final PR head Historical Backtest Smoke | pending |
| Actual R2 | real independent observation, trusted timestamp and authorization | NOT IMPLEMENTED, requires later decision |

## Decision gates

User rejected A as preferred route. This authorizes design/offline preparation under B's previously proposed limited scope, **not** actual collector provisioning, a new storage/provider/trust anchor or a changed historical admission policy. Those choices require separately approved ADR and explicit decision. No reason to stop design/CI for routine implementation details.

## Evidence log

- 2026-10-25: Added `scripts/review_funding_witness_draft.py` pure offline candidate reviewer, `tests/test_funding_witness_draft.py` deterministic synthetic fixtures, `docs/design/funding-independent-witness-r2.md` trust/deployment design and explicit 2026-10-25 supersession of A-first research recommendation. The reviewer never authenticates an independent signature/time root, so even positive output is `CANDIDATE_MATCH_UNATTESTED`; all source/approval/trading flags hard-false. **CI and actual observer evidence not yet verified**.

- 2026-10-25: GitHub third prospective immutable original 2026-10-25 with matching successful release.published audit; still R1-only. Main existing code and ADR read. Official OKX contract cross-checked against current endpoint docs.

## Resume from here

Open PR linked to Issue #85 and this active plan. Run code-level offline tests, all five CI and Historical Smoke. Fix actual CI errors from logs. Upon exact final-head green checks squash merge, verify main CI, and archive the child plan separately. Parent Issue #85 stays open; do not deploy witness or promote candidate output.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: actual independent time/observer attestation, approved source acquisition, negative Funding low-volatility and 90 pinned days, economic gating.
