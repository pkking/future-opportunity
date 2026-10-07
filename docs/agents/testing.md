# Agent Testing, E2E, and Evidence Contract

## Purpose

Tests are executable evidence. They exist to prevent both software regressions
and agent hallucination.

A strategy is not "working" because code looks plausible. It is working only to
the extent demonstrated by repeatable tests and captured evidence.

## CI gate model

Every change must preserve these gates.

### Gate 1 — static and architecture safety

Required:

```bash
uv run ruff check .
```

Architecture tests enforce boundaries such as read-only V0 exchange adapters.

If strict type checking is added as a required gate later, it must first be made
green on the existing baseline; do not introduce permanently failing gates.

### Gate 2 — code-level tests

Run domain/application/adapter/persistence/regression tests:

```bash
uv run pytest tests \
  --ignore=tests/test_api_smoke.py \
  --ignore=tests/e2e
```

This gate includes PostgreSQL integration tests and therefore requires the CI
PostgreSQL service.

### Gate 3 — API contract tests

```bash
uv run pytest tests/test_api_smoke.py
```

API tests must assert business semantics and safety surface, not only status
codes. The OpenAPI surface must not expose live order/trading endpoints in V0.

### Gate 4 — E2E strategy acceptance

```bash
mkdir -p artifacts/e2e
E2E_EVIDENCE_PATH=artifacts/e2e/strategy-evidence.json \
  uv run pytest tests/e2e -v \
  --junitxml=artifacts/e2e/junit.xml
```

CI uploads `artifacts/e2e/` even when the test fails.

### Historical smoke — pinned real-market replay

Historical smoke is an additional offline evidence layer. It does not replace
Gate 4 reference scenarios.

```bash
uv run python scripts/run_pinned_historical_smoke.py
uv run pytest tests/e2e/test_historical_backtest_acceptance.py -v
```

Rules:

- raw exchange archives stay out of git;
- committed historical fixtures must include provenance and checksums;
- compact derived books must state the frozen capital scenario and prove the
  retained depth covers the required base quantity with the declared margin;
- missing historical evidence remains `unassessed`; it is never synthesized;
- historical negative opportunities are valid evidence when the production
  qualification workflow rejects them for the expected reason;
- the historical evidence artifact must be uploaded with `if: always()`;
- V0 historical acceptance is defined by
  `tests/e2e/historical-target-policy.json` and gates provenance + replay
  semantics, not historical return magnitude;
- deterministic reference targets may be displayed for comparison but must not
  be reused as historical pass/fail criteria;
- distribution-based historical targets become eligible for design only after
  at least 30 distinct pinned entry-market days per strategy; 90 days is the
  preferred evidence base;
- switching to distribution-based historical gating requires a separate ADR and
  explicit human approval.

## Historical target policy

The repository deliberately separates **capability targets** from **observed
market distributions**.

Reference E2E answers:

```text
Can the strategy meet the intended business target when a qualifying
market state exists?
```

Historical replay answers:

```text
Did the product correctly interpret and handle this auditable real market
period?
```

The active V0 historical gate therefore requires:

```text
valid provenance/checksums
+ deterministic offline replay
+ stable normalization/derivation semantics
+ expected qualification semantics
= historical pass
```

A real market period does not fail historical CI merely because it contains no
profitable opportunity.

The progressive transition rule is:

```text
Stage 1 (current)
  provenance + semantics gate
  returns = reporting evidence

>= 30 pinned entry-market days / strategy
  eligible to design Stage 2

90 days / strategy
  preferred evidence base

Stage 2
  distribution-based targets
  requires separate ADR + human approval
```

Stage 2 thresholds must be product decisions based on accumulated evidence.
Agents must not automatically infer them from existing reference targets or
lower targets to make history pass.

### Corpus growth contract

Prepared remote artifacts do not count toward distribution readiness. A market
day counts only when all of the following are true:

```text
compact fixture committed
+ corpus-index.json entry committed
+ fixture manifest/index agreement
+ checksum/provenance validation
+ offline replay succeeds
```

Funding date-range preparation is bounded to 31 days per dispatch and executes
one independent matrix job per UTC market day. Cash discovery is similarly
date-scoped; expired futures metadata must come from verified historical archive
identity plus explicit product-spec provenance, never from guessed current
instrument metadata.

Tests that assert corpus size/readiness must derive expectations from the
versioned corpus index. They must not hard-code today's number of pinned days;
corpus growth itself is an expected repository change.

### Promotion evidence contract

Prepared compact artifacts enter the corpus only through an explicit,
review-based promotion.

Promotion must verify:

- the compact artifact is selected by exact name from an exact preparation run;
- the compact artifact is not expired and exposes an Actions SHA-256 digest;
- `derived_from_artifact.workflow_run` matches the selected source run;
- the parent preparation artifact ID belongs to that same source run;
- the parent Actions artifact digest matches the manifest SHA-256;
- `pinning_status=commit_ready`;
- only `manifest.json` plus manifest-referenced canonical evidence files are
  present;
