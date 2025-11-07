from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_update_weights_unauthorized(monkeypatch: Any) -> None:
    # No ADMIN_TOKEN configurado o token inválido
    response = client.post(
        "/scheduler/weights/update",
        json={
            "account": "acc",
            "w_engagement": 0.6,
            "w_relevance": 0.4,
            "learning_rate": 0.05,
        },
        headers={"X-Admin-Token": "bad"},
    )
    assert response.status_code == 401


def test_update_weights_out_of_range(monkeypatch: Any) -> None:
    # Mock token ok, pero pesos inválidos

    monkeypatch.setenv("ADMIN_TOKEN", "secret")

    response = client.post(
        "/scheduler/weights/update",
        json={
            "account": "acc",
            "w_engagement": 1.0,
            "w_relevance": 0.2,  # suma 1.2 > 1.05
            "learning_rate": 0.05,
        },
        headers={"X-Admin-Token": "secret"},
    )
    assert response.status_code == 422


def test_update_weights_success_and_audit(monkeypatch: Any) -> None:
    # Mock token ok y cliente supabase con auditoría
    monkeypatch.setenv("ADMIN_TOKEN", "secret")

    calls: list[str] = []

    class MockClient:
        def table(self, name: str) -> Any:
            class Table:
                def __init__(self, name: str) -> None:
                    self._name = name

                def select(self, *_: Any) -> "Table":
                    return self

                def eq(self, *_: Any) -> "Table":
                    return self

                def limit(self, *_: Any) -> "Table":
                    return self

                def upsert(self, *_: Any) -> "Table":
                    calls.append(f"upsert:{self._name}")
                    return self

                def insert(self, *_: Any) -> "Table":
                    calls.append(f"insert:{self._name}")
                    return self

                def execute(self) -> Any:
                    # Para select de params, devolvemos defaults existentes
                    if self._name == "scheduler_model_params":
                        return type(
                            "R",
                            (),
                            {
                                "data": [
                                    {"w_engagement": 0.6, "w_relevance": 0.4, "learning_rate": 0.05}
                                ]
                            },
                        )
                    return type("R", (), {"data": []})

            return Table(name)

    def mock_get_client() -> Any:
        return MockClient()

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client)

    response = client.post(
        "/scheduler/weights/update",
        json={
            "account": "acc",
            "w_engagement": 0.65,
            "w_relevance": 0.35,
            "learning_rate": 0.05,
        },
        headers={"X-Admin-Token": "secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["new_weights"]["w_engagement"] == 0.65
    assert data["new_weights"]["w_relevance"] == 0.35
    # Verifica que hubo upsert y auditoría
    assert any(c.startswith("upsert:scheduler_model_params") for c in calls)
    assert any(c.startswith("insert:scheduler_model_audit") for c in calls)
