from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload() -> dict[str, Any]:
    return {
        "account": "vibecodinglatam",
        "post_id": "post_test_1",
        "likes": 10,
        "comments": 2,
        "saves": 1,
        "reach": 1000,
        "followers": 1000,
    }


def test_feedback_supabase_unavailable(monkeypatch: Any) -> None:
    # Simula que no hay cliente (variables de entorno faltantes, etc.)
    def mock_get_client_fail() -> Any:
        raise RuntimeError("no supabase")

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client_fail)

    r = client.post("/scheduler/feedback", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"  # cuando no hay supabase
    assert data["stored"] is False
    assert 0.0 <= float(data["engagement_score"]) <= 1.0


def test_feedback_insert_failure(monkeypatch: Any) -> None:
    # Simula cliente supabase pero falla insert (tabla inexistente, error de red, etc.)
    class MockClient:
        class _Table:
            def __init__(self, name: str) -> None:
                self.name = name

            def insert(self, *_: Any, **__: Any) -> "MockClient._Table":
                return self

            def execute(self) -> Any:
                raise RuntimeError("insert failed")

        def table(self, name: str) -> "MockClient._Table":
            return MockClient._Table(name)

    def mock_get_client() -> Any:
        return MockClient()

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client)

    r = client.post("/scheduler/feedback", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"  # endpoint sigue ok
    assert data["stored"] is False  # pero no se persistió
    assert 0.0 <= float(data["engagement_score"]) <= 1.0


def test_feedback_insert_success(monkeypatch: Any) -> None:
    # Simula inserción exitosa
    class MockClient:
        class _Table:
            def __init__(self, name: str) -> None:
                self.name = name
                self._insert_called = False

            def insert(self, *_: Any, **__: Any) -> "MockClient._Table":
                self._insert_called = True
                return self

            def execute(self) -> Any:
                return type("R", (), {"data": [{"id": 1}]})

        def table(self, name: str) -> "MockClient._Table":
            return MockClient._Table(name)

    def mock_get_client() -> Any:
        return MockClient()

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client)

    r = client.post("/scheduler/feedback", json=_payload())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["stored"] is True
    assert 0.0 <= float(data["engagement_score"]) <= 1.0
