import pytest
from app import create_app
from app.models import db as _db
from app.config import TestConfig


@pytest.fixture
def app():
    """Fresh app + DB for every test function."""
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


DEFAULT_PASSWORD = "Str0ng!Pass#99"


def register(client, username="testuser", email="test@example.com", password=DEFAULT_PASSWORD):
    return client.post("/auth/register", data={
        "username": username,
        "email": email,
        "password": password,
        "confirm": password,
    }, follow_redirects=True)


def login(client, username="testuser", password=DEFAULT_PASSWORD):
    return client.post("/auth/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=True)
