# OKX Funding as-of provenance: official-contract gap and witness design options

Issue: #85
Status: IMPLEMENTING
Owner: agent
Started: 2026-10-24
Last checkpoint: 2026-10-24

## Objective

Produce a source-backed decision-quality research note distinguishing (a) retrospective OKX event-time reconstruction, (b) GitHub pre-entry immutable custody and independently attested byte replay, (c) independent pre-entry observation of an official API response, and (d) an exchange-signed/publication-origin claim. Find feasible future evidence improvement paths without changing the already accepted historical acquisition policy or performing market API writes/reads in a GitHub audit workflow.

## Baseline

- Latest merged `main` SHA `56aa5ce6cc83e77316015d3b95a1b74ccfb2be53` after PRs #150–151, main CI #40143543770 SUCCESS, no open PRs.
- Issue #85 remains OPEN/BLOCKED_EVIDENCE. Funding 32 pinned / preferred 90, Cash 66. Two daily immutable source originals (2026-10-23/24) match release.published audits, zero numeric overlap revisions, normal first-day confirmation advancement.
- Official OKX documentation consulted 2026-10-24: public historical funding-rate data, 1Dutc `confirm` values and public Market Data independent service caches; private `OK-ACCESS-SIGN` signing *requests*.
- Current accepted frozen ADR-0008 prohibits numerical economics gate and does not authorize an alternative historical publication/authentication proof.

## Non-goals

No new market API polling, real/fake signing, network witness, sidecar, storage vendor, irreversible data migration, GitHub scheduler, retrospective backfill, historical fixture admission, strategy gate, trading or exchange credentials. This subplan delivers **research specification only**, not evidence acquisition or approval.

## Acceptance

- [ ] Cite verified official OKX docs and separate `fundingTime`, `realizedRate`, candle `confirm`, client request signature and third-party custody semantics.
- [ ] Explain why late historical reconstruction and cross-day byte consistency do **not** prove when OKX published source values.
- [ ] Evaluate at least three plausible evidence options with trust boundary, clock, independence, reproducibility, failure modes and expected operator/maintenance cost.
- [ ] Describe an outcome-blind independent-observer evidence contract and validation gates as a **proposal only**; never assert the witness exists or approve sample inclusion.
- [ ] Identify which design choices need explicit human approval (new source standard / independent collection/storage / economic gate); keep current flags and 32 pinned cases unchanged.
- [ ] Submit docs-only PR linked to Issue/Plan, pass five CI jobs + Historical Smoke on final head, merge, verify main CI, then independently archive completed plan and update parent Issue #85 checkpoint.

## Implementation

- [ ] 1. Research official docs and repository current source contract, draft sourced feasibility note.
- [ ] 2. CI/Smoke final-head review, merge, postmerge main CI.
- [ ] 3. Archive and update parent evidence backlog, no runtime behavior change.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Documentation fidelity | official OKX docs and current audit code | pending |
| CI | five plan/static/code/API/E2E jobs | pending |
| Historical | Historical Backtest Smoke | pending |

## Decision gates

No approval is sought by this subplan. Implementation of a newly independent exchange-fetching witness/third-party service, new storage or a changed historical acquisition-grade standard may require an ADR and explicit human approval. Continue research without implementing any of those changes.

## Evidence log

- 2026-10-24: Official OKX API documentation (https://www.okx.com/docs-v5/en/ and https://www.okx.com/docs-v5/zh/) consulted, REST signing is client private-request authentication; public Funding history is recent historical event values, not a signed publication proof.

## Resume from here

Write short but precise source-backed note in docs/research, then PR review and CI. Do not create an exchange API reader or unapproved witness.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: actual independently verified publication as-of UTC entry, exchange response signatures, negative-low regime, pinned 90-day Funding basis.