- the existing corpus is already valid before staging;
- dataset ID, strategy/date identity, fixture path, and canonical file content
  cannot collide or drift silently.

Promotion never commits directly to `main`. It pushes a dedicated review
branch after offline validation. If repository policy permits Actions-created
pull requests, the workflow opens the PR. If the repository blocks
`GITHUB_TOKEN` from creating PRs, the workflow must emit machine-readable
`pr-handoff.json` with the exact branch/title/source evidence and succeed as a
review-handoff state rather than misclassifying the validated corpus data as a
failure. A connected GitHub integration or operator may then open the PR from
that exact branch.

Whether opened automatically or via handoff, the PR must run normal CI and
Historical Backtest Smoke. Automatic merge is not part of the promotion
contract.

Idempotent re-promotion is allowed only for the same corpus fact. Manifest JSON
formatting differences are ignored after structural parsing, while canonical
evidence files remain byte-sensitive and checksum-gated.

### Campaign promotion contract

Corpus campaigns reuse the single-artifact promotion primitive and add one
atomic transaction boundary around all items.

Required behavior:

- operator input is an explicit versioned list of exact run/artifact pairs;
- duplicate source pairs or duplicate compact artifact names fail closed;
- each compact and parent preparation artifact is verified independently;
- a campaign contains at most 31 items;
- already-present identical items may be no-ops;
- any invalid later item rolls back every fixture newly staged earlier in the
  same campaign and restores the original corpus index;
- campaign input order must not affect deterministic corpus ordering;
- evidence records per-item promotion status plus resulting 30/90 readiness;
- one changed campaign produces one review branch and one PR or PR handoff;
- the review branch must pass normal CI and Historical Backtest Smoke before
  human merge.

### Corpus distribution reporting semantics (not Stage-2 gating)

```bash
uv run python scripts/report_historical_corpus_distribution.py
```

The report must replay every valid, indexed pinned case. The report is
`economics_gate=reporting_only` regardless of the case return.

- Each distinct pinned market day currently contributes one frozen entry/exit
  case. Report `pinned_case_qualification_rate` with its case denominator.
  Market-wide opportunity arrival rate remains `null`/unassessed.
- Expected-return distributions may include qualified and rejected cases but
  must be labeled `expected_net_return_all_cases`.
- Realized returns belong only to qualified cases with sufficiently complete
  evidence. Unqualified cases and incomplete realized returns must never enter
  distributions as numerical zero.
- Funding Carry returns are separately bounded using 1-minute mark-price
  evidence; an exact funding settlement mark remains unavailable.
- Report quantiles use `(n - 1) * percentile` linear interpolation over exact
  `Decimal` data; no assessed sample means zero assessed count and null
  min/P25/P50/P90/max/mean.
- Returns reflect their case-specific holding horizons, not annualized APR.
- Store each case's dataset ID, date, manifest provenance and workflow
  actuals, including qualification, delta/risk invariants and return evidence.
- A report-generation failure is an evidence failure and must leave an error
  artifact. A poor or negative realized return, by itself, must not fail
  Stage-1 historical acceptance.

`Historical Backtest Smoke` uploads
`artifacts/historical-smoke/corpus-distribution.json` alongside the original
pinned-case gate evidence. The distribution report does not change the
ADR-0007 30/90-day eligibility or activate Stage 2.

### Selection provenance contract

A fixture may omit `selection_provenance` only for legacy Stage-1 evidence.
When the field is present, it is fail-closed evidence and must validate
independently.

Required semantics:

- source workflow run/artifact ID/name/digest identify the reviewed sampling
  evidence;
- canonical sampling-evidence SHA-256 must match deterministic replay;
- policy version, strategy, seed, study window, population and selected dates
  must match the replayed sample;
- the fixture `entry_market_date` must belong to the selected date set;
- Funding acquisition dates with selection provenance must exactly equal the
  reviewed draw;
- sampled Cash discovery may run only selected dates;
- Cash case planning must account for the complete draw as selected cases plus
  explicit exclusions; missing dates cannot disappear;
- full and compact fixture manifests must preserve the same provenance
  structurally;
- promotion/loader validation must reject strategy/date/provenance drift.

Corpus reporting classifies days as `pre_registered_sample` or
`legacy_untracked` and reports provenance coverage. This is reporting-only:
ADR-0007 readiness continues to count every valid pinned day until a separate
policy decision changes it.

### Pre-registered acquisition wave contract

`Acquire Pre-registered Historical Wave` is reusable orchestration over the
canonical acquisition composer and read-only preparation campaign.

Required behavior:

- exact Funding sampling and Cash case-plan source identities are verified by
  the composer before preparation;
