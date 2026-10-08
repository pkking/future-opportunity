# Cash 2025 Q3/Q4: exact 24-case preparation handoff

Status: manifests constructed from prior pinned, immutable selection control; **no acquisition run executed or authorized to promote by this document**.

## Inputs

- Independent 2025 Q3/Q4 source-capacity evidence: workflow 37754484440, artifact 11539801691, sha256:d1f34518fc4821d4183eb4d009722d6ec7264cc02ac4e5f12172fa16e3ae2da6.
- Q3 87/87 and Q4 90/90 unique daily FUTURES chain catalog coverage; six fixed SPOT catalog references and two exact futures exit-member identities verified.
- Quarter date pre-registration: `docs/historical-acquisition-plans/cash-2025-q3q4-24day-preregistration-v1.json`; immutable selection workflow 37755705789, artifact 11539833591, sha256:f67f1db18609c87e2cea363abf33eff7dc4592d4ab8680019ff6e1a63b206c74.
- Q3 replay hash `3449f56506669a382dbc6c7290d762a00d518a84bebc9530eb904c03e3ab70cd`; Q4 replay hash `97c3b6c4f296e5819055eace56b5c396c317e285051ea142be2dcb8799073f8b`.

## Approved pre-expiry contract-selection semantics

| Preparation wave | Cases | Future | Entry | Planned exit | Expected expiry |
|---|---:|---|---|---|---|
| Q3 2025 | 12 | BTC-USDT-250926 | selected date, 00:15 UTC | 2025-09-25 00:15 UTC | 2025-09-26 08:00 UTC |
| Q4 2025 | 12 | BTC-USDT-251226 | selected date, 00:15 UTC | 2025-12-25 00:15 UTC | 2025-12-26 08:00 UTC |

The exact case array is stored in:

- `docs/historical-acquisition-plans/cash-2025-q3-12day-wave-001.json`
- `docs/historical-acquisition-plans/cash-2025-q4-12day-wave-001.json`

Each manifest carries a replayable `pre_registered_availability_sample` tied to the **selection-control workflow artifact**, not to an unverified manual date list. The existing manifest parser validates policy, sample size, date window and evidence SHA before preparation.

## How to run (explicit only)

After the governed PR has merged to `main`, the operator may dispatch **one wave at a time** to limit source transfer and investigation blast radius:

```bash
gh workflow run prepare-cash-2025-quarter-wave.yml \
  -R pkking/future-opportunity -f wave=q3

gh workflow run prepare-cash-2025-quarter-wave.yml \
  -R pkking/future-opportunity -f wave=q4
```

The `resolve` job validates exact 12 cases and artifact-bound provenance. `acquire` calls the current reusable `acquire-historical-campaign.yml`, which produces offline compact fixture and actuals artifacts only. The summary job verifies exactly 12 compact artifacts on fully successful preparations. There is **no automatic promotion, PR merge or corpus mutation**.

## Hard evidence boundary

Canonical 2025 entry/exit catalog identity does **not** establish:
- 00:15 SPOT and FUTURES raw L2 order books on each of the 24 selected entry days;
- complete entry-to-exit trajectories / order-book staleness and fee/cost consistency;
- a historical instrument specification valid at each past date;
- complete realized return on a **qualified** sample;
- any profitable case, independent trading experiment or economic acceptance gate.

Missing, ambiguous, incompatible or timing-invalid samples must remain explicitly failed/unassessed, not replaced based on observed returns. The 24 new dates must **not** be added to the pinned corpus until prepared evidence is validated under a separate governed campaign Planner → Promotion → PR → CI/Smoke process. The economic gate stays disabled and existing Cash 30/Funding 32 historical days stay unchanged.
