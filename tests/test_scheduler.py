from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scheduler_next_post_smoke() -> None:
    r = client.get("/scheduler/next_post")
    assert r.status_code == 200
    data = r.json()
    for key in ("account", "recommended_time", "content_type", "topic", "priority"):
        assert key in data
    assert isinstance(data["account"], str)
    assert isinstance(data["recommended_time"], str)
    assert isinstance(data["content_type"], str)
    assert isinstance(data["topic"], str)
    assert 0.0 <= float(data["priority"]) <= 1.0
