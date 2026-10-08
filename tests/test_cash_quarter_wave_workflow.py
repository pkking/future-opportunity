from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/prepare-cash-stage2-quarter-wave.yml"


def test_quarter_wave_workflow_is_explicit_dispatch_only() -> None:
    text = WORKFLOW.read_text()

    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "type: choice" in text
    assert "- q1" in text
    assert "- q2" in text


def test_quarter_wave_workflow_uses_only_approved_manifests() -> None:
    text = WORKFLOW.read_text()

    assert "cash-stage2-q1-wave-001.json" in text
    assert "cash-stage2-q2-wave-001.json" in text
    assert "acquire-historical-campaign.yml" in text
    assert "promote-historical" not in text
    assert "corpus_mutation: false" in text
    assert "promotion_dispatched: false" in text
