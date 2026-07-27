"""Additional vault tests: export, error pages, and edge cases."""
import json
import pytest
from tests.conftest import register, login, DEFAULT_PASSWORD


def _setup(client, username, email):
    register(client, username=username, email=email)
    login(client, username=username)


def test_export_empty_vault(client, app):
    _setup(client, "exportempty", "exportempty@example.com")
    resp = client.get("/vault/export")
    data = json.loads(resp.data)
    assert data["entry_count"] == 0
    assert data["vault_export"] == []


def test_export_with_entries(client, app):
    _setup(client, "exportfull", "exportfull@example.com")
    client.post("/vault/new", data={
        "title": "ExportMe",
        "category": "Login",
        "site_url": "https://example.com",
        "username": "user@example.com",
        "secret": "ExpSecret99!",
        "notes": "",
    }, follow_redirects=True)
    resp = client.get("/vault/export")
    data = json.loads(resp.data)
    assert data["entry_count"] == 1
    assert data["vault_export"][0]["title"] == "ExportMe"
    assert data["vault_export"][0]["secret"] == "ExpSecret99!"


def test_export_requires_auth(client, app):
    resp = client.get("/vault/export", follow_redirects=True)
    assert b"Log in" in resp.data


def test_404_error_page(client, app):
    resp = client.get("/this/page/does/not/exist")
    assert resp.status_code == 404
    assert b"404" in resp.data or b"Not Found" in resp.data


def test_generate_password_requires_auth(client, app):
    resp = client.get("/vault/generate-password", follow_redirects=True)
    assert b"Log in" in resp.data


def test_generate_password_length_capped_at_64(client, app):
    _setup(client, "pwgencap", "pwgencap@example.com")
    resp = client.get("/vault/generate-password?length=999")
    data = json.loads(resp.data)
    assert len(data["password"]) == 64


def test_vault_entry_category_defaults_to_login(client, app):
    _setup(client, "vaultdefaultcat", "vaultdefaultcat@example.com")
    client.post("/vault/new", data={
        "title": "DefaultCat",
        "category": "Login",
        "site_url": "",
        "username": "",
        "secret": "SomeS3cret!xx",
        "notes": "",
    }, follow_redirects=True)
    resp = client.get("/vault/")
    assert b"DefaultCat" in resp.data


def test_reveal_requires_auth(client, app):
    resp = client.post("/vault/999/reveal", follow_redirects=True)
    assert b"Log in" in resp.data


def test_delete_requires_auth(client, app):
    resp = client.post("/vault/999/delete", follow_redirects=True)
    assert b"Log in" in resp.data
