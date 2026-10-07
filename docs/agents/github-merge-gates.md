# GitHub-first Agent Plan Integrity: repository administration

The PR validator is only a required merge gate **after a repository administrator enables it**. The available GitHub integration can change contents, Actions and Issues, but cannot create/edit repository Rulesets.

## Ruleset setup (owner/admin action)

On GitHub: **Settings → Rules → Rulesets → New branch ruleset**.

- Name: `main-agent-governance`.
- Enforcement: Active.
- Target branches: `main`.
- Require a pull request before merging; do not allow ordinary direct pushes.
- Require status checks to pass before merging, selecting these exact job names from successful PR runs:
  - `Agent plan integrity`
  - `Static and architecture safety`
  - `Code-level tests`
  - `API contract tests`
  - `E2E strategy acceptance`
- Require branch up to date before merging unless a compatible merge queue is intentionally configured.
- Block force pushes and branch deletion.
- Disable bypass for agents and automation accounts; reserve emergency admin bypass only under an explicit human process.

Existing historical PRs #1-#4 only qualify for the code-level legacy exception when their entire diff remains under `tests/fixtures/historical/`; their existing CI and Historical Backtest Smoke checks are still required for correctness. Do not enable a mandatory per-PR Historical Smoke status check unless that job is guaranteed to run for all relevant PR paths: skipped/missing checks require careful policy design.

## Verify after activation

1. Inspect `GET /repos/pkking/future-opportunity/rulesets`; confirm active enforcement on `main`.
2. Open an intentional negative PR with no `Issue:` or `Plan:` lines (do not merge it). It must fail `Agent plan integrity`.
3. Confirm the negative PR cannot merge despite other jobs passing.
4. Verify a fully linked PR receives the green check and can proceed through standard review.
5. Record Ruleset ID, enforcement and test PR links in Issue #6.

## Trust boundary

PRs can modify repository files, including `scripts/validate_agent_plan.py` and CI workflows. The GitHub-hosted job is therefore only a consistency check, not a security boundary against malicious contributors. For robust enforcement, protect those paths with CODEOWNERS and required human reviews, or move the privileged required Check to a trusted workflow/reusable workflow that PR authors cannot alter. Never run untrusted PR code with write permissions or long-lived secrets.
