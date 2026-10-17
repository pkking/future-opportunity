# CI compatibility after frozen Cash Q3/Q4 corpus growth

Issue: #69
Status: COMPLETED
Owner: agent
Started: 2026-10-17
Last checkpoint: 2026-10-17

## Objective
Preserve strict frozen source-selection anti-drift and no-unreviewed-overlap
constraints while making corpus-indexed regression tests work *before and
after* explicit, source-matching, reviewed 24-day 2025 Cash promotion.
Do not relax selection validation or fabricate historical evidence.

## Non-goals
No production validator changes, strategy/ADR/economic threshold changes,
no current-source date substitutions, no changes to the 24 compact
source files, no direct main merge and no trading enablement.

## Evidence and current facts
- Operator staging Run [39021366976](https://github.com/pkking/future-opportunity/actions/runs/39021366976)
  succeeded, exact planner Run 39020272173, Q3 source 39016938121,
  Q4 source 39018358844. Evidence ZIP 12096916071, SHA-256
  b1fef132db32c504be2120ab29c6866624aa55682f0b32240af108e550592a6a.
- 24/24 `promotion.json` statuses = staged; offline pinned historical
  smoke `gate.passed=true`; branch
  `historical-corpus-campaign/cash-2025-q3-q4-review-001-wave-001-39021366976-1`
  commit `dd2d0bfaca84253f59fc627190a0ff42fb7f64e0`
  compares against `main` in exactly 121 historical-fixture files:
  one index and 24 × five compact files. Main 30 Cash / 32 Funding,
  proposed branch 54 Cash / 32 Funding; no original day removed.
- GitHub Actions could not create PR due
  `repository_policy_blocks_actions_pr_creation`;
  connector created [PR #82](https://github.com/pkking/future-opportunity/pull/82)
  pointing at exact branch.
- Initial PR-head [CI 39021604899](https://github.com/pkking/future-opportunity/actions/runs/39021604899)
  failed **five code-level regression tests** (443 passed):
  old selection tests read the *current* corpus index and require 24
  preselected 2025 days to be unpinned, which is false after the
  intended promotion, while distribution test hardcodes prior snapshot
  Cash pre-registered count 27, qualified/realized count 8 and exactly
  two 2026 expiry cohorts. Plan-integrity, static, API, E2E and offline
  historical smoke all SUCCESS.
- `validate_cash_prior_quarter_preregistration` still intentionally
  refuses a selected date already in the passed pinned-date set; this
  validator must remain strict. The source selection policy is frozen
  in `docs/historical-acquisition-plans/cash-2025-q3q4-24day-preregistration-v1.json`.
  Original Q3/Q4 acquisition manifests carry the only admissible
  selection provenance. Pinned 2025 Q3/Q4 manifests must match it
  *exactly* when excluding cohort-identical already-promoted records
  from an initial, historical pre-promotion test context.

## Acceptance criteria
- [x] Tests inspect the actual pinned corpus; only exact frozen-source
      2025 records may be categorized as already-promoted cohort
      records. Reject missing/altered provenance, wrong future/exit,
      partial atomic cohort, duplicate and unrelated overlap.
- [x] Pre-promotion deterministic replay retains the exact 24 frozen
      days and population/sampling proofs. Standalone validator must
      still reject any selected day in its pinned-date argument;
      drift/source tampering/governance negatives stay intact.
- [x] Distribution tests reflect 2025 Q3 and Q4 each independently
      (12 cases, Q3 9 qualified + 3 unqualified, Q4 7 qualified +
      5 unqualified); retain the distinct 2026 quarters and full
      qualification denominator including eight rejected records.
      Reporting_only, unassessed risk/market-wide, reference gate
      disabled remain enforced.
- [x] CI final head: static, code-level, API, E2E, Agent plan integrity,
      Historical Backtest Smoke success. Leave PR #82 OPEN for explicit
      human review/approval/merge. Main pinned counts unchanged.

## Implementation slices
- [x] 1. Add provenance-aware tests for pre- and post-promotion
      freeze replay contexts; never change strict production validator.
- [x] 2. Adjust distribution report regression to assert actual 2025
      and preexisting 2026 cohorts and explicit 54/32 proposed counts.
- [x] 3. Update this plan with CI evidence, create a final-head
      checkpoint and issue comment. No automatic merge.

## Verification matrix
| Gate | Evidence | Status |
|---|---|---|
| Targeted | Targeted regression paths included in code-level CI 39022005642 | PASS |
| Static | CI static+architecture, 39022005642 | PASS on initial fixed head |
| Code | CI 39022005642, 448 passed, 1 warning | PASS on initial fixed head |
| API | CI 39022005642 | PASS on initial fixed head |
| E2E | CI 39022005642 | PASS on initial fixed head |
| Plan | CI 39022005642 | PASS on initial fixed head |
| Historical | Historical Smoke 39022005591 | PASS on initial fixed head |

## Review checkpoint
- Original staged branch commit: `dd2d0bfaca84253f59fc627190a0ff42fb7f64e0`.
- [PR #82](https://github.com/pkking/future-opportunity/pull/82)
  created from the exact promotion workflow handoff due to GitHub Actions
  `repository_policy_blocks_actions_pr_creation`.
- Original PR code-level CI [39021604899](https://github.com/pkking/future-opportunity/actions/runs/39021604899)
  failed five outdated tests with 443 passed, not a source artifact failure.
- Fixed initial head `fdecebbb898f9948ddea0519c2841910c2baa18f`:
  [CI 39022005642](https://github.com/pkking/future-opportunity/actions/runs/39022005642)
  SUCCESS (448 passed, 1 warning; static, API, E2E, plan integrity all pass),
  [Historical Smoke 39022005591](https://github.com/pkking/future-opportunity/actions/runs/39022005591)
  SUCCESS.
- Production `validate_cash_prior_quarter_preregistration` remains
  **unchanged** and still rejects pinned overlaps. Test code only
  reconstructs a historical pre-promotion baseline from source-identical
  already-pinned fixtures and requires either zero or all 24 cohort
  items. Tampered or partial promotion remains fail-closed. Historical
  reporting now explicitly asserts 2025 Q3 (9/3), Q4 (7/5) plus
  unchanged 2026 cohorts; 8 rejected examples retained.
- **No main corpus mutation**, no automatic merge, no change to ADR,
  live trading, reference economics or stage-2 gates.

## Decision gates
The user authorized a workflow that stages a review PR, NOT the final
merge. Human review and explicit merge approval are separate. Do not
misinterpret `Stage-2 decision quality ready` as approved economics
thresholds; no live orders.

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
Implementation and regression testing complete. Waiting for final-head CI after
checkpoint, then explicit human review/merge of PR #82 and postmerge main proof.

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
