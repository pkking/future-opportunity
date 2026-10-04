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


def test_v0_openapi_exposes_management_and_history_without_live_orders() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    paths = set(schema["paths"])
    required = {
        "/v1/strategies",
        "/v1/history",
        "/v1/positions",
        "/v1/positions/{position_id}",
        "/v1/positions/{position_id}/refresh",
        "/v1/positions/{position_id}/close",
        "/v1/opportunities/{opportunity_id}",
        "/v1/opportunities/{opportunity_id}/observations",
        "/v1/opportunities/{venue}/{strategy}/{base}",
        "/v1/simulations/{venue}/{strategy}/{base}",
    }
    assert required <= paths
    assert not any(
        token in path.lower()
        for path in paths
        for token in ("/orders", "/live-order", "/trade")
    )
