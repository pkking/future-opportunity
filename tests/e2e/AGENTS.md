# E2E Agent Instructions

Scope: `tests/e2e/`.

These rules add to the repository root `AGENTS.md`.

- E2E is business acceptance evidence, not a place for unit tests.
- Exercise application workflows from Discover through Position/Return/Risk and
  Close where the strategy lifecycle supports it.
- Do not call live exchange APIs in CI-gating E2E.
- Read targets from `strategy-targets.json`; do not duplicate threshold values
  only inside Python tests.
- Every scenario records actual numeric metrics through the evidence collector.
- Keep fixture/scenario identity stable and versioned.
- Never lower a target merely to make CI green.
- Funding Carry may intentionally end with partial return evidence while funding
  settlement is unassessed; assert that explicitly.
- Cash-and-Carry delivery scenarios must distinguish basis convergence from
  post-delivery residual directional PnL.
- A failed target must remain observable in the JSON/JUnit CI artifacts.
