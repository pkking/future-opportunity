from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any


def plan_stratified_evidence_days(
    eligible: Mapping[str, str | None],
    *,
    strata: Sequence[str],
    quota_per_stratum: int,
    seed: str,
    unavailable_dates: Sequence[str] = (),
) -> dict[str, Any]:
    """Outcome-blind deterministic selection from pre-labelled market dates.

    The labels MUST come from ex-ante observable evidence, frozen before
    looking at qualification/expected/realized returns.
    """
    labels = tuple(strata)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("strata must be non-empty and unique")
    if type(quota_per_stratum) is not int or quota_per_stratum <= 0:
        raise ValueError("quota_per_stratum must be a positive integer")
    if not seed:
        raise ValueError("a frozen selection seed is required")
    unavailable = set(unavailable_dates)
    if len(unavailable) != len(unavailable_dates):
        raise ValueError("unavailable dates must be unique")
    if unavailable - set(eligible):
        raise ValueError("unavailable date is not in the observed population")
    buckets: dict[str, list[str]] = defaultdict(list)
    unassessed: list[str] = []
    for market_date, stratum in eligible.items():
        if date.fromisoformat(market_date).isoformat() != market_date:
            raise ValueError("invalid canonical market date")
        if stratum is None:
            unassessed.append(market_date)
        elif stratum not in labels:
            raise ValueError("unrecognized regime or cohort label")
        else:
            buckets[stratum].append(market_date)
    selected: dict[str, list[str]] = {}
    shortfalls: dict[str, int] = {}
    for stratum in labels:
        ready = (d for d in buckets[stratum] if d not in unavailable)
        ranked = sorted(
            ready,
            key=lambda d: (
                hashlib.sha256(
                    f"evidence-stratified-v1|{seed}|{stratum}|{d}".encode()
                ).hexdigest(), d,
            ),
        )
        selected[stratum] = sorted(ranked[:quota_per_stratum])
        shortfalls[stratum] = max(quota_per_stratum - len(ranked), 0)
    return {
        "schema_version": 1,
        "selection_policy": "evidence-stratified-v1",
        "seed": seed,
        "strata": list(labels),
        "quota_per_stratum": quota_per_stratum,
        "observed_population_count": len(eligible),
        "stratum_population_counts": {
            s: len(buckets[s]) for s in labels
        },
        "unavailable_dates": sorted(unavailable),
        "unassessed_label_dates": sorted(unassessed),
        "selected_by_stratum": selected,
        "shortfall_by_stratum": shortfalls,
        "capacity_sufficient": not any(shortfalls.values()),
        "selection_semantics": (
            "pre-registered source/ex-ante label only; "
            "no economics or outcome input; no replacement"
        ),
    }
