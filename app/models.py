from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc)
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

db = SQLAlchemy()
_hasher = PasswordHasher()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    key_salt = db.Column(db.LargeBinary(16), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_logins = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    entries = db.relationship(
        "VaultEntry", backref="owner", cascade="all, delete-orphan", lazy="dynamic"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = _hasher.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            _hasher.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    def get_id(self):
        return str(self.id)


ENTRY_CATEGORIES = ["Login", "Card", "Identity", "Note", "Other"]


class VaultEntry(db.Model):
    __tablename__ = "vault_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(32), default="Login", nullable=False)
    site_url = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    secret_ciphertext = db.Column(db.LargeBinary, nullable=False)
    notes_ciphertext = db.Column(db.LargeBinary, nullable=True)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
