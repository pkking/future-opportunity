from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from future_opportunity.backtest.campaign import (
    HistoricalCampaignManifest,
    parse_historical_campaign_manifest,
)


_FUNDING_ARTIFACT = re.compile(
    r"^okx-btc-funding-compact-(\d{4}-\d{2}-\d{2})$"
)


@dataclass(frozen=True, slots=True)
class FundingPromotionWaveHandoff:
    planner_run_id: str
    planner_artifact_name: str
    planner_artifact_id: int
    planner_artifact_digest: str
    wave_file: str
    campaign: HistoricalCampaignManifest

    def __post_init__(self) -> None:
        if not self.planner_run_id.isdigit():
            raise ValueError("planner_run_id must be numeric")
        if self.planner_artifact_id <= 0:
            raise ValueError("planner_artifact_id must be positive")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.planner_artifact_digest):
            raise ValueError("planner_artifact_digest must be sha256")
        if not re.fullmatch(r"waves/[A-Za-z0-9][A-Za-z0-9._-]*\.json", self.wave_file):
            raise ValueError("wave_file must be a canonical planner wave path")


@dataclass(frozen=True, slots=True)
class FundingPromotionHandoff:
    schema_version: int
    handoff_id: str
    target_workflow: str
    waves: tuple[FundingPromotionWaveHandoff, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported Funding promotion handoff schema")
        if self.target_workflow != ".github/workflows/promote-planned-historical-wave.yml":
            raise ValueError("handoff must target Promote Planned Historical Wave")
        if len(self.waves) != 2:
            raise ValueError("Funding promotion handoff requires exactly two waves")

    def funding_dates(self) -> tuple[str, ...]:
        result: list[str] = []
        for wave in self.waves:
            for item in wave.campaign.items:
                match = _FUNDING_ARTIFACT.fullmatch(item.compact_artifact_name)
                if match is None:
                    raise ValueError(
                        "Funding handoff contains non-Funding compact artifact"
                    )
                result.append(match.group(1))
        if len(result) != len(set(result)):
            raise ValueError("Funding promotion handoff contains duplicate dates")
        return tuple(result)


def load_funding_promotion_handoff(path: Path) -> FundingPromotionHandoff:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("Funding promotion handoff must be an object")
    expected = {"schema_version", "handoff_id", "target_workflow", "waves"}
    if set(raw) != expected:
        raise ValueError("Funding promotion handoff fields differ from schema")
    waves_raw = raw["waves"]
    if not isinstance(waves_raw, list):
        raise TypeError("Funding promotion handoff waves must be a list")

    waves: list[FundingPromotionWaveHandoff] = []
    for position, item in enumerate(waves_raw):
        if not isinstance(item, dict):
            raise TypeError(f"Funding promotion wave {position} must be an object")
        expected_wave = {
            "planner_run_id",
            "planner_artifact_name",
            "planner_artifact_id",
            "planner_artifact_digest",
            "wave_file",
            "campaign",
        }
        if set(item) != expected_wave:
            raise ValueError(
                f"Funding promotion wave {position} fields differ from schema"
            )
        campaign = parse_historical_campaign_manifest(item["campaign"])
        waves.append(
            FundingPromotionWaveHandoff(
                planner_run_id=str(item["planner_run_id"]),
                planner_artifact_name=str(item["planner_artifact_name"]),
                planner_artifact_id=int(item["planner_artifact_id"]),
                planner_artifact_digest=str(item["planner_artifact_digest"]),
                wave_file=str(item["wave_file"]),
                campaign=campaign,
            )
        )

    handoff = FundingPromotionHandoff(
        schema_version=int(raw["schema_version"]),
        handoff_id=str(raw["handoff_id"]),
        target_workflow=str(raw["target_workflow"]),
        waves=tuple(waves),
    )
    dates = handoff.funding_dates()
    if len(dates) != 24:
        raise ValueError("Funding promotion handoff must contain exactly 24 dates")
    if any(len(wave.campaign.items) != 12 for wave in handoff.waves):
        raise ValueError("each Funding promotion wave must contain exactly 12 items")
    return handoff