- expected Funding, Cash and total item counts are derived from the composed
  `acquisition.json`, never duplicated as workflow constants;
- total items remain bounded by the acquisition manifest maximum of 31;
- each non-empty strategy side must carry matching selection provenance;
- after preparation, compact artifact total, unique artifact-name count and
  per-strategy compact counts must exactly match the derived expected counts;
- zero Funding or zero Cash is valid when the other strategy side is non-empty;
- duplicate or unexpected compact artifact identity fails closed;
- the workflow remains `actions: read` + `contents: read` and must not
  mutate the corpus, push review branches or create PRs.

The first 5 Funding + 3 Cash inputs remain workflow defaults for regression
self-testing only. They are not a reusable wave-size contract.

### Cash acquisition case planning

Cash case planning is a read-only bridge between historical FUTURES discovery
and explicit acquisition manifests.

Inputs remain operator facts:

- exact successful Cash discovery run ID;
- `future_id`;
- `expiry_at`;
- `exit_at`;
- `entry_time_utc`.

The planner must independently verify/download discovery artifacts from that
exact run and then enforce:

- supported discovery schema/status;
- unique market dates;
- explicit future ID match;
- UTC entry/exit/expiry semantics;
- `entry < exit < expiry`;
- BTC-USDT YYMMDD suffix agreement with expiry date;
- maximum 31 selected cases.

Dates with no unique FUTURES archive, future mismatch, or entry not before the
explicit exit remain explicit exclusions in evidence. They are never silently
rewritten into different strategy cases.

The planner workflow permissions are limited to `actions: read` and
`contents: read`. It must not invoke preparation workflows, mutate the corpus,
push branches, or create PRs. Its output is acquisition-ready `cash_cases`
plus diagnostics only.

### Historical market-day sampling policy

Market days intended to support future Stage-2 distribution design must be
selected before strategy outcomes are inspected.

The v1 sampler is deterministic systematic stratification with SHA-256-derived
within-stratum offsets. Inputs are limited to:

- strategy;
- inclusive UTC start/end dates;
- requested sample size;
- stable seed;
- policy version.

Sampling code must not accept prices, funding rates, basis, volatility,
qualification, returns, or other market outcomes.

Required evidence includes the complete request, population size, stratum
boundaries, hash inputs/digests, offsets and selected dates. Sampling evidence
is valid only if the repository can recompute the entire result from the
request and obtain the same payload.

Missing historical source data is an explicit exclusion. It must not trigger a
silent replacement with another date. A different replacement/resampling rule
requires a new policy version.

The read-only sampling workflow has `contents: read` only and must not invoke
acquisition/preparation, mutate the corpus, push branches, or create PRs.

Existing manually selected fixtures remain valid Stage-1 regression evidence
but must not be interpreted as an unbiased market-wide sample.

### Historical acquisition composition

Acquisition composition is a read-only bridge between reviewed inputs and an
explicit acquisition dispatch.

The composer may combine:

- either an optional explicit Funding UTC start/end range **or** an exact
  successful Funding sampling run + artifact;
- an optional exact successful Cash case-plan run + artifact.

Required behavior:

- Funding range and Funding sampling evidence are mutually exclusive;
- Funding start/end are supplied together or not at all;
- sampled Funding evidence is deterministically replayed and must use
  `strategy=funding-carry`;
- sampled Funding dates are passed as explicit chronological `market_dates`;
  intermediate unsampled dates are never inserted;
- at least one effective Funding day or selected Cash case exists;
- exact Cash case-plan run status is completed/success;
- exact artifact name resolves once, is unexpired, and exposes an Actions digest;
- downloaded case-plan schema/evidence type/counts/template are revalidated;
- reporting-only `entry_market_date` is removed before acquisition;
- the final JSON is reparsed by the normal acquisition manifest parser and
  therefore reuses the 31-item cap plus UTC/future/expiry rules;
- permissions remain `actions: read` + `contents: read`;
- the composer never dispatches preparation/acquisition, mutates the corpus,
  pushes branches, creates PRs, or merges.

The composed artifact is review input only. `Acquire Historical Campaign`
remains a separate explicit operator action.

### Historical acquisition campaign

Acquisition is an **artifact-producing but corpus-read-only** workflow layer.

The acquisition manifest may contain:

- one optional inclusive Funding UTC date range;
- explicit Cash cases with `entry_at`, `exit_at`, `future_id`, and
  `expiry_at`;
- a planner campaign prefix.

Rules:

- one acquisition is bounded to at most 31 total prepared items;
- Cash entry/exit/expiry semantics are explicit inputs and are never inferred
  from discovery output;
