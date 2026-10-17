# Cash 2025 quarter preparation artifact identity gate

Issue: #69
Status: COMPLETED
Owner: agent
Started: 2026-10-10
Last checkpoint: 2026-10-17

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

- [x] Offline tests reject missing/extra/duplicate/mismatched artifacts,
      incorrect source run/contract/date, expired/missing digest/empty artifact,
      malformed manifests/API shape; accept exact 12x3 case inventory.
- [x] Q3/Q4 workflow gates artifact inventory using committed manifest and
      emits status/error evidence even if verification fails.
- [x] Workflow remains dispatch-only, read-only, no corpus or promotion writes.
- [x] Targeted tests and static check pass.
- [x] Full final-head CI, API, E2E and historical smoke pass.
- [x] Issue #69 stays open pending actual operator dispatch and evidence.

## Implementation slices

- [x] 1. Add deterministic offline artifact-inventory checker with
      fail-closed structured report and CLI (`72bd980`, `12766e1`).
- [x] 2. Add comprehensive unit tests and workflow invariants
      (`8546f57`, `4b3c7dc`, `80b3665`, `f5d3fcd`).
- [x] 3. Wire Q3/Q4 summary job to verify inventory and always upload the
      evidence (including failures) (`0400357`).
- [x] 4. Run tests and inspect final GitHub checks; checkpoint with evidence.
      Final reviewed head `f5d7b99`; CI 38047639238 and Historical Smoke
      38047639302 successful. Squash merged as `695938f` via PR #70.

## Verification matrix

| Scope | Command / CI gate | Expected evidence | Status |
|---|---|---|---|
| Targeted | `uv run pytest tests/test_cash_2025_quarter_artifact_identity.py tests/test_cash_2025_quarter_acquisition_handoff.py -v` | code-tests in CI 38047639238 passed | verified |
| Static | `uv run ruff check .` | static in CI 38047639238 passed | verified |
| Code | `uv run pytest tests --ignore=tests/test_api_smoke.py --ignore=tests/e2e` | CI 38047639238 passed | verified |
| API | `uv run pytest tests/test_api_smoke.py` | CI 38047639238 passed | verified |
| E2E | `uv run pytest tests/e2e -v` | CI 38047639238 E2E success | verified |
| Historical | Historical Backtest Smoke workflow | 38047639302 success | verified |

## Decision gates

None for inventory validation. Operator has not dispatched 2025 Q3/Q4
preparations; Issue #69 execution and publication-dependent evidence remain
separate. Do not bypass explicit operator control.

## Evidence log

- 2026-10-10: GitHub inspection: main `d93fcd9`, issue #69 only open
  issue, no open PR, 37809568438 CI and 37809568399 Historical Smoke success.
- 2026-10-10: Existing summary checks compact *count* only;
  reusable Cash workflow produces prepared/compact/actuals names.
- 2026-10-10: PR #70 head `f5d7b99`: CI 38047639238 success,
  Historical Smoke 38047639302 success. Squash merged `695938f`.
  No Q3/Q4 preparation dispatched; main pinned corpus unchanged.

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

## 2026-10-17 source-backed frozen Q3 acceptance checkpoint

