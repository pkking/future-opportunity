from __future__ import annotations

from pathlib import Path

from future_opportunity.backtest.funding_promotion_handoff import (
    load_funding_promotion_handoff,
)


HANDOFF = Path(
    "docs/historical-promotion-handoffs/"
    "stage2-funding-waves-002-003.json"
)


def test_funding_promotion_handoff_is_exact_and_non_overlapping() -> None:
    handoff = load_funding_promotion_handoff(HANDOFF)

    assert handoff.handoff_id == "stage2-funding-waves-002-003"
    assert handoff.target_workflow == (
        ".github/workflows/promote-planned-historical-wave.yml"
    )
    assert [wave.planner_run_id for wave in handoff.waves] == [
        "37596889005",
        "37600237687",
    ]
    assert [wave.campaign.campaign_id for wave in handoff.waves] == [
        "preregistered-review-002-wave-001",
        "preregistered-review-003-wave-001",
    ]
    assert [wave.wave_file for wave in handoff.waves] == [
        "waves/preregistered-review-002-wave-001.json",
        "waves/preregistered-review-003-wave-001.json",
    ]

    dates = handoff.funding_dates()
    assert len(dates) == 24
    assert len(set(dates)) == 24
    assert dates[:12] == (
        "2026-02-07",
        "2026-02-14",
        "2026-02-16",
        "2026-02-23",
        "2026-03-05",
        "2026-03-10",
        "2026-03-22",
        "2026-03-28",
        "2026-04-03",
        "2026-04-08",
        "2026-04-20",
        "2026-04-27",
    )
    assert dates[12:] == (
        "2026-05-05",
        "2026-05-16",
        "2026-05-29",
        "2026-06-02",
        "2026-06-15",
        "2026-06-23",
        "2026-07-04",
        "2026-07-12",
        "2026-07-25",
        "2026-08-08",
        "2026-08-19",
        "2026-08-29",
    )


def test_funding_promotion_handoff_pins_planner_artifact_digests() -> None:
    handoff = load_funding_promotion_handoff(HANDOFF)

    assert [
        (wave.planner_artifact_id, wave.planner_artifact_digest)
        for wave in handoff.waves
    ] == [
        (
            11470314464,
            "sha256:8f1189786a43d9bf5ef265d99f0a07544357a6f7ab2c097576329d67246ed187",
        ),
        (
            11472665816,
            "sha256:8aa8e9b5b3e82a2226b8334f5fdccda870e201ff2b832582a5cc601742645850",
        ),
    ]


def test_handoff_contains_only_exact_source_runs() -> None:
    handoff = load_funding_promotion_handoff(HANDOFF)

    assert {
        item.source_workflow_run
        for item in handoff.waves[0].campaign.items
    } == {"37593545181"}
    assert {
        item.source_workflow_run
        for item in handoff.waves[1].campaign.items
    } == {"37597427096"}
