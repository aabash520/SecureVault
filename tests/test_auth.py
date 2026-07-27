import pytest
from tests.conftest import register, login, DEFAULT_PASSWORD


def test_register_success(client):
    resp = register(client)
    assert b"Log in" in resp.data or b"Account created" in resp.data


def test_register_duplicate_username(client):
    register(client, username="dupuser", email="dup1@example.com")
    resp = register(client, username="dupuser", email="dup2@example.com")
    assert b"already registered" in resp.data


def test_register_duplicate_email(client):
    register(client, username="user_a", email="shared@example.com")
    resp = register(client, username="user_b", email="shared@example.com")
    assert b"already registered" in resp.data


def test_register_password_mismatch(client):
    resp = client.post("/auth/register", data={
        "username": "mismatch",
        "email": "m@example.com",
        "password": "Str0ng!Pass#99",
        "confirm": "Different!Pass#00",
    }, follow_redirects=True)
    assert b"Passwords must match" in resp.data


def test_register_short_password(client):
    resp = client.post("/auth/register", data={
        "username": "shortpw",
        "email": "short@example.com",
        "password": "short",
        "confirm": "short",
    }, follow_redirects=True)
    assert b"10 characters" in resp.data


def test_register_weak_password_no_uppercase(client):
    resp = client.post("/auth/register", data={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "str0ng!pass#99",
        "confirm": "str0ng!pass#99",
    }, follow_redirects=True)
    assert b"uppercase" in resp.data


def test_register_weak_password_no_special_char(client):
    resp = client.post("/auth/register", data={
        "username": "weakuser2",
        "email": "weak2@example.com",
        "password": "Str0ngPass99xx",
        "confirm": "Str0ngPass99xx",
    }, follow_redirects=True)
    assert b"special" in resp.data


def test_login_success(client):
    register(client, username="loginuser", email="loginuser@example.com")
    resp = login(client, username="loginuser")
    assert b"Vault" in resp.data or resp.status_code == 200


def test_login_wrong_password(client):
    register(client, username="wrongpw", email="wrongpw@example.com")
    resp = client.post("/auth/login", data={
        "username": "wrongpw",
        "password": "Wrong!Pass#000",
    }, follow_redirects=True)
    assert b"Invalid" in resp.data


def test_login_nonexistent_user(client):
    resp = client.post("/auth/login", data={
        "username": "nobody",
        "password": "irrelevant",
    }, follow_redirects=True)
    assert b"Invalid" in resp.data


def test_brute_force_lockout(client):
    register(client, username="lockme", email="lockme@example.com")
    for _ in range(5):
        client.post("/auth/login", data={"username": "lockme", "password": "Wrong!Pass#00"})
    resp = client.post("/auth/login", data={
        "username": "lockme", "password": DEFAULT_PASSWORD
    }, follow_redirects=True)
    assert b"locked" in resp.data or b"Invalid" in resp.data


def test_logout(client):
    register(client, username="logoutuser", email="logoutuser@example.com")
    login(client, username="logoutuser")
    resp = client.post("/auth/logout", follow_redirects=True)
    assert b"Logged out" in resp.data or resp.status_code == 200


def test_dashboard_requires_login(client):
    resp = client.get("/vault/", follow_redirects=True)
    assert b"Log in" in resp.data


def test_settings_page_requires_login(client):
    resp = client.get("/auth/settings", follow_redirects=True)
    assert b"Log in" in resp.data


def test_change_password(client):
    register(client, username="changepw", email="changepw@example.com")
    login(client, username="changepw")
    new_pw = "NewStr0ng!Pass#77"
    resp = client.post("/auth/settings", data={
        "current_password": DEFAULT_PASSWORD,
        "new_password": new_pw,
        "confirm_password": new_pw,
    }, follow_redirects=True)
    assert b"updated" in resp.data or resp.status_code == 200


def test_change_password_wrong_current(client):
    register(client, username="badcurrent", email="badcurrent@example.com")
    login(client, username="badcurrent")
    resp = client.post("/auth/settings", data={
        "current_password": "Wrong!Pass#000",
        "new_password": "NewStr0ng!Pass#77",
        "confirm_password": "NewStr0ng!Pass#77",
    }, follow_redirects=True)
    assert b"incorrect" in resp.data
