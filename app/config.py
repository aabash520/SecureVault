import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

_ENV = os.getenv("FLASK_ENV", "development")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///securevault.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _ENV == "production"
    SESSION_COOKIE_NAME = "sv_session"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "15"))
    )

    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_SSL_STRICT = _ENV == "production"

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB request cap

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY = "fixed-window"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    RATELIMIT_ENABLED = False
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}
