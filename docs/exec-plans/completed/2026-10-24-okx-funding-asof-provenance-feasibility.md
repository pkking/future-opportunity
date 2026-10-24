# OKX Funding as-of provenance: official-contract gap and witness design options

Issue: #85
Status: COMPLETED
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

## Acceptance criteria

- [x] Cite verified official OKX docs and separate `fundingTime`, `realizedRate`, candle `confirm`, client request signature and third-party custody semantics.
- [x] Explain why late historical reconstruction and cross-day byte consistency do **not** prove when OKX published source values.
- [x] Evaluate at least three plausible evidence options with trust boundary, clock, independence, reproducibility, failure modes and expected operator/maintenance cost.
- [x] Describe an outcome-blind independent-observer evidence contract and validation gates as a **proposal only**; never assert the witness exists or approve sample inclusion.
- [x] Identify which design choices need explicit human approval (new source standard / independent collection/storage / economic gate); keep current flags and 32 pinned cases unchanged.
- [x] Submit docs-only PR linked to Issue/Plan, pass five CI jobs + Historical Smoke on final head, merge, verify main CI, then independently archive completed plan and update parent Issue #85 checkpoint.

## Implementation slices

- [x] 1. Research official docs and repository current source contract, draft sourced feasibility note.
- [x] 2. CI/Smoke final-head review, merge, postmerge main CI.
- [x] 3. Archive and update parent evidence backlog, no runtime behavior change.

## Verification matrix

| Gate | Evidence | Status |
| --- | --- | --- |
| Documentation fidelity | official OKX guide referenced by new research note; code/policy compared to main | PASS (source-backed scope) |
| CI | PR #152 final-head CI #40143914612 five SUCCESS; postmerge main #40143970897 SUCCESS | PASS |
| Historical | PR #152 final-head #40143914673 SUCCESS | PASS |

## Decision gates

No approval is sought by this subplan. Implementation of a newly independent exchange-fetching witness/third-party service, new storage or a changed historical acquisition-grade standard may require an ADR and explicit human approval. Continue research without implementing any of those changes.

## Evidence log

- 2026-10-24: PR #152 final tested head `4cb6d4810b884bba4e9dd01ed7487476a522c725`, [CI #40143914612](https://github.com/pkking/future-opportunity/actions/runs/40143914612) five SUCCESS and [Historical Backtest Smoke #40143914673](https://github.com/pkking/future-opportunity/actions/runs/40143914673) SUCCESS; squash merge `fc576b6cdf319e79ceab106b8f66b4fe0bca61c5`; postmerge [main CI #40143970897](https://github.com/pkking/future-opportunity/actions/runs/40143970897) SUCCESS. E2E evidence Artifact ID `12579528059`, SHA256 `9e3d124a0649bae0172d340e8087383598d4b4d898e63e4a62a3c7f6b8f820d9`; historical Artifact ID `12580111933`, SHA256 `1de68bdde83f557693dffcd5793c4024154b979387c8af92eefa5be5e800383f`.
- 2026-10-24: First implementation head failed plan integrity [#40143868733](https://github.com/pkking/future-opportunity/actions/runs/40143868733) solely because section headers used `## Acceptance` and `## Implementation` instead of the required exact headings. Fixed without lowering the validator; final CI all five passed. No runtime/exchange or source changes.

- 2026-10-24: Research note `docs/research/okx-funding-asof-source-provenance-feasibility.md` drafted with official OKX source links for `funding-rate-history`, `history-candles`, Market Data independent-caches warning, and private request HMAC. Distinguishes R0 retrospective replay / R1 GitHub immutable custody / proposed R2 independent before-entry observer / unidentified R3 actual exchange first-publication signature. Provides four-option cost/trust/failure matrix and a proposed independent-witness receipt schema **without deploying any observer or altering policy**. CI pending.

- 2026-10-24: Official OKX API documentation (https://www.okx.com/docs-v5/en/ and https://www.okx.com/docs-v5/zh/) consulted, REST signing is client private-request authentication; public Funding history is recent historical event values, not a signed publication proof.

## Resume from here

This evidence feasibility research is complete. Continue parent Issue #85 with original-source operational monitoring and discovery of *actual independently verifiable* as-of publication witnesses. **Do not implement an independent collector, approve new source classes, infer venue signatures or alter historical admissions** without an explicit approved ADR. No R2/R3 witness was deployed or verified.

## Completion

Final commit: `fc576b6cdf319e79ceab106b8f66b4fe0bca61c5` (PR #152 squash, exact tested head `4cb6d4810b884bba4e9dd01ed7487476a522c725`)
CI run: #40143914612 five SUCCESS, Historical #40143914673 SUCCESS, postmerge main #40143970897 SUCCESS
E2E artifact: ID `12579528059`, Historical artifact ID `12580111933`; SHA256 digests in evidence log
Remaining unassessed items: actual independently verified publication as-of UTC entry, exchange response signatures, negative-low regime, pinned 90-day Funding basis.
