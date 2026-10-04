from fastapi.testclient import TestClient

from future_opportunity.api import app


def test_web_workbench_and_strategy_catalog_are_served() -> None:
    with TestClient(app) as client:
        index = client.get("/")
        strategies = client.get("/v1/strategies")

    assert index.status_code == 200
    assert "future-opportunity" in index.text
    assert "Discover Opportunities" in index.text

    assert strategies.status_code == 200
    names = [item["name"] for item in strategies.json()["results"]]
    assert names == ["funding-carry", "cash-and-carry"]