- Cash timestamps must be UTC and satisfy `entry < exit < expiry`;
- BTC-USDT expiry-future ID/date must agree with the explicit expiry timestamp;
- duplicate Cash entry-market dates fail closed;
- Funding/Cash jobs reuse the existing preparation workflow_call contracts;
- acquisition permissions remain `contents: read` only;
- acquisition must not modify `tests/fixtures/historical/`, push a branch,
  create a PR, or count anything as pinned readiness;
- the normalized acquisition-control artifact is part of the evidence contract;
- only after the entire acquisition run completes successfully may the
  read-only planner inventory that exact run through a `workflow_run` trigger;
- a failed/partial acquisition run must not be planned or promoted.

The acquisition run is therefore a producer of prepared candidate evidence,
not a corpus mutation step.

### Read-only candidate campaign planner

The candidate planner is a separate **read-only** artifact inventory workflow
and must never be treated as a promotion gate. Its permissions are limited to
`actions: read` and `contents: read`.

It accepts explicit successful preparation run IDs and verifies:

- the source run status is completed/success and artifact listing is complete;
- each selected compact artifact is unexpired and has an Actions SHA-256 digest;
- each compact manifest points to the exact source run;
- each parent preparation artifact belongs to the same run and its digest
  matches the compact manifest;
- the compact fixture is commit-ready, contains no unexpected files/symlinks,
  and passes canonical checksums and strategy-specific validation;
- repeated candidate strategy/date, dataset ID, or source pair fails closed;
- pinned strategy/date with a different dataset ID fails closed;
- the generated campaign waves are deterministic and have at most 31 items;
- report counts distinguish committed pinned days from unmerged candidate days;
- no corpus files, Git branches, or PRs are mutated.

The planner uses only the **committed** corpus index as its comparison baseline;
open PRs are deliberately not counted as pinned and are not automatically
deduplicated. The operator must review existing PRs before dispatching the
generated explicit campaign manifest.

`historical-campaign-planner-<run_id>` should include a review-only
`report.json`, an acquisition `inventory.json`, and the generated
`waves/*.json` manifests. CI gating remains on the committed corpus, not
on a planner projection.

## What an E2E scenario must cover

A strategy E2E scenario should exercise the real application workflow rather
than directly testing one formula:

```text
Market fixture/replay
  -> Discover
  -> Qualification
  -> OpportunityObservation
  -> StrategyPlan
  -> Paper Execution
  -> Position
  -> Risk
  -> Refresh/Close when applicable
  -> Return attribution
  -> Expected-vs-current/realized
```

The scenario must assert the relevant business target from
`tests/e2e/strategy-targets.json`.

## Strategy target rules

Targets are versioned repository facts.

Each target declares:

- scenario ID;
- strategy and strategy version;
- capital;
- minimum expected or realized return;
- maximum absolute delta percentage;
- required qualification state;
- required evidence completeness;
- required risk invariant states or allowed unassessed states.

Changing a target to make a failing strategy pass is a product/strategy change,
not a test-only change. It requires justification in the execution plan and an
ADR when the underlying return/risk semantics change.

## Determinism

CI-gating E2E must be offline and deterministic.

Allowed evidence sources:

- committed synthetic reference scenarios;
- committed historical replay fixtures with provenance and checksum;
- deterministic seeded generators when the seed is committed.

Not allowed as the only gating evidence:

- current live market prices;
- network-dependent exchange calls;
- wall-clock-sensitive profitability;
- unpinned remote datasets.

Live exchange validation may run separately as a diagnostic/non-gating workflow.

## E2E observability artifact

Every E2E run writes machine-readable evidence.

Minimum fields per scenario:

```json
{
  "scenario_id": "...",
  "strategy": "...",
  "strategy_version": "...",
  "fixture_id": "...",
  "target": {},
  "actual": {},
  "qualified": true,
  "position_state": "...",
  "risk_invariants": [],
  "return_complete": true,
  "unassessed_components": [],
  "passed": true
}
```

The report must contain actual numeric values, not only pass/fail.

CI also stores JUnit output so failures remain inspectable without reproducing
the agent session.

## Evidence semantics

Use these labels consistently:

- **verified** — a test/CI/artifact directly supports the claim;
- **assumption** — versioned input or explicit policy;
- **unassessed** — evidence is unavailable;
- **diagnostic** — informative but non-gating live/external result.

A passing unit test cannot substitute for an E2E target when the claim is about
strategy outcome.

## Failure behavior

On E2E failure:

- preserve the evidence artifact;
- do not lower the target automatically;
- compare target vs actual;
- identify whether the failure is strategy economics, market fixture,
  execution cost, risk invariant, adapter normalization, or test defect;
- record the diagnosis in the active execution plan.

## Adding a new strategy

A new strategy is incomplete until it has:

- StrategyDefinition;
- deterministic E2E scenario;
- versioned acceptance target;
- return/risk evidence;
- API/CLI path;
- CI evidence artifact.

This requirement applies before any future live-execution discussion.
