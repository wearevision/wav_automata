from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scheduler_run_daily_single() -> None:
    payload = {"accounts": ["vibecodinglatam"], "length": 100}
    r = client.post("/scheduler/run_daily", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data and isinstance(data["results"], list)
    assert len(data["results"]) >= 1
    first = data["results"][0]
    assert "scheduled" in first and "content" in first
    assert "text" in first["content"]
