"""
LiveLLM - Tests for FastAPI Endpoints
"""

import pytest
from starlette.testclient import TestClient
from livellm.api.main import app
from livellm.storage.seed_data import generate_seed_data


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    generate_seed_data()


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_models():
    client = TestClient(app)
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 5


def test_get_diurnal_metrics():
    client = TestClient(app)
    response = client.get("/api/metrics/diurnal")
    assert response.status_code == 200
    data = response.json()
    assert "peak_hours_utc" in data
    assert "data" in data
    assert len(data["data"]) > 0


def test_get_drift_metrics():
    client = TestClient(app)
    response = client.get("/api/metrics/drift?model_id=gpt-4o")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "gpt-4o"
    assert len(data["series"]) == 30
    assert len(data["alerts"]) >= 1


def test_live_probe_endpoint():
    client = TestClient(app)
    payload = {
        "model_id": "claude-3-5-sonnet",
        "tier": 1,
        "use_nonce": True
    }
    response = client.post("/api/probe/live", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "telemetry" in data
    assert "evaluation" in data
    assert data["telemetry"]["ttft_ms"] > 0
    assert data["telemetry"]["tps"] > 0
