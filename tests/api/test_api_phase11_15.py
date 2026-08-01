"""Integration tests for Phase 11–15 REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_git_status(temp_repo: Path) -> None:
    """Test POST /api/v1/git/status endpoint."""
    payload = {"repo_path": str(temp_repo)}
    response = client.post("/api/v1/git/status", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "current_branch" in data


def test_api_git_history(temp_repo: Path) -> None:
    """Test POST /api/v1/git/history endpoint."""
    payload = {"repo_path": str(temp_repo), "max_count": 5}
    response = client.post("/api/v1/git/history", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["count"] >= 1


def test_api_pr_analyze(temp_repo: Path) -> None:
    """Test POST /api/v1/pr/analyze endpoint."""
    payload = {"repo_path": str(temp_repo), "base_ref": "HEAD~1", "head_ref": "HEAD", "pr_id": "PR-API-1"}
    response = client.post("/api/v1/pr/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["pr_id"] == "PR-API-1"


def test_api_pr_impact(temp_repo: Path) -> None:
    """Test POST /api/v1/pr/impact endpoint."""
    payload = {"repo_path": str(temp_repo), "base_ref": "HEAD~1", "head_ref": "HEAD", "max_depth": 2}
    response = client.post("/api/v1/pr/impact", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "impacted_files" in data


def test_api_review_and_get_review(temp_repo: Path) -> None:
    """Test POST /api/v1/review and GET /api/v1/review/{review_id} endpoints."""
    payload = {"repo_path": str(temp_repo), "base_ref": "HEAD~1", "head_ref": "HEAD", "pr_id": "PR-REV-99"}
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "review_id" in data
    rev_id = data["review_id"]

    # GET review by ID
    get_res = client.get(f"/api/v1/review/{rev_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["review_id"] == rev_id


def test_api_github_webhook() -> None:
    """Test POST /api/v1/github/webhook endpoint."""
    payload = {"action": "opened", "number": 10, "repository": {"name": "PRAudit"}}
    headers = {"X-GitHub-Event": "pull_request"}

    response = client.post("/api/v1/github/webhook", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "received"
    assert data["pr_number"] == 10
