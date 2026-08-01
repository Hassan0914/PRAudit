"""Integration tests for Phase 6–10 REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_graphs_endpoint(temp_repo: Path) -> None:
    """Test POST /api/v1/graphs endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/graphs", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "call_graph" in data
    assert "import_graph" in data
    assert "dependency_graph" in data
    assert "inheritance_graph" in data


def test_api_metrics_endpoint(temp_repo: Path) -> None:
    """Test POST /api/v1/metrics endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/metrics", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "summary" in data
    assert data["summary"]["total_files"] > 0
    assert "file_metrics" in data


def test_api_static_analysis_endpoint(temp_repo: Path) -> None:
    """Test POST /api/v1/static-analysis endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/static-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "total_findings" in data
    assert "findings" in data


def test_api_security_endpoint(temp_repo: Path) -> None:
    """Test POST /api/v1/security endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/security", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "total_vulnerabilities" in data
    assert "vulnerabilities" in data


def test_api_index_search_endpoint(temp_repo: Path) -> None:
    """Test POST /api/v1/index/search endpoint."""
    payload = {"repo_path": str(temp_repo), "query": "main", "limit": 10}
    response = client.post("/api/v1/index/search", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["query"] == "main"
    assert data["total_matches"] > 0
