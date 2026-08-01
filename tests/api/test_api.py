"""Integration tests for FastAPI REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert json_data["service"] == "PRAudit"


def test_api_analyze_repository(temp_repo: Path) -> None:
    """Test POST /api/v1/analyze endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["status"] == "success"
    assert "summary" in json_data
    assert json_data["summary"]["repository_name"] == "sample_repo"
    assert "parsing_stats" in json_data
    assert "chunk_stats" in json_data
    assert "symbol_stats" in json_data


def test_api_list_files(temp_repo: Path) -> None:
    """Test POST /api/v1/files endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/files", json=payload)
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["status"] == "success"
    assert json_data["total_files"] > 0
    assert len(json_data["files"]) > 0


def test_api_query_symbols(temp_repo: Path) -> None:
    """Test POST /api/v1/symbols endpoint."""
    payload = {"repo_path": str(temp_repo), "name": "add"}
    response = client.post("/api/v1/symbols", json=payload)
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["status"] == "success"
    assert json_data["count"] >= 1
    assert json_data["symbols"][0]["name"] == "add"
