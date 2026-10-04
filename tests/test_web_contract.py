from pathlib import Path

from fastapi.testclient import TestClient

from future_opportunity.api import app


WEB = Path("src/future_opportunity/web/index.html")


def test_workbench_html_is_single_well_formed_document() -> None:
    text = WEB.read_text()

    assert text.count("<!doctype html>") == 1
    assert text.count("</html>") == 1
    assert text.count("async function loadHistory()") == 1
    assert text.count("async function loadPositions()") == 1


def test_workbench_exposes_agent_guarded_business_workflow() -> None:
    text = WEB.read_text()

    for view in ("discover-view", "analyze-view", "positions-view", "history-view"):
        assert f'id="{view}"' in text

    assert 'id="liquidity-policy"' in text
    assert '<option value="strict">' in text
    assert '<option value="partial">' in text
    assert 'id="max-impact"' in text
    assert "liquidity_policy" in text
    assert "max_impact_bps" in text
    assert "item.qualification.qualified" in text
    assert "/refresh" in text
    assert "/close" in text


def test_root_serves_workbench() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "future-opportunity" in response.text
    assert "Partial deployment is never automatic" in response.text
