"""Integration tests for Phase 21–30 SaaS REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_memory_endpoint() -> None:
    res = client.get("/api/v1/memory?repository_name=PRAudit")
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_api_rules_endpoints() -> None:
    payload = {
        "rule_id": "API-RULE-1",
        "name": "API Rule",
        "description": "Rule registered via API",
        "category": "SECURITY",
        "severity": "CRITICAL",
    }
    post_res = client.post("/api/v1/rules", json=payload)
    assert post_res.status_code == 200

    get_res = client.get("/api/v1/rules")
    assert get_res.status_code == 200
    assert get_res.json()["count"] >= 1


def test_api_learning_endpoints() -> None:
    payload = {
        "event_id": "ev_1",
        "rule_id": "API-RULE-1",
        "agent_name": "SecurityReviewer",
        "feedback_action": "ACCEPTED",
    }
    post_res = client.post("/api/v1/learning", json=payload)
    assert post_res.status_code == 200

    get_res = client.get("/api/v1/learning")
    assert get_res.status_code == 200
    assert get_res.json()["metrics"]["total_feedback_events"] >= 1


def test_api_dashboard_endpoint() -> None:
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 200
    assert res.json()["dashboard"]["total_repositories"] >= 1


def test_api_auth_and_org_endpoints() -> None:
    auth_res = client.post("/api/v1/auth", json={"username": "admin", "password": "admin"})
    assert auth_res.status_code == 200

    org_res = client.post("/api/v1/organizations", json={"name": "Globex", "domain": "globex.com"})
    assert org_res.status_code == 200


def test_api_providers_and_optimization() -> None:
    prov_res = client.get("/api/v1/providers?provider_type=github")
    assert prov_res.status_code == 200

    opt_res = client.get("/api/v1/optimization")
    assert opt_res.status_code == 200


def test_api_platform_health_and_status() -> None:
    h_res = client.get("/api/v1/platform/health")
    assert h_res.status_code == 200

    s_res = client.get("/api/v1/platform/status")
    assert s_res.status_code == 200
