"""Tests for main blueprint: landing page, health endpoint, and redirects."""
from tests.conftest import register, login


def test_landing_page_unauthenticated(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"SecureVault" in resp.data


def test_landing_page_authenticated_redirects_to_vault(client, app):
    register(client)
    login(client)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/vault/" in resp.headers["Location"]


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    import json
    data = json.loads(resp.data)
    assert data["status"] == "ok"
    assert data["service"] == "SecureVault"
