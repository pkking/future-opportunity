# 2026-10-08-funding-stage2-design-evidence: Prepare Stage-2 decision evidence

Issue: #41
Status: READY_FOR_REVIEW
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Prepare a decision-ready Stage-2 distribution-gate proposal for Funding Carry now that the merged historical corpus contains 32 distinct pinned market days, while preserving ADR-0007's requirement that Stage 2 cannot be activated or thresholds frozen without a separate ADR and human approval.

## Current facts

- Main contains 32 distinct pinned Funding Carry market days and 5 Cash-and-Carry days.
- ADR-0007 minimum eligibility is 30 distinct market days per strategy; preferred evidence base is 90.
- Funding therefore qualifies to propose Stage-2 target design, but the repository as a whole is not minimum-ready because Cash remains at 5 days.
- Final Wave 003 Historical Backtest Smoke artifact 11521697208 reports Funding: 32 evaluated cases, 0 qualified cases, qualification rate 0.
- Expected net return across all 32 Funding cases is fully assessed: minimum -0.001432718975083680, P25 -0.0013358771869091625, median -0.001304108183561355, mean -0.0013090434891949763, P90 -0.001239404526487287, maximum -0.001215.
- Realized-return bounds are unassessed for qualified cases because there are zero qualified cases.
- 29/32 Funding days (90.625%) are pre-registered samples; 3 are legacy untracked.
- Market-wide opportunity arrival rate remains explicitly unassessed.

## Constraints and invariants

- Do not activate Stage 2.
- Do not modify the active historical gate (`provenance_and_semantics`).
- Do not copy deterministic reference targets into historical thresholds.
- Do not tune thresholds merely so the 32-day corpus passes.
- Preserve the distinction between pinned-case qualification rate and market-wide opportunity arrival rate.
- Preserve zero-opportunity periods as evidence rather than coercing them into realized-return zeroes.
- Any Stage-2 ADR remains Proposed until explicit human approval.

## Acceptance criteria

- [x] Version a concise 32-day Funding evidence summary with provenance.
- [x] Separate facts from product choices requiring approval.
- [x] Propose candidate aggregation-window semantics.
- [x] Propose qualification-rate semantics that do not claim market-wide opportunity frequency.
- [x] Propose which return statistic can be gated and explain why realized-return statistics are currently unavailable.
- [x] Define zero-opportunity treatment options.
- [x] Define sample-size / pre-registration / evidence-completeness options.
- [x] Draft a Proposed Stage-2 ADR without activating it.
- [x] Reduce the remaining human decision to a small explicit option set.
- [ ] Full PR CI and Historical Backtest Smoke pass.

## Implementation slices

- [x] 1. Confirm Wave 003 merged main state and Stage-2 eligibility.
- [x] 2. Extract final 32-day distribution evidence from Historical Smoke artifact.
- [x] 3. Version evidence analysis.
- [x] 4. Draft Proposed ADR with explicit decision alternatives.
- [x] 5. Review for accidental policy activation.
- [ ] 6. Run repository CI/Smoke and archive at the human-approval boundary.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Main pinned Funding count | `tests/fixtures/historical/corpus-index.json` | 32 |
| Stage-2 eligibility rule | ADR-0007 | Funding meets >=30 |
| Final historical evidence | Smoke run 37710601449 artifact 11521697208 | extracted |
| Active historical gate unchanged | report field `active_historical_gate=provenance_and_semantics` | verified |
| Reference targets not reused | report field `reference_targets_used_as_thresholds=false` | verified |
| Evidence note | `docs/research/funding-stage2-design-evidence-32-days.md` | complete |
| Proposed ADR | `docs/adr/0008-funding-stage2-historical-distribution-gate.md` | Proposed only |
| Static/API/E2E | PR CI | pending |
| Historical Smoke | PR workflow | pending |

## Decision gates

Human approval is required before accepting ADR-0008 or changing any active historical threshold. This task recommends keeping the current Stage-1 gate active and delaying numerical economics-gate activation until qualified-case realized-return evidence exists, preferably with >=90 pinned days before freezing stable thresholds.

## Evidence log

- 2026-10-08: Wave 003 PR #40 merged as 383aa12fa5ef4b6f55d442734db6100a4c5c2b84.
- 2026-10-08: main corpus verified at Funding=32 distinct days, Cash=5.
- 2026-10-08: Historical Smoke run 37710601449 artifact 11521697208 digest sha256:7cbdc484176ae0c167b6c0d8124d107c46a4b89a6d0072e03331bacb31237c5c.
- 2026-10-08: Funding report: 32 evaluated, 0 qualified, pinned qualification rate=0, 32/32 expected-net-return assessed, 0 realized-return assessed.
- 2026-10-08: Funding selection provenance: 29 pre-registered, 3 legacy; pre-registered coverage ratio=0.90625.
- 2026-10-08: evidence note and Proposed ADR-0008 drafted; active policy remains unchanged.

## Deviations and discoveries

The 30-day threshold is sufficient to propose Stage-2 design but not sufficient to infer a realized-return distribution here because no Funding case qualified under the current production economics. The design must therefore separate qualification evidence from conditional realized-return evidence.

## Resume from here

Open a PR linked to Issue #41, run all gates, archive this plan after successful review-head CI, and stop at the human approval boundary. Do not accept ADR-0008 or activate Stage 2 without explicit approval.

## Completion

Final commit: pending
CI run: pending
Remaining unassessed items: PR verification and human approval of Stage-2 product choices