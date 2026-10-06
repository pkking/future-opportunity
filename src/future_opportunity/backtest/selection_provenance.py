from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from future_opportunity.backtest.sampling import (
    HistoricalSamplingRequest,
    historical_sampling_json,
    parse_historical_sampling_evidence,
    sample_historical_market_days,
)


_SAFE_ARTIFACT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SUPPORTED_STRATEGIES = {"funding-carry", "cash-and-carry"}


@dataclass(frozen=True, slots=True)
class HistoricalSelectionSource:
    workflow_run: str
    artifact_name: str
    artifact_id: str
    artifact_digest: str

    def __post_init__(self) -> None:
        if not self.workflow_run.isdigit():
            raise ValueError("selection workflow_run must be numeric")
        if not self.artifact_id.isdigit():
            raise ValueError("selection artifact_id must be numeric")
        if _SAFE_ARTIFACT_NAME.fullmatch(self.artifact_name) is None:
            raise ValueError("selection artifact_name must be a safe name")
        _normalize_actions_digest(self.artifact_digest)


@dataclass(frozen=True, slots=True)
class HistoricalSelectionProvenance:
    schema_version: int
    selection_kind: str
    strategy: str
    source: HistoricalSelectionSource
    policy_version: str
    seed: str
    start_date: str
    end_date: str
    requested_sample_size: int
    population_size: int
    selected_market_dates: tuple[str, ...]
    sampling_evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported historical selection provenance schema")
        if self.selection_kind != "pre_registered_sample":
            raise ValueError(
                "unsupported historical selection_kind: "
                f"{self.selection_kind}"
            )
        if self.strategy not in _SUPPORTED_STRATEGIES:
            raise ValueError(
                f"unsupported historical selection strategy: {self.strategy}"
            )
        _validate_sha256(self.sampling_evidence_sha256)

        request = HistoricalSamplingRequest(
            strategy=self.strategy,
            start_date=self.start_date,
            end_date=self.end_date,
            sample_size=self.requested_sample_size,
            seed=self.seed,
            policy_version=self.policy_version,
        )
        replay = sample_historical_market_days(request)
        if replay.population_size != self.population_size:
            raise ValueError(
                "selection population_size does not match deterministic replay"
            )
        if replay.selected_dates != self.selected_market_dates:
            raise ValueError(
                "selection market dates do not match deterministic replay"
            )
        expected_sha = _sampling_evidence_sha256(replay)
        if expected_sha != self.sampling_evidence_sha256:
            raise ValueError(
                "selection sampling_evidence_sha256 does not match replay"
            )

    def contains_market_date(self, market_date: str) -> bool:
        return market_date in self.selected_market_dates


def selection_provenance_from_sampling_evidence(
    raw_sampling_evidence: Any,
    *,
    source_workflow_run: str,
    artifact_name: str,
    artifact_id: str,
    artifact_digest: str,
) -> HistoricalSelectionProvenance:
    sample = parse_historical_sampling_evidence(raw_sampling_evidence)
    return HistoricalSelectionProvenance(
        schema_version=1,
        selection_kind="pre_registered_sample",
        strategy=sample.request.strategy,
        source=HistoricalSelectionSource(
            workflow_run=source_workflow_run,
            artifact_name=artifact_name,
            artifact_id=artifact_id,
            artifact_digest=_normalize_actions_digest(artifact_digest),
        ),
        policy_version=sample.request.policy_version,
        seed=sample.request.seed,
        start_date=sample.request.start_date,
        end_date=sample.request.end_date,
        requested_sample_size=sample.request.sample_size,
        population_size=sample.population_size,
        selected_market_dates=sample.selected_dates,
        sampling_evidence_sha256=_sampling_evidence_sha256(sample),
    )


