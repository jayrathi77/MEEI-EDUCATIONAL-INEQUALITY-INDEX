"""Integration tests for FastAPI REST API endpoints."""
import pytest
from pathlib import Path
import sys

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["synthetic_mode"] is True
    assert isinstance(data["data_ready"], dict)
    assert all(data["data_ready"].values())


def test_overview_endpoint(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    data = r.json()
    assert data["n_districts"] == 200
    assert data["synthetic_mode"] is True


def test_districts_list_and_lookup(client):
    r = client.get("/api/districts?page_size=10")
    assert r.status_code == 200
    data = r.json()
    assert "districts" in data
    assert len(data["districts"]) > 0
    first_id = data["districts"][0]["district_id"]

    # Specific district lookup
    r_detail = client.get(f"/api/districts/{first_id}")
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert detail["district_id"] == first_id
    assert "meei" in detail


def test_index_summary_and_diagnostics(client):
    r_sum = client.get("/api/index/summary")
    assert r_sum.status_code == 200
    assert "distribution" in r_sum.json()

    r_diag = client.get("/api/index/diagnostics")
    assert r_diag.status_code == 200


def test_iop_endpoints(client):
    r_sum = client.get("/api/iop/summary")
    assert r_sum.status_code == 200
    assert r_sum.json().get("status") == "OK"

    r_circ = client.get("/api/iop/circumstances")
    assert r_circ.status_code == 200
    assert "circumstances" in r_circ.json()


def test_models_endpoints(client):
    r_comp = client.get("/api/models/comparison")
    assert r_comp.status_code == 200
    data = r_comp.json()
    assert "models" in data
    assert "best_model" in data

    r_val = client.get("/api/models/validation")
    assert r_val.status_code == 200


def test_explainability_endpoints(client):
    r_glob = client.get("/api/explainability/global")
    assert r_glob.status_code == 200
    data = r_glob.json()
    assert "global_importance" in data
    assert len(data["global_importance"]) > 0

    r_loc = client.get("/api/explainability/district/D001")
    assert r_loc.status_code == 200
    assert "shap_contributions" in r_loc.json()


def test_priorities_endpoint(client):
    r = client.get("/api/priorities?page_size=10")
    assert r.status_code == 200
    data = r.json()
    assert "districts" in data
    assert len(data["districts"]) <= 10


def test_methodology_and_data_sources(client):
    r_m = client.get("/api/methodology")
    assert r_m.status_code == 200

    r_d = client.get("/api/data-sources")
    assert r_d.status_code == 200
    assert r_d.json()["current_data"] == "SYNTHETIC_DEMO"
