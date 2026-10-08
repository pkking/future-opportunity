# 2026-10-08-funding-stage2-design-evidence: Prepare Stage-2 decision evidence

Issue: #41
Status: COMPLETED
Owner: agent
Started: 2026-10-08
Last checkpoint: 2026-10-08

## Objective

Prepare a decision-ready Stage-2 distribution-gate proposal for Funding Carry from the merged 32-day historical corpus without activating Stage 2 or freezing product thresholds.

## Acceptance criteria

- [x] Version a concise 32-day Funding evidence summary with provenance.
- [x] Separate facts from product choices requiring approval.
- [x] Propose aggregation-window semantics.
- [x] Propose pinned-case qualification-rate semantics without claiming market-wide opportunity frequency.
- [x] Explain why realized-return gating is currently unavailable.
- [x] Define zero-opportunity treatment.
- [x] Define sample/provenance/evidence-completeness candidate rules.
- [x] Draft ADR-0008 as Proposed only.
- [x] Reduce remaining human decision to explicit options.
- [x] Full PR CI and Historical Backtest Smoke pass.

## Implementation slices

- [x] Confirm Wave 003 merged main state and Stage-2 eligibility.
- [x] Extract final 32-day distribution evidence.
- [x] Version evidence analysis.
- [x] Draft Proposed ADR-0008.
- [x] Verify no active policy change is introduced.
- [x] Run repository CI/Smoke.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Funding pinned days | main corpus | 32 |
| Funding pre-registered coverage | final report | 29/32 = 90.625% |
| Funding qualified cases | final report | 0/32 |
| Expected-net-return assessed | final report | 32/32 |
| Realized-return assessed | final report | 0 qualified cases |
| Active historical gate | `provenance_and_semantics` | unchanged |
| Reference targets used as thresholds | false | unchanged |
| Required CI | run 37711113286 | 5/5 successful |
| Historical Backtest Smoke | run 37711113313 | successful |

## Decision gates

ADR-0008 remains Proposed. Human approval is still required before accepting it or implementing any Stage-2 numerical economics gate.

Recommended posture at this boundary:

- keep Stage 1 active;
- treat 32 days as sufficient for semantic design, not stable economic threshold freezing;
- do not manufacture a realized-return threshold from zero qualified cases;
- continue collecting qualified-case evidence;
- prefer >=90 pinned days before freezing stable thresholds.

## Evidence log

- Wave 003 merge: 383aa12fa5ef4b6f55d442734db6100a4c5c2b84.
- Final historical evidence source: run 37710601449 artifact 11521697208, digest sha256:7cbdc484176ae0c167b6c0d8124d107c46a4b89a6d0072e03331bacb31237c5c.
- Funding distribution: min -0.1433%, P25 -0.1336%, median -0.1304%, mean -0.1309%, P90 -0.1239%, max -0.1215% expected net return across pinned cases.
- PR #42 review CI: 37711113286; Historical Smoke: 37711113313.

## Deviations and discoveries

The evidence threshold for proposal readiness was met, but zero qualified cases means the corpus does not yet contain a conditional realized-return distribution. Stage-2 design must therefore distinguish decision-quality semantics from economic-attractiveness semantics.

## Resume from here

After this proposal PR is merged, stop for explicit human approval. If ADR-0008 is approved, create a separate implementation task. If the user chooses a different option set, revise ADR-0008 in a new task before any policy activation.

## Completion

Final commit: a1b076eb02a94ec4bc1559a40e96573db3ab8559
CI run: 37711113286 (all five required jobs successful); Historical Backtest Smoke 37711113313 successful
Remaining unassessed items: human approval of ADR-0008 product choices and any subsequent Stage-2 implementation