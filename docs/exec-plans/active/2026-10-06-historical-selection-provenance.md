# 2026-10-06-historical-selection-provenance: Preserve pre-registration evidence through corpus fixtures

Status: PLANNING
Owner: agent
Started: 2026-10-06
Last checkpoint: 2026-10-06

## Objective

Preserve outcome-independent historical sampling provenance end to end so a
future reviewer can distinguish:

- legacy/manual pinned regression days;
- days selected by a reviewed pre-registered sampling artifact.

Target evidence chain:

```text
sampling request/result artifact
  -> exact source run/artifact identity
  -> acquisition selection provenance
  -> preparation input
  -> full + compact fixture manifest
  -> pinned corpus/report classification
```

The work records provenance only. It does **not** change ADR-0007 readiness
counts or Stage-2 eligibility semantics.

## Why this is required

The deterministic sampling policy now chooses market days without observing
strategy outcomes, and Funding acquisition can consume explicit sampled dates.

However, the current acquisition/preparation manifests retain the selected dates
but not the exact sampling artifact identity/digest. Once a fixture is pinned,
the repository cannot prove from the fixture alone that the date came from a
pre-registered draw.

Cash also still needs a sample-driven discovery path that preserves the same
source evidence.

## Non-goals

- No Stage-2 threshold design/activation.
- No change to current 30/90 readiness computation.
- No automatic acquisition/promotion/merge.
- No retroactive claim that legacy fixtures were pre-registered.
- No outcome-dependent resampling or replacement.
- No raw archive changes.

## Governing decisions

- AGENTS.md
- ADR-0006 historical provenance
- ADR-0007 progressive acceptance policy
- deterministic historical sampling policy
- acquisition / preparation / campaign promotion contracts

## Design direction

Introduce optional strategy-specific **selection provenance** with a versioned
schema. A pre-registered record identifies:

- selection kind;
- strategy;
- exact sampling workflow run ID;
- exact sampling artifact name + Actions artifact ID + digest;
- sampling policy version;
- seed;
- study window;
- selected market dates;
- sampling evidence payload SHA-256.

The provenance is copied, never recomputed from market outcomes.

Funding:

```text
sample artifact
  -> composer verifies/replays sample
  -> acquisition carries funding selection provenance
  -> each Funding preparation receives the same record
  -> compact fixture states the date is one selected member
```

Cash:

```text
cash-and-carry sample artifact
  -> sampled discovery runs only selected dates
  -> discovery control artifact carries sample identity
  -> case planner preserves sample provenance
  -> acquisition + Cash preparation carry the record
  -> compact fixture states the entry date is one selected member
```

Legacy/manual acquisition remains valid with selection provenance absent.

## Constraints and invariants

- Selection provenance is optional for backward compatibility.
- If present, it must be internally complete and fail closed.
- Strategy in provenance must match the prepared strategy.
- Prepared market date must be one of selected_market_dates.
- Sampling artifact identity must be exact run/name/id/digest.
- Sampling evidence SHA-256 must be over canonical JSON bytes.
- Policy version/seed/window/dates must agree with verified sampling evidence.
- Preparation workflows only copy already-verified provenance; they do not
  select dates.
- Compact derivation must preserve selection provenance exactly.
- Promotion/corpus validation must reject provenance drift.
- Legacy fixtures remain `selection_kind=legacy_untracked` in reporting,
  never silently upgraded.
- Corpus report may report provenance coverage counts, but Stage-1 economics
  and ADR-0007 readiness remain unchanged until a later explicit decision.

## Acceptance criteria

- [x] Define versioned selection-provenance model + parser.
- [x] Canonical SHA-256 of sampling evidence is deterministic and verified.
- [x] Funding composer emits verified selection provenance with explicit dates.
- [x] Acquisition manifest carries optional Funding/Cash selection provenance.
- [x] Funding preparation/full/compact manifests preserve provenance.
- [ ] Add sampled Cash discovery workflow from exact sampling artifact.
- [ ] Cash discovery control carries exact sample provenance.
- [ ] Cash case planner preserves provenance into its report.
- [ ] Cash composer/acquisition preserves provenance.
- [ ] Cash preparation/full/compact manifests preserve provenance.
- [ ] Fixture loaders/promoters reject provenance/date/strategy drift.
- [ ] Corpus report classifies pre-registered vs legacy/untracked days.
- [ ] Reporting adds provenance coverage counts without changing 30/90 readiness.
- [ ] Tests cover legacy compatibility, tampering, wrong strategy/date and exact copying.
- [ ] README/testing docs explain provenance classification.
- [ ] Final CI + relevant workflow self-tests green.
- [ ] Archive after verification.

## Implementation slices

- [x] 1. Selection provenance model and canonical sampling-evidence digest.
- [x] 2. Funding composer/acquisition propagation.
- [x] 3. Funding preparation/fixture propagation.
- [ ] 4. Sampled Cash discovery + control evidence.
- [ ] 5. Cash case-plan/acquisition/preparation propagation.
- [ ] 6. Corpus validation/report classification.
- [ ] 7. Docs, final verification and archive.

## Verification matrix

| Gate | Evidence | Status |
|---|---|---|
| Static/architecture | normal CI | pending |
| Code | provenance/parser/propagation/tamper tests | pending |
| API | no regression | pending |
| Reference E2E | unchanged | pending |
| Sampling workflow | exact sample evidence | existing green |
| Funding sampled composer | exact sample -> provenance + dates | pending |
| Cash sampled discovery | exact sample -> selected discovery dates only | pending |
| Historical smoke/report | provenance classification reporting_only | pending |

## Decision gates

A later explicit decision is required before changing ADR-0007 eligibility to
count only pre-registered days. This plan records the facts needed for that
decision but does not make it.

## Evidence log

- 2026-10-06: deterministic sampling workflow run 37482498880 produced Funding
  sample artifact 11421537670.
- 2026-10-06: selection-provenance value object/parser now replays the exact
  deterministic sample and verifies canonical sampling-evidence SHA-256, source
  run/artifact identity shape, policy/seed/window/population, selected dates,
  strategy and market-date membership. Tamper tests cover seed/date/hash/schema.
- 2026-10-06: historical acquisition schema carries optional per-strategy
  selection provenance. Funding explicit dates must exactly equal the reviewed
  selected_market_dates when provenance is present.
- 2026-10-06: Funding resolve/preparation path passes verified selection
  provenance to each selected day; full and compact Funding manifests preserve
  it byte-for-byte as JSON structure.
- 2026-10-06: sampled composer run 37483512784 verified that exact artifact,
  replayed the draw, and emitted the five explicit Funding dates without gap
  filling.
- 2026-10-06: current committed corpus remains 2 Funding + 2 Cash days and does
  not yet encode whether a pinned fixture was pre-registered.

## Deviations and discoveries

None.

## Resume from here

Implement Cash sampled discovery from an exact cash-and-carry sampling artifact.
Discovery must run only selected dates and emit a control record containing the
exact sampling artifact identity/digest plus canonical selection provenance.
Then propagate that provenance through Cash case-plan -> acquisition ->
preparation/full/compact fixture.

## Completion

Final implementation commit:
CI run:
Workflow evidence:
Remaining unassessed items:
