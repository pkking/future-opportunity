# Cash 2025 quarter preparation artifact identity gate

Issue: #69
Status: VERIFYING
Owner: agent
Started: 2026-10-10
Last checkpoint: 2026-10-10

## Objective

Before a frozen Q3 or Q4 2025 Cash preparation run is described as complete,
verify the full prepared, compact and actuals **artifact inventory** against
the exact twelve pre-registered dates and historical future contract in its
immutable acquisition manifest. Produce machine-readable, fail-closed inventory
evidence so the human operator can distinguish preparation completeness from
unassessed L2/replay/return semantics.

## Non-goals

- Do not dispatch either preparation run, auto-promote fixtures, mutate the
  pinned corpus, replace pre-registered dates, or enable economics thresholds.
- Do not treat presence of ZIP artifacts as proof of their contents or realized
  strategy profitability. The separate planner/promotion process remains required.
- Do not change strategy/domain models or accepted ADR boundaries.

## Must-read context

- `AGENTS.md`, `docs/design-baseline-v0.1.md`,
  `docs/v0-implementation-status.md`
- `docs/agents/workflow.md`, `docs/agents/testing.md`
- `docs/historical-acquisition-plans/cash-2025-q3-12day-wave-001.json`
- `docs/historical-acquisition-plans/cash-2025-q4-12day-wave-001.json`
- `.github/workflows/prepare-cash-2025-quarter-wave.yml`
- `.github/workflows/prepare-cash-historical-fixture.yml`

## Current facts

- Main head at start: `d93fcd9fe1d0703bd17fade34eba93e278963378`.
- Post-merge main CI: run 37809568438 success; Historical Smoke:
  run 37809568399 success.
- Funding 32, Cash 30 pinned days; Stage-2 decision quality accepted,
  economics gate disabled.
- Issue #69 is open; no Q3/Q4 preparation workflow_dispatch runs identified
  in latest Actions history inspected on 2026-10-10.
- The 2025 wave summary currently counts only twelve artifact names beginning
  with `okx-btc-cash-and-carry-compact-`; it does not verify one per frozen
  date, 12 prepared parents and 12 actuals, expiry identity, artifact digest
  or expiry status.
- Cash reusable preparation emits three artifacts per case: full preparation,
  compact and actuals. All include the exact date, future ID and run ID.

## Constraints and invariants

- Only explicit `workflow_dispatch` initiates Q3/Q4 preparation.
- Frozen source selection is bound to run 37755705789, artifact 11539833591,
  SHA-256 f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74.
- Frozen cohorts are Q3 12x BTC-USDT-250926 and Q4 12x BTC-USDT-251226;
  both entry at 00:15 UTC with contract-specific exit and expiry.
- Validate names by exact expected set, unique ID/name, positive size,
  nonexpired status and Actions sha256 digest; fail closed on extras,
  omissions, collisions, run identity mismatch and malformed API payloads.
- Evidence must not assert that downloaded artifact contents or L2
  completeness have been inspected. Keep read-only permissions.
- Run CI, API, E2E and Historical Smoke for final revision before calling
  the task complete.

## Acceptance criteria

- [ ] Offline tests reject missing/extra/duplicate/mismatched artifacts,
      incorrect source run/contract/date, expired/missing digest/empty artifact,
      malformed manifests/API shape; accept exact 12x3 case inventory.
- [ ] Q3/Q4 workflow gates artifact inventory using committed manifest and
      emits status/error evidence even if verification fails.
- [ ] Workflow remains dispatch-only, read-only, no corpus or promotion writes.
- [ ] Targeted tests and static check pass.
- [ ] Full final-head CI, API, E2E and historical smoke pass.
- [ ] Issue #69 stays open pending actual operator dispatch and evidence.

## Implementation slices

- [x] 1. Add deterministic offline artifact-inventory checker with
      fail-closed structured report and CLI (`72bd980`, `12766e1`).
- [x] 2. Add comprehensive unit tests and workflow invariants
      (`8546f57`, `4b3c7dc`, `80b3665`, `f5d3fcd`).
- [x] 3. Wire Q3/Q4 summary job to verify inventory and always upload the
      evidence (including failures) (`0400357`).
- [ ] 4. Run tests and inspect final GitHub checks; checkpoint with evidence.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Targeted | `uv run pytest tests/test_cash_2025_quarter_artifact_identity.py tests/test_cash_2025_quarter_acquisition_handoff.py -v` | deterministic pass | pending |
| Static | `uv run ruff check .` | zero violations | pending |
| Code | `uv run pytest tests --ignore=tests/test_api_smoke.py --ignore=tests/e2e` | CI code-tests | pending |
| API | `uv run pytest tests/test_api_smoke.py` | CI api-tests | pending |
| E2E | `uv run pytest tests/e2e -v` | strategy-e2e-evidence artifact | pending |
| Historical | Historical Backtest Smoke workflow | verified pinned corpus | pending |

## Decision gates

None for inventory validation. Operator has not dispatched 2025 Q3/Q4
preparations; Issue #69 execution and publication-dependent evidence remain
separate. Do not bypass explicit operator control.

## Evidence log

- 2026-10-10: GitHub inspection: main `d93fcd9`, issue #69 only open
  issue, no open PR, 37809568438 CI and 37809568399 Historical Smoke success.
- 2026-10-10: Existing summary checks compact *count* only;
  reusable Cash workflow produces prepared/compact/actuals names.

## Deviations and discoveries

- Original PR head `4b3c7dc` CI `38047526617` failed Code-level tests
  at collection: `ModuleNotFoundError: No module named 'scripts'`.
  The standalone verifier is not a package; tests now load it with Python
  `runpy.run_path` (`f5d3fcd`). The same head's static, API, E2E and
  Historical Smoke checks passed, but **this is not final-head evidence**.
- Repository checkout is not available in the local tool runtime; validation
  is performed by actual GitHub Actions on review heads.
- Reviewer must not interpret Actions SHA-256 metadata format validation as
  downloaded ZIP/content verification.

## Resume from here

Inspect CI + Historical Smoke on final PR #70 head; fix causal failures,
then record final-head results before squash merge. Keep Issue #69 open because
operator-dispatched 2025 Q3/Q4 source acquisition and governed promotion remain.

## Completion

Final commit: pending
CI run: pending
E2E artifact: pending
Remaining unassessed items: real Q3/Q4 archives, L2 content, completed
operator-dispatched runs, planner and promotion evidence.
