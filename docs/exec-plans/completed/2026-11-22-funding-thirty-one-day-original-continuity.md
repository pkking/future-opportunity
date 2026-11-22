# Extend Option A Funding immutable original-source continuity to thirty-one days

Issue: #85
Status: COMPLETED
Owner: agent
Started: 2026-11-22
Last checkpoint: 2026-11-22

## Objective

Expand the already validated 2026-10-23..2026-11-03 (twelve complete UTC source days; eleven adjacent pairs) to 2026-10-23..2026-11-22 (thirty-one complete UTC days, thirty adjacent pairs), after confirming all nineteen new immutable releases and their independently successful `release.published` audits. Preserve existing original source provenance and frozen decision-quality limits.

## Non-goals

No exchange GETs beyond those already captured in immutable GitHub Releases, new schedule, historical backfill, independent witness, source promotion, pinned corpus growth, threshold change, economics gate, or real trading.

## Verified current facts

- main `dbe197d1b3f0d996b2176020cbbb8ab419cf1dde`, zero open PRs; [main CI #41684697537](https://github.com/pkking/future-opportunity/actions/runs/41684697537) SUCCESS.
- Previous actual read-only [12-day source ZIP review #41684148969](https://github.com/pkking/future-opportunity/actions/runs/41684148969) SUCCESS: 12/12 original days, 11/11 consistent adjacent pairs, 0 numeric revisions and 0 unassessed, derived artifact ZIP SHA256 `cef985c80d872bf7b67ead53272d3aa485fa5176cd88e6264c7516ab95d7f4d0`.
- Nineteen new immutable `funding-vps-YYYY-MM-DD` Releases exist for 2026-11-04..2026-11-22, every one with an independently successful `release.published` audit run (all SUCCESS):

| UTC day | Independent audit run | UTC day | Independent audit run |
|---|---|---|---|
| 2026-11-04 | [#41743508734](https://github.com/pkking/future-opportunity/actions/runs/41743508734) | 2026-11-14 | [#43531169666](https://github.com/pkking/future-opportunity/actions/runs/43531169666) |
| 2026-11-05 | [#41938041264](https://github.com/pkking/future-opportunity/actions/runs/41938041264) | 2026-11-15 | [#43655997882](https://github.com/pkking/future-opportunity/actions/runs/43655997882) |
| 2026-11-06 | [#42133588827](https://github.com/pkking/future-opportunity/actions/runs/42133588827) | 2026-11-16 | [#43777812411](https://github.com/pkking/future-opportunity/actions/runs/43777812411) |
| 2026-11-07 | [#42315488987](https://github.com/pkking/future-opportunity/actions/runs/42315488987) | 2026-11-17 | [#43984025723](https://github.com/pkking/future-opportunity/actions/runs/43984025723) |
| 2026-11-08 | [#42427751239](https://github.com/pkking/future-opportunity/actions/runs/42427751239) | 2026-11-18 | [#44204176696](https://github.com/pkking/future-opportunity/actions/runs/44204176696) |
| 2026-11-09 | [#42537850372](https://github.com/pkking/future-opportunity/actions/runs/42537850372) | 2026-11-19 | [#44425431757](https://github.com/pkking/future-opportunity/actions/runs/44425431757) |
| 2026-11-10 | [#42724912641](https://github.com/pkking/future-opportunity/actions/runs/42724912641) | 2026-11-20 | [#44642262760](https://github.com/pkking/future-opportunity/actions/runs/44642262760) |
| 2026-11-11 | [#42927878277](https://github.com/pkking/future-opportunity/actions/runs/42927878277) | 2026-11-21 | [#44840823881](https://github.com/pkking/future-opportunity/actions/runs/44840823881) |
| 2026-11-12 | [#43124050561](https://github.com/pkking/future-opportunity/actions/runs/43124050561) | 2026-11-22 | [#44964483532](https://github.com/pkking/future-opportunity/actions/runs/44964483532) |
| 2026-11-13 | [#43333500220](https://github.com/pkking/future-opportunity/actions/runs/43333500220) | | |

- Read-only watcher runs [#44881323311](https://github.com/pkking/future-opportunity/actions/runs/44881323311) (11-21) and [#44998176251](https://github.com/pkking/future-opportunity/actions/runs/44998176251) (11-22) SUCCESS and re-verified their rolling three-day windows; the isolated 11-20 watcher [#44697120922](https://github.com/pkking/future-opportunity/actions/runs/44697120922) failed fast (~1.5s, transient GitHub API access failure before any report), the same failure class as the previously classified [2026-10-26 watcher 403](https://github.com/pkking/future-opportunity/actions/runs/40273247940); it is a watcher-only incident, not a missing immutable Release, and the 11-20 Release plus its independent audit #44642262760 succeeded.
- Separate best-effort GitHub scheduled pre-entry collectors keep failing their hard 00:15 UTC clock gate (latest [#44980760730](https://github.com/pkking/future-opportunity/actions/runs/44980760730)); not a VPS source chain incident, never backfilled.
- **All nineteen new adjacent pairs 11/03→04 .. 11/21→22 remain UNASSESSED until the real postmerge GitHub-only replay.** Watcher health and release metadata do not establish numeric overlap consistency.

## Required sources

- AGENTS.md, docs/design-baseline-v0.1.md, docs/v0-implementation-status.md
- docs/agents/workflow.md, docs/agents/testing.md, docs/adr/0008-funding-stage2-historical-distribution-gate.md
- docs/exec-plans/active/2026-10-17-funding-regime-independent-coverage.md
- .github/workflows/review-funding-source-continuity.yml, scripts/report_funding_source_continuity.py, tests/test_funding_source_continuity.py

## Constraints

- Only read original immutable GitHub ZIPs with matching successful independent release event audit and source SHA256 per day; fail closed on any missing original, audit, API completeness, numerical revision or invalid historical confirmation.
- Preserve workflow_dispatch manual exact 2..90 completed UTC date scope, workflow-file-only one-shot main-push trigger, no cron, GitHub read-only permissions and no source writes. The previous 12-day main-push review job completed in 27 seconds; thirty-one days stay far inside the existing 25-minute timeout, so no timeout change is required.
- Preserve frozen Funding sign / spot trailing 100bps volatility 2×2, no market-wide opportunity arrival claims.
- `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`, Funding pinned 32/90, Cash 66; no Stage-2 economic gate or trade.

## Acceptance criteria

- [x] Extend one-shot workflow main-push default to `2026-10-23..2026-11-22` inclusive (31 original days, 30 adjacent pairs).
- [x] Offline regression test enforces exact 31 days, 30 pairs and unchanged manual read-only/safety constraints.
- [x] Exact final PR head has all 5 required CI checks plus Historical Smoke SUCCESS.
- [x] After merge, actual main-push GitHub original ZIP report confirms all 31 day statuses and 30 adjacent comparison states; report exact pair populations, numerical/confirmation revision findings, unassessed count and original/derived SHA256; do not assume consistency ahead of time.
- [x] Record audited outcome in Issue #85, then archive evidence and update parent plan in a separate completion-only PR; parent Issue remains open.

## Implementation slices

- [x] 1. Modify workflow bounded default date only.
- [x] 2. Modify exact-date governance regression test.
- [x] 3. PR, final-head CI/Historical Smoke, merge if authorized, verify real 31-day source report.
- [x] 4. Comment Issue #85 and archive in separately verified PR.

## Verification matrix

| Gate | State |
|---|---|
| Final PR head 5 required CI checks | SUCCESS, [CI #45037753837](https://github.com/pkking/future-opportunity/actions/runs/45037753837) (PR #169) |
| Final PR head Historical Smoke | SUCCESS, [run #45037753956](https://github.com/pkking/future-opportunity/actions/runs/45037753956) |
| Real source continuity main-push report | SUCCESS, [run #45053416810](https://github.com/pkking/future-opportunity/actions/runs/45053416810): 31/31 days, 30/30 consistent pairs, 0 revisions, 0 unassessed |
| Postmerge main CI | SUCCESS, [#45037830948](https://github.com/pkking/future-opportunity/actions/runs/45037830948), [#45040654647](https://github.com/pkking/future-opportunity/actions/runs/45040654647), [#45043683723](https://github.com/pkking/future-opportunity/actions/runs/45043683723), [#45044742588](https://github.com/pkking/future-opportunity/actions/runs/45044742588), [#45053344096](https://github.com/pkking/future-opportunity/actions/runs/45053344096) |

## Decision gates

None for bounded read-only Option A extension. New trust authorities, alternate witness, changed evidence admission, markets sampling schedule, historical promotion, economic/real-trade permission remain unapproved.

## Evidence log

- 2026-11-22: Confirmed 31 consecutive immutable `funding-vps-*` Releases 2026-10-23..2026-11-22 via GitHub API; all 19 new-day independent release audits SUCCESS; main CI green on `dbe197d1b3f0d996b2176020cbbb8ab419cf1dde`; zero open PRs. Classified 11-20 watcher failure as transient watcher-only API incident (re-verified by 11-21/11-22 successful watchers). New adjacent-pair overlap consistency remains unassessed.
- 2026-11-22: [PR #169](https://github.com/pkking/future-opportunity/pull/169) merged `469cd852` after final-head [CI #45037753837](https://github.com/pkking/future-opportunity/actions/runs/45037753837) all five required checks SUCCESS and [Historical Smoke #45037753956](https://github.com/pkking/future-opportunity/actions/runs/45037753956) SUCCESS; postmerge [main CI #45037830948](https://github.com/pkking/future-opportunity/actions/runs/45037830948) SUCCESS.
- 2026-11-22: **Real main-push 31-day review [run #45037830949](https://github.com/pkking/future-opportunity/actions/runs/45037830949) FAILED — genuine new engineering fact.** The derived artifact (ID `14759204926`) shows `26/30` pairs consistent, `0` revisions, `4` UNASSESSED pairs; days 2026-11-19..22 were classified "missing matching successful independent original-source audit" although all four independent audits are SUCCESS with matching `head_branch`/`event`/timestamps. Root cause diagnosed by local reproduction: after ~26 days of consecutive per-day requests (release metadata + two asset downloads each, plus one original-ZIP fetch in the continuity pass), GitHub returned intermittent HTTP 403 secondary rate limiting; `check_day`/`verify_release` convert 403 into per-day UNASSESSED receipts, which the custody ledger then reported as missing audits. The prior 12-day run (~60 requests) never tripped the threshold; 31 days (~150+ requests in ~20s) did. Core quota was never exhausted (4600+/5000 remaining) — secondary abuse-rate limiting, not quota exhaustion.
- 2026-11-22: [PR #170](https://github.com/pkking/future-opportunity/pull/170) merged `d429357` (final-head [CI #45040570902](https://github.com/pkking/future-opportunity/actions/runs/45040570902) 5/5 SUCCESS, [Historical Smoke #45040570993](https://github.com/pkking/future-opportunity/actions/runs/45040570993) SUCCESS; postmerge [main CI #45040654647](https://github.com/pkking/future-opportunity/actions/runs/45040654647) SUCCESS). Adds per-day pacing (ledger 5s/day, continuity 2s/day, injected `pause`, no-op default) and bounded 30s/60s retry for retryable transport failures and GitHub-API-HTTP receipts; retry exhaustion keeps UNASSESSED exactly as before.
- 2026-11-22: Dispatched 31-day review [run #45040702446](https://github.com/pkking/future-opportunity/actions/runs/45040702446) on merged fix head `d429357`: STILL FAIL-CLOSED, same 4 tail days (26/30 pairs). Local reproduction showed persistent 403s during sustained load with recovery ~3 minutes after requests stop — retrying while the run keeps drawing from the rolling bucket never drains it. Observed secondary threshold ≈ 80 release-asset downloads per rolling window; the design made 3 downloads/day (custody manifest+ZIP, continuity ZIP refetch) = 93 for 31 days.
- 2026-11-22: [PR #171](https://github.com/pkking/future-opportunity/pull/171) merged `dd31a4f` (final-head [CI #45043600363](https://github.com/pkking/future-opportunity/actions/runs/45043600363) 5/5 SUCCESS, [Historical Smoke #45043600290](https://github.com/pkking/future-opportunity/actions/runs/45043600290) SUCCESS; postmerge [main CI #45043683723](https://github.com/pkking/future-opportunity/actions/runs/45043683723) SUCCESS). Adds `_AssetCacheTransport`: production `main()` deduplicates the custody pass's immutable `releases/download` responses for the continuity pass's refetch (3→2 downloads/day ≈ 62 for 31 days); API/error responses never cached; all digest/shape validation unchanged on served bytes.
- 2026-11-22: Dispatched again [run #45043774200](https://github.com/pkking/future-opportunity/actions/runs/45043774200) on `dd31a4f`: **30/31 days verified, 29/30 pairs consistent, 0 revisions**, only the final day 2026-11-22 UNASSESSED ("missing matching successful independent original-source audit" — a throttled tail after 30 paced days). Local isolated re-check of 2026-11-22 immediately returns `RELEASE_AND_INDEPENDENT_AUDIT_VERIFIED`, proving the day's evidence is fine and the failure is purely tail throttling: 5s/day pace still leaves ~90 requests in a ~3-minute rolling window, and 30s+60s backoff is shorter than the observed drain time.
- 2026-11-22: Dispatched [run #45044821371](https://github.com/pkking/future-opportunity/actions/runs/45044821371) on `549d324`: **28/31 days verified, 27/30 pairs consistent, 0 revisions**, days 11-20..22 UNASSESSED. Total step duration 20 minutes — retries exhausted even at 30/60/180s backoff, which a ~3-minute rolling secondary limit cannot explain. Full local reproduction with per-URL tracing then captured the REAL root cause: the 403 body reads `API rate limit exceeded for 198.44.91.209 ... Authenticated requests get a higher rate limit` with `x-ratelimit-remaining: 0`. `check_day`/`verify_release` tag requests reached api.github.com **unauthenticated** (only the audit-history listing carried the token), falling into the shared **60/hour unauthenticated per-IP bucket**. A 31-day review issues ~62 unauthenticated API calls — just over the limit, with failure position drifting by unrelated tenants on shared runner/proxy IPs. This also retroactively explains the earlier tail-day failures and why 12-day (24 calls) runs always passed.
- 2026-11-22 (final fix): both production clients now authenticate every request (`Authorization: Bearer <token>` at client level; per-request `Accept` headers merge normally; permissions remain `contents: read` + `actions: read`). Added `build_authenticated_client` in the ledger script and an authenticated header in the continuity script's cached client; new test pins authenticated clients in both mains. **Full local 31-day verification then completed end-to-end: `status=OVERLAP_VALUES_CONSISTENT_ONLY`, 31/31 audited days, 30/30 consistent pairs, 0 revisions, 0 UNASSESSED.** Regime inventory across the 31 observed days: nonnegative/high 29, negative/high 2 (**2026-11-18 and 2026-11-20 — first negative-Funding observations in this prospective source research**), negative/low 0, nonnegative/low 0. Full 30-pair overlap table recorded for the archive PR.

## Deviations and discoveries

- **2026-11-22 secondary rate limit fix (in progress).** The 12-day-proven request pattern does not scale to 31 days. Fix design, preserving all fail-closed semantics:
  - `scripts/report_funding_prospective_custody_ledger.py`: per-day pace (`DAY_PACE_SECONDS=5`, injected `pause`, default no-op for tests/library callers), bounded retry with 30s/60s backoff for retryable transport failures (HTTP 403/429/5xx, request errors) and for `check_day` receipts whose reason is a GitHub API HTTP failure; retry exhaustion keeps the day UNASSESSED exactly as before; audit-history fetch also retried.
  - `scripts/report_funding_source_continuity.py`: per-day original-ZIP fetch pace (`FETCH_PACE_SECONDS=2`) and bounded retry on transport-level errors only; digest/shape integrity failures still fail immediately.
  - New offline tests: transient 403 recovers with exactly one backoff and pacing; persistent 403 exhausts retries and stays UNASSESSED; existing parametrized audit-failure test updated for retryable codes (3 calls) vs permanent 401 (1 call).
  - CI `timeout-minutes: 25` unchanged: worst-case wall time = 31×(5+2)s pace + bounded retries ≪ 25 min; local live run in progress to confirm end-to-end behavior before the fix PR.

## 2026-11-22 — authoritative thirty-one-day evidence and outcome

- Final authoritative read-only review [run #45053416810](https://github.com/pkking/future-opportunity/actions/runs/45053416810) SUCCESS on main `2913dc1` (workflow_dispatch after the authenticated-client fix merged): `checked_day_count=31`, `github_audited_day_count=31`, `expected_pair_count=30`, `consistent_pair_count=30`, `revision_pair_count=0`, `unassessed_pair_count=0`, `every_adjacent_pair_assessed=true`, status `OVERLAP_VALUES_CONSISTENT_ONLY`. Derived artifact ID `14766557435`.
- Outcome recorded on [Issue #85](https://github.com/pkking/future-opportunity/issues/85#issuecomment-7083479816).
- Engineering chain that made it possible, each step forced by genuine CI evidence: [#169](https://github.com/pkking/future-opportunity/pull/169) window extension (CI 5/5 + Smoke), [#170](https://github.com/pkking/future-opportunity/pull/170) pacing+bounded retry, [#171](https://github.com/pkking/future-opportunity/pull/171) immutable asset-download dedupe, [#172](https://github.com/pkking/future-opportunity/pull/172) longer tail backoff, [#173](https://github.com/pkking/future-opportunity/pull/173) authenticated every GitHub read (root cause: ~62 unauthenticated per-day tag calls vs the shared 60/hour per-IP bucket). Intermediate real review runs [#45037830949](https://github.com/pkking/future-opportunity/actions/runs/45037830949), [#45040702446](https://github.com/pkking/future-opportunity/actions/runs/45040702446), [#45043774200](https://github.com/pkking/future-opportunity/actions/runs/45043774200) and [#45044821371](https://github.com/pkking/future-opportunity/actions/runs/45044821371) each failed closed and are retained as honest engineering evidence; none was reinterpreted as market data.

Full 30-pair adjacent overlap table (overlapping settled Funding records, zero numeric revisions each pair):

| UTC adjacent pair | Overlap | UTC adjacent pair | Overlap |
|---|---:|---|---:|
| 10-23→24 | 284 | 11-03→04 | 275 |
| 10-24→25 | 286 | 11-04→05 | 278 |
| 10-25→26 | 290 | 11-05→06 | 281 |
| 10-26→27 | 293 | 11-06→07 | 274 |
| 10-27→28 | 275 | 11-07→08 | 277 |
| 10-28→29 | 277 | 11-08→09 | 281 |
| 10-29→30 | 281 | 11-09→10 | 284 |
| 10-30→31 | 284 | 11-10→11 | 275 |
| 10-31→11-01 | 287 | 11-11→12 | 277 |
| 11-01→02 | 290 | 11-12→13 | 280 |
| 11-02→03 | 292 | 11-13→14 | 283 |
| | | 11-14→15 | 286 |
| | | 11-15→16 | 289 |
| | | 11-16→17 | 292 |
| | | 11-17→18 | 275 |
| | | 11-18→19 | 278 |
| | | 11-19→20 | 275 |
| | | 11-20→21 | 277 |
| | | 11-21→22 | 280 |

- Fixed source regime classification over the 31 observed days: `nonnegative_high_volatility=29`, `negative_high_volatility=2` (**2026-11-18, 2026-11-20 — first negative-Funding observations in this prospective source research**), `negative_low_volatility=0`, `nonnegative_low_volatility=0`.
- **Unresolved**: this is GitHub custody of VPS-supplied bytes with stable overlap, not exchange-signed OKX first-publication proof; `exchange_signed=false`, `point_in_time_publication_verified=false`, `acquisition_approved=false`, `promotion_approved=false`. Funding pinned 32/90, Cash 66; Stage-2 economics gate disabled; real trading prohibited. Negative/low stratum still unobserved; Issue #85 stays OPEN/BLOCKED_EVIDENCE.

## Resume from here

Verified and archived. Continue from parent Issue #85's long-lived Option A plan for genuinely new completed UTC source days (next extension: any new dates after 2026-11-22). Do not replay this completed 31-day window solely to create new artifacts; no backdating, no late GETs, no reinterpretation of absent days.

## Completion

Final commits: `469cd852` (#169), `d429357` (#170), `dd31a4f` (#171), `549d324` (#172), `2913dc1` (#173).
Authoritative evidence: [run #45053416810](https://github.com/pkking/future-opportunity/actions/runs/45053416810) SUCCESS, derived artifact ID `14766557435`.
Remaining unassessed: independent OKX first-publication timing/signatures, three missing prospective market-state strata (including the first-ever negative/low observation), Funding 32/90 pinned days, Cash 66; no historical source promotion, numeric Stage-2 economics approval, market-wide opportunity-frequency inference or real trading.
