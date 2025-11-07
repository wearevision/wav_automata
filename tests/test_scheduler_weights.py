from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_weights_defaults(monkeypatch: Any) -> None:
    def mock_get_client() -> Any:
        class MockClient:
            def table(self, name: str) -> Any:
                class Table:
                    def select(self, *_: Any) -> "Table":
                        return self

                    def eq(self, *_: Any) -> "Table":
                        return self

                    def limit(self, *_: Any) -> "Table":
                        return self

                    def execute(self) -> Any:
                        return type("R", (), {"data": []})

                return Table()

        return MockClient()

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client)

    response = client.get("/scheduler/weights", params={"account": "test_account"})
    assert response.status_code == 200
    data = response.json()
    assert data["account"] == "test_account"
    assert data["w_engagement"] == 0.6
    assert data["w_relevance"] == 0.4
    assert "defaults" in data.get("message", "")


def test_get_weights_existing(monkeypatch: Any) -> None:
    def mock_get_client() -> Any:
        class MockClient:
            def table(self, name: str) -> Any:
                class Table:
                    def select(self, *_: Any) -> "Table":
                        return self

                    def eq(self, *_: Any) -> "Table":
                        return self

                    def limit(self, *_: Any) -> "Table":
                        return self

                    def execute(self) -> Any:
                        return type(
                            "R",
                            (),
                            {
                                "data": [
                                    {
                                        "account": "acc",
                                        "w_engagement": 0.71,
                                        "w_relevance": 0.29,
                                        "learning_rate": 0.05,
                                        "updated_at": "2025-11-07T12:34:22Z",
                                    }
                                ]
                            },
                        )

                return Table()

        return MockClient()

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client)

    response = client.get("/scheduler/weights", params={"account": "acc"})
    assert response.status_code == 200
    data = response.json()
    assert data["w_engagement"] == 0.71
    assert data["w_relevance"] == 0.29
    assert data["learning_rate"] == 0.05
    assert data["updated_at"] == "2025-11-07T12:34:22Z"


def test_get_weights_error(monkeypatch: Any) -> None:
    def mock_get_client_error() -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr("app.routers.scheduler_ai.get_client", mock_get_client_error)

    response = client.get("/scheduler/weights", params={"account": "x"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("error") == "supabase_unavailable"
