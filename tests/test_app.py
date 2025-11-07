from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("project") == "WAV Automata"


def test_generator_post_minimal():
    payload = {"topic": "Lanzamiento de producto"}
    r = client.post("/generator/post", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "copy" in data and isinstance(data["copy"], str)
    assert "hashtags" in data and isinstance(data["hashtags"], list)
    assert "visual_prompt" in data and isinstance(data["visual_prompt"], str)


def test_semantic_score_basic():
    payload = {"text": "IA generativa en marketing", "context": "marketing IA contenidos"}
    r = client.post("/semantic/score", json=payload)
    assert r.status_code == 200
    data = r.json()
    for k in ("relevance", "momentum", "roi_prediction"):
        assert k in data
        assert 0.0 <= float(data[k]) <= 1.0