**Q3 frozen preparation accepted; Q4 and promotion still blocked.**
Operator-dispatched [Run 39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
(`wave=q3`) on main `437089cc1609c009adc7df1b6da64174bd495d4f`
completed **SUCCESS**. All 12 Cash matrix cases passed. The invariant
control and manifest resolver also passed; source provenance remains pinned
to run `37755705789`, artifact `11539833591`, digest
`sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74`.

Downloaded the
`cash-2025-quarter-summary-q3` artifact (ID `12094684975`, SHA-256
`f3b6afade9420a26c3df8bc33a2175b0c675de0d3abdc26870fc2d1f588d414c`).
Its `summary.json` reports `status=verified_inventory_only`,
`acquisition_result=success`, exactly **12 prepared + 12 compact +
12 actuals**, no missing/extra names, errors, expired artifacts or
digest-format failures, `corpus_mutation=false`,
`promotion_dispatched=false`. The built-in audit correctly labels
`artifact_contents_verified=false`: it checks metadata only.

**Additional independent downloaded ZIP/content inspection** over the
same 36 distinct, nonexpired Actions artifacts:
- All **36 ZIP bytes** match the SHA-256 digest supplied by GitHub Actions.
- All **12 prepared and 12 compact manifests** have four canonical
  SPOT/FUTURES entry/exit JSONL components; each is one sampled book.
  All **96 normalized JSONL checksums** match manifest SHA-256, prices
  and quantities remain positive, and source age is 0..578ms across
  cases, within 5000ms.
- All 12 compact manifests have `pinning_status=commit_ready`, preserve
  the exact frozen `selection_provenance` and identify the same run,
  exact matching parent prepared artifact ID, and matching **actual
  prepared ZIP SHA-256**. All 12 actuals reports agree with their
  prepared datasets and frozen entry/exit UTC timestamps.
- 12 reports each contain one case: **9 qualified**, **3 correctly
  rejected** for `expected_net_return_not_positive` on
  `2025-09-07`, `2025-09-15`, `2025-09-22`.
  Those unqualified cases have `realized_net_return=null` and are
  NOT mislabeled as zero-profit realized trades. Of the nine qualified
  cases, nine realized-paper-return components are complete and positive
  for their respective holding periods (median 0.0031091820414691266,
  range 0.0005676965571048619..0.005162027964995246),
  **not** annualized or a Stage-2 threshold. Qualified sample ratio
  9/12 is not a market-wide opportunity rate. `MarginSafety` and
  `VenueExposure` are unassessed where reported.
- No fixture was promoted or added to the pinned corpus.

The original status block and pre-Q3 resume instructions below were
written before this run and are superseded by the next actions here.

## 2026-10-17 Q4 independently verified and combined Q3/Q4 checkpoint

**Both frozen quarters are accepted at the preparation/content-audit boundary.**
The Q4 operator-dispatched [run 39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844)
completed **SUCCESS** on main
`5bdc2598307140624d0e7cfb734bcc519bd0b186`, with all 12
`BTC-USDT-251226` fixed-date cases passed. The frozen source-bound
resolver, acquisition manifest and 12-case audit jobs succeeded.
Source selection unchanged: run `37755705789`,
artifact `11539833591`, digest
`sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74`.

Downloaded the `cash-2025-quarter-summary-q4` artifact
(ID `12095459608`, Actions ZIP SHA-256
`c10176846f26365179eacdb00c23a2c7adfd86d85fef7599c7f7a576f57e22f1`).
Its `summary.json` reports `status=verified_inventory_only`,
`acquisition_result=success`, exactly **12 prepared + 12 compact +
12 actuals**, no errors, missing/extra names, expired artifacts or
checksum-format violations. It explicitly marks
`artifact_contents_verified=false`, `corpus_mutation=false`,
`promotion_dispatched=false`.

**Independent ZIP content audit, not just inventory metadata:**
- Downloaded **all 36 actual Q4 ZIPs** and checked each archive's
  SHA-256 against its GitHub Actions artifact digest: **36/36 match**.
- Verified exactly four normalized entry/exit SPOT/FUTURES sampled
  books per prepared and compact manifest: **96/96 JSONL
  SHA-256 match**. Prices and retained quantities are finite and
  strictly positive; each side has nonempty levels, book time
  staleness ≤**409ms** vs a 5000ms maximum.
- All **12 compact** `pinning_status=commit_ready`; exact source
  selection provenance and the same run ID match; each parent prepared
  artifact ID and SHA-256 of the *downloaded ZIP bytes* agree.
  All 12 actuals dataset IDs, entry 00:15 UTC, expiry-contract
  identity and exit 2025-12-25T00:15:00+00:00 agree with frozen manifest.
- **7 qualified cases** with `return_complete=true` and complete
  simulated realized net returns (positive in these seven pre-selected
  cases; median ~**0.3110%** for their respective holding periods,
  min ~0.0802%, max ~0.6623%).
- **5 legitimately rejected** dates: 2025-11-22, 2025-11-29,
  2025-12-07, 2025-12-14, 2025-12-22, each reason
  `expected_net_return_not_positive`, with
  `realized_net_return=null` (not a numerical zero).

**Combined Q3 [39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
and Q4 [39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844)
independently verified:** 24 distinct frozen dates; **72/72**
prepared/compact/actuals ZIP SHA-256 and **192/192**
canonical sampled JSONL SHA-256 match; maximum source age **578ms**.
**16 qualified** with complete simulated realized net returns,
**8 appropriately rejected** with null realized returns.
The 16 qualified cases have median per-holding-period paper realized
net return ~**0.3110%** (range ~0.0568%–0.6623%).
This is NOT an annualized yield, market-wide opportunity frequency,
guaranteed return, account-level risk assessment, or Stage-2 economics
gate. `MarginSafety` and `VenueExposure` remain unassessed in
their respective historical reports.

**No pinned corpus case was promoted** by either run.
`Issue #69` stays OPEN for the separate read-only planner,
reviewed corpus promotion, CI, and final corpus accounting.
The previous Q4-pending handoff below is superseded.

## Resume from here

**ARCHIVED / COMPLETED.** Earlier source failures, pending commands and
review-blocked state described above are retained as historical
checkpoints only and are superseded by this closeout. Do not replay
an acquisition, diagnostic, planner or promotion based on a stale
checkpoint in this file.

Issue #69 is closed/completed after the user approved [PR #82](https://github.com/pkking/future-opportunity/pull/82).
The exact frozen Q3 and Q4 12-day preparations were independently
verified (runs [39016938121](https://github.com/pkking/future-opportunity/actions/runs/39016938121)
and [39018358844](https://github.com/pkking/future-opportunity/actions/runs/39018358844));
read-only planner [39020272173](https://github.com/pkking/future-opportunity/actions/runs/39020272173)
and governed staging [39021366976](https://github.com/pkking/future-opportunity/actions/runs/39021366976)
produced the source-bound 24-item review. User-approved PR #82 merged
as `ad4790c0c7ec785eb2de9d53704e154515451001`.
Post-merge main CI and Historical Smoke both succeeded; pinned
corpus is **Cash 54 / Funding 32**, all 24 registered 2025 dates
retained including eight correctly unqualified samples.
For future work start a **new Issue and execution plan**; never
re-use the closed Issue #69. No economics threshold or live trading
was approved.

## Completion

Final reviewed head: `f5d7b993ba32df53a731f053a0b8f6dd80f54b21`
Squash merge: `695938fda2094b63b941b93ce7e0926bb815cd17` (PR #70)
CI run: https://github.com/pkking/future-opportunity/actions/runs/38047639238 (success)
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/38047639302 (success)
E2E: strategy-e2e-evidence uploaded by 38047639238 (strategy acceptance success)
Updated 2026-10-17: Q3 Run 39016938121 and its 36 ZIP contents independently
verified as detailed above. Updated 2026-10-17: frozen Q3 Run 39016938121 and Q4 Run 39018358844
both independently verified (24 days / 72 ZIPs / 192 canonical files).
Remaining UNASSESSED: combined read-only planner output, governed
promotion PR and committed corpus result. Issue #69 remains OPEN.
Issue #69 is deliberately OPEN. The task is blocked on operator source evidence,
not completed. Plan stays active.

### Final reconciliation — 2026-10-17

Final commit: `ad4790c0c7ec785eb2de9d53704e154515451001` (PR #82,
human-approved completion of Issue #69, postdating the historical
checkpoints above; this archival move tracked under Issue #83).
CI run: https://github.com/pkking/future-opportunity/actions/runs/39023534155 (main SUCCESS).
Historical Smoke: https://github.com/pkking/future-opportunity/actions/runs/39023534123 (main SUCCESS).
Source integrity: Q3 39016938121 + Q4 39018358844; planner
39020272173; staged promotion 39021366976; 24/24 unique dates,
Cash 54 / Funding 32, no original fixture replaced.
Remaining unassessed items: The 90-day preferred distinct-day
coverage (Cash needs 36 more, Funding 58 more), more independent
Cash expiry cohorts, stronger Funding pre-entry regime coverage,
account-specific MarginSafety and portfolio-level VenueExposure.
Stage-2 economics and live execution remain DISABLED; these are
new research/ADR scopes, not unfinished tasks under Issue #69.