def parse_historical_selection_provenance(
    raw: Any,
) -> HistoricalSelectionProvenance:
    if not isinstance(raw, dict):
        raise TypeError("historical selection provenance must be an object")
    if set(raw) != {
        "schema_version",
        "selection_kind",
        "strategy",
        "source",
        "sampling",
    }:
        raise ValueError(
            "historical selection provenance fields differ from schema"
        )

    source_raw = raw.get("source")
    sampling_raw = raw.get("sampling")
    if not isinstance(source_raw, dict):
        raise TypeError("historical selection source must be an object")
    if not isinstance(sampling_raw, dict):
        raise TypeError("historical selection sampling must be an object")
    if set(source_raw) != {
        "workflow_run",
        "artifact_name",
        "artifact_id",
        "artifact_digest",
    }:
        raise ValueError("historical selection source fields differ from schema")
    if set(sampling_raw) != {
        "policy_version",
        "seed",
        "start_date",
        "end_date",
        "requested_sample_size",
        "population_size",
        "selected_market_dates",
        "evidence_sha256",
    }:
        raise ValueError(
            "historical selection sampling fields differ from schema"
        )

    selected = sampling_raw.get("selected_market_dates")
    if not isinstance(selected, list) or not all(
        isinstance(item, str) for item in selected
    ):
        raise TypeError(
            "historical selection selected_market_dates must be strings"
        )

    schema_version = raw.get("schema_version")
    requested = sampling_raw.get("requested_sample_size")
    population = sampling_raw.get("population_size")
    if type(schema_version) is not int:
        raise TypeError("historical selection schema_version must be integer")
    if type(requested) is not int:
        raise TypeError(
            "historical selection requested_sample_size must be integer"
        )
    if type(population) is not int:
        raise TypeError("historical selection population_size must be integer")

    return HistoricalSelectionProvenance(
        schema_version=schema_version,
        selection_kind=_required_string(raw, "selection_kind"),
        strategy=_required_string(raw, "strategy"),
        source=HistoricalSelectionSource(
            workflow_run=_required_string(source_raw, "workflow_run"),
            artifact_name=_required_string(source_raw, "artifact_name"),
            artifact_id=_required_string(source_raw, "artifact_id"),
            artifact_digest=_required_string(source_raw, "artifact_digest"),
        ),
        policy_version=_required_string(sampling_raw, "policy_version"),
        seed=_required_string(sampling_raw, "seed"),
        start_date=_required_string(sampling_raw, "start_date"),
        end_date=_required_string(sampling_raw, "end_date"),
        requested_sample_size=requested,
        population_size=population,
        selected_market_dates=tuple(selected),
        sampling_evidence_sha256=_required_string(
            sampling_raw,
            "evidence_sha256",
        ),
    )


def validate_selection_provenance_for_market_date(
    raw: Any,
    *,
    strategy: str,
    market_date: str,
) -> HistoricalSelectionProvenance:
    provenance = parse_historical_selection_provenance(raw)
    if provenance.strategy != strategy:
        raise ValueError(
            "historical selection provenance strategy mismatch: "
            f"{provenance.strategy} != {strategy}"
        )
    if not provenance.contains_market_date(market_date):
        raise ValueError(
            "historical market date is outside selection provenance: "
            f"{market_date}"
        )
    return provenance


def historical_selection_provenance_payload(
    provenance: HistoricalSelectionProvenance,
) -> dict[str, object]:
    return {
        "schema_version": provenance.schema_version,
        "selection_kind": provenance.selection_kind,
        "strategy": provenance.strategy,
        "source": {
            "workflow_run": provenance.source.workflow_run,
            "artifact_name": provenance.source.artifact_name,
            "artifact_id": provenance.source.artifact_id,
            "artifact_digest": provenance.source.artifact_digest,
        },
        "sampling": {
            "policy_version": provenance.policy_version,
            "seed": provenance.seed,
            "start_date": provenance.start_date,
            "end_date": provenance.end_date,
            "requested_sample_size": provenance.requested_sample_size,
            "population_size": provenance.population_size,
            "selected_market_dates": list(provenance.selected_market_dates),
            "evidence_sha256": provenance.sampling_evidence_sha256,
        },
    }


def _sampling_evidence_sha256(sample) -> str:
    return hashlib.sha256(
        historical_sampling_json(sample).encode("utf-8")
    ).hexdigest()


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"historical selection requires {key}")
    return value


def _normalize_actions_digest(value: str) -> str:
    raw = value.removeprefix("sha256:")
    _validate_sha256(raw)
    return "sha256:" + raw.lower()


def _validate_sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("SHA-256 must contain 64 hexadecimal characters")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("SHA-256 must be hexadecimal") from error
