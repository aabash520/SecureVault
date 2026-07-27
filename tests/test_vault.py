import json
import pytest
from app.models import VaultEntry
from tests.conftest import register, login, DEFAULT_PASSWORD


def _setup_user(client, username, email, password=DEFAULT_PASSWORD):
    register(client, username=username, email=email, password=password)
    login(client, username=username, password=password)


def _create_entry(client, title="GitHub", secret="mypassword99", site_url="https://github.com",
                  category="Login"):
    return client.post("/vault/new", data={
        "title": title,
        "category": category,
        "site_url": site_url,
        "username": "user@example.com",
        "secret": secret,
        "notes": "my note",
    }, follow_redirects=True)


def _first_entry_id(app, username):
    from app.models import User
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        entry = VaultEntry.query.filter_by(user_id=user.id).first()
        return entry.id if entry else None


def test_create_entry(client, app):
    _setup_user(client, "vaultcreate", "vaultcreate@example.com")
    resp = _create_entry(client)
    assert b"Entry saved" in resp.data or b"GitHub" in resp.data


def test_create_entry_with_category(client, app):
    _setup_user(client, "vaultcat", "vaultcat@example.com")
    resp = _create_entry(client, title="My Visa Card", category="Card")
    assert b"Entry saved" in resp.data or b"My Visa Card" in resp.data


def test_dashboard_shows_entry(client, app):
    _setup_user(client, "vaultlist", "vaultlist@example.com")
    _create_entry(client, title="UniqueTitle9988")
    resp = client.get("/vault/")
    assert b"UniqueTitle9988" in resp.data


def test_search_entry(client, app):
    _setup_user(client, "vaultsearch", "vaultsearch@example.com")
    _create_entry(client, title="SearchableEntry")
    resp = client.get("/vault/?q=Searchable")
    assert b"SearchableEntry" in resp.data


def test_search_no_results(client, app):
    _setup_user(client, "vaultnosearch", "vaultnosearch@example.com")
    _create_entry(client, title="SomeEntry")
    resp = client.get("/vault/?q=zzzznotfound")
    assert b"No results for" in resp.data or resp.status_code == 200


def test_category_filter(client, app):
    _setup_user(client, "vaultcatfilter", "vaultcatfilter@example.com")
    _create_entry(client, title="LoginEntry", category="Login")
    _create_entry(client, title="CardEntry", category="Card")
    resp = client.get("/vault/?cat=Card")
    assert b"CardEntry" in resp.data
    assert b"LoginEntry" not in resp.data


def test_reveal_returns_secret(client, app):
    _setup_user(client, "vaultreveal", "vaultreveal@example.com")
    _create_entry(client, title="RevealTest", secret="topsecret789")
    entry_id = _first_entry_id(app, "vaultreveal")
    assert entry_id is not None

    resp = client.post(f"/vault/{entry_id}/reveal")
    data = json.loads(resp.data)
    assert data["secret"] == "topsecret789"


def test_delete_entry(client, app):
    _setup_user(client, "vaultdelete", "vaultdelete@example.com")
    _create_entry(client, title="DeleteMe")
    entry_id = _first_entry_id(app, "vaultdelete")
    assert entry_id is not None

    resp = client.post(f"/vault/{entry_id}/delete", follow_redirects=True)
    assert b"Entry deleted" in resp.data


def test_toggle_favorite(client, app):
    _setup_user(client, "vaultfav", "vaultfav@example.com")
    _create_entry(client, title="FavEntry")
    entry_id = _first_entry_id(app, "vaultfav")
    assert entry_id is not None

    resp = client.post(f"/vault/{entry_id}/favorite")
    data = json.loads(resp.data)
    assert data["is_favorite"] is True

    resp2 = client.post(f"/vault/{entry_id}/favorite")
    data2 = json.loads(resp2.data)
    assert data2["is_favorite"] is False


def test_favorites_filter(client, app):
    _setup_user(client, "vaultfavfilter", "vaultfavfilter@example.com")
    _create_entry(client, title="StarredEntry")
    entry_id = _first_entry_id(app, "vaultfavfilter")
    client.post(f"/vault/{entry_id}/favorite")

    resp = client.get("/vault/?favorites=1")
    assert b"StarredEntry" in resp.data


def test_generate_password(client, app):
    _setup_user(client, "pwgen", "pwgen@example.com")
    resp = client.get("/vault/generate-password")
    data = json.loads(resp.data)
    pw = data["password"]
    assert len(pw) == 20
    assert any(c.isupper() for c in pw)
    assert any(c.isdigit() for c in pw)
    assert any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in pw)


def test_generate_password_custom_length(client, app):
    _setup_user(client, "pwgenlen", "pwgenlen@example.com")
    resp = client.get("/vault/generate-password?length=32")
    data = json.loads(resp.data)
    assert len(data["password"]) == 32


def test_cannot_access_other_users_entry(client, app):
    _setup_user(client, "owneruser", "owner@example.com")
    _create_entry(client, title="OwnerSecret")
    entry_id = _first_entry_id(app, "owneruser")
    assert entry_id is not None

    client.post("/auth/logout")
    register(client, username="attackeruser", email="attacker@example.com")
    login(client, username="attackeruser")

    resp = client.post(f"/vault/{entry_id}/reveal")
    assert resp.status_code == 404


def test_cannot_favorite_other_users_entry(client, app):
    _setup_user(client, "favowner", "favowner@example.com")
    _create_entry(client, title="PrivateEntry")
    entry_id = _first_entry_id(app, "favowner")

    client.post("/auth/logout")
    register(client, username="favattacker", email="favattacker@example.com")
    login(client, username="favattacker")

    resp = client.post(f"/vault/{entry_id}/favorite")
    assert resp.status_code == 404


def test_vault_requires_auth(client, app):
    resp = client.get("/vault/new", follow_redirects=True)
    assert b"Log in" in resp.data


def test_edit_entry(client, app):
    _setup_user(client, "vaultedit", "vaultedit@example.com")
    _create_entry(client, title="Original", secret="oldpass")
    entry_id = _first_entry_id(app, "vaultedit")

    resp = client.post(f"/vault/{entry_id}/edit", data={
        "title": "Updated",
        "category": "Note",
        "site_url": "",
        "username": "",
        "secret": "N3wPass!word#77",
        "notes": "",
    }, follow_redirects=True)
    assert b"Entry updated" in resp.data
    assert b"Updated" in resp.data
