from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Build the API against an isolated SQLite file for every test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("CALCULATOR_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    # Import the application after the environment variable is set. Removing
    # cached application modules keeps this fixture isolated if tests are
    # reordered or expanded later.
    for module_name in (
        "app.main",
        "app.api.routes",
        "app.models.history",
        "app.db.database",
    ):
        sys.modules.pop(module_name, None)

    from app.main import app

    with TestClient(app) as client:
        yield client


def test_health_and_calculation_round_trip(api_client: TestClient) -> None:
    assert api_client.get("/api/health").json() == {"success": True, "status": "ok"}

    response = api_client.post("/api/calculate", json={"expression": "(2+3)*4"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"] == 20
    assert payload["expression"] == "(2+3)*4"
    assert payload["record"]["id"] > 0

    history = api_client.get("/api/history")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["expression"] == "(2+3)*4"


def test_history_persists_and_supports_search(api_client: TestClient) -> None:
    for expression in ("1+2", "7*8", "(10-4)/2"):
        assert api_client.post("/api/calculate", json={"expression": expression}).status_code == 201

    searched = api_client.get("/api/history", params={"keyword": "7"})
    assert searched.status_code == 200
    assert searched.json()["total"] == 1
    assert searched.json()["items"][0]["result"] == 56

    # A new client instance still reads from the same database file.
    with TestClient(api_client.app) as reopened_client:
        persisted = reopened_client.get("/api/history")
    assert persisted.json()["total"] == 3


def test_calculation_errors_are_returned_as_client_errors(api_client: TestClient) -> None:
    division_by_zero = api_client.post("/api/calculate", json={"expression": "1 / 0"})
    assert division_by_zero.status_code == 400
    assert "Division by zero" in division_by_zero.json()["detail"]["message"]

    malformed = api_client.post("/api/calculate", json={"expression": "(1+2"})
    assert malformed.status_code == 400
    assert "Missing closing parenthesis" in malformed.json()["detail"]["message"]

    blank = api_client.post("/api/calculate", json={"expression": "   "})
    assert blank.status_code == 422


def test_delete_one_record_and_clear_all(api_client: TestClient) -> None:
    ids = []
    for expression in ("2+2", "3+3"):
        response = api_client.post("/api/calculate", json={"expression": expression})
        ids.append(response.json()["record"]["id"])

    deleted = api_client.delete(f"/api/history/{ids[0]}")
    assert deleted.status_code == 200
    assert api_client.get("/api/history").json()["total"] == 1

    missing = api_client.delete(f"/api/history/{ids[0]}")
    assert missing.status_code == 404

    cleared = api_client.delete("/api/history")
    assert cleared.status_code == 200
    assert cleared.json()["deleted_count"] == 1
    assert api_client.get("/api/history").json()["total"] == 0


def test_stats_are_calculated_from_persisted_records(api_client: TestClient) -> None:
    for expression in ("2", "4", "6"):
        assert api_client.post("/api/calculate", json={"expression": expression}).status_code == 201

    stats = api_client.get("/api/stats")
    assert stats.status_code == 200
    assert stats.json()["total"] == 3
    assert stats.json()["average"] == pytest.approx(4)
    assert stats.json()["minimum"] == 2
    assert stats.json()["maximum"] == 6


def test_steps_favorite_export_and_previous_answer(api_client: TestClient) -> None:
    first = api_client.post("/api/calculate", json={"expression": "(2+3)*4"})
    assert first.status_code == 201
    assert "2 + 3 = 5" in first.json()["steps"]
    record_id = first.json()["record"]["id"]

    favorite = api_client.post(f"/api/history/{record_id}/favorite")
    assert favorite.status_code == 200
    assert favorite.json()["record"]["is_favorite"] is True

    answer = api_client.post("/api/calculate", json={"expression": "Ans+5"})
    assert answer.status_code == 201
    assert answer.json()["result"] == 25

    exported = api_client.get("/api/history/export")
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert "(2+3)*4" in exported.text
    assert "Ans+5" in exported.text
