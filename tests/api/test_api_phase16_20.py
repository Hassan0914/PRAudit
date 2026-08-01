"""Integration tests for Phase 16–20 AI & Enterprise REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_ai_review(temp_repo: Path) -> None:
    """Test POST /api/v1/ai/review endpoint."""
    payload = {
        "repo_path": str(temp_repo),
        "base_ref": "HEAD~1",
        "head_ref": "HEAD",
        "pr_id": "PR-AI-API",
        "model_id": "claude-3-5-sonnet",
    }
    response = client.post("/api/v1/ai/review", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "review_id" in data
    assert data["model"] == "claude-3-5-sonnet"


def test_api_ai_context(temp_repo: Path) -> None:
    """Test POST /api/v1/ai/context endpoint."""
    payload = {"repo_path": str(temp_repo), "base_ref": "HEAD~1", "head_ref": "HEAD", "token_budget": 16000}
    response = client.post("/api/v1/ai/context", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "total_estimated_tokens" in data


def test_api_ai_workflow(temp_repo: Path) -> None:
    """Test POST /api/v1/ai/workflow endpoint."""
    payload = {"repo_path": str(temp_repo), "base_ref": "HEAD~1", "head_ref": "HEAD", "pr_id": "PR-WF-API"}
    response = client.post("/api/v1/ai/workflow", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["workflow_status"] == "completed"


def test_api_ai_evaluate() -> None:
    """Test POST /api/v1/ai/evaluate endpoint."""
    payload = {"review_id": "rev_test", "ai_finding_titles": ["High Cyclomatic Complexity in 'calculate'"]}
    response = client.post("/api/v1/ai/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["precision"] == 1.0


def test_api_telemetry_and_costs() -> None:
    """Test GET /api/v1/ai/telemetry and GET /api/v1/ai/costs endpoints."""
    t_res = client.get("/api/v1/ai/telemetry")
    assert t_res.status_code == 200

    c_res = client.get("/api/v1/ai/costs")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "total_cost_usd" in c_data
