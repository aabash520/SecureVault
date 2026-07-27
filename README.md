# SecureVault

[![CI](https://github.com/aabash520/SecureVault/actions/workflows/ci.yml/badge.svg)](https://github.com/aabash520/SecureVault/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A zero-knowledge password manager built with Flask and AES-256-GCM encryption.
The server never sees plaintext secrets — your master password never leaves your device
unencrypted.

> **Module:** The Internet and Web Technologies (ST5041CMD)
> **GitHub Repo:** https://github.com/aabash520/SecureVault

---

## Features

| Feature | Detail |
|---------|--------|
| AES-256-GCM encryption | Every secret encrypted at rest; nonce randomised per write |
| Argon2id password hashing | Industry-standard; resistant to GPU/ASIC attacks |
| Scrypt key derivation | Per-user 128-bit salt; derived key lives only in session |
| Entry categories | Login, Card, Identity, Note, Other |
| Favorites | Star important entries; filterable |
| Password generator | Cryptographically secure, server-side + client-side |
| Vault export | Download all decrypted entries as JSON |
| Account settings | Change master password; delete account |
| Search & filter | Live client-side search + server-side category/favorite filter |
| Brute-force protection | Account locked after 5 failed logins |
| Rate limiting | 10/hr register · 20/hr login (Flask-Limiter) |
| CSRF protection | Flask-WTF tokens on all state-changing requests |
| Security headers | HSTS · CSP · X-Frame-Options · Permissions-Policy · X-XSS-Protection |
| Session security | HttpOnly · SameSite=Lax · 15-min auto-logout on inactivity |
| Error pages | Custom 404 and 500 pages |
| 50+ git commits | Full incremental development history |
| 50+ tests | Crypto unit tests + auth/vault integration tests |

---

## Quick Start

```bash
git clone https://github.com/aabash520/SecureVault.git
cd SecureVault
make install           # creates .venv and installs deps
cp .env.example .env   # edit SECRET_KEY
make run               # starts on http://localhost:5000
```

Or manually:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

### Run tests

```bash
make test
# or
pytest tests/ -v
```

---

## Project Structure

```
SecureVault/
├── app/
│   ├── __init__.py          # App factory, security headers, error handlers
│   ├── config.py            # Dev / Production / Test config classes
│   ├── models.py            # User + VaultEntry SQLAlchemy models
│   ├── crypto.py            # AES-256-GCM encrypt/decrypt + scrypt KDF
│   ├── main.py              # Landing page blueprint
│   ├── auth/
│   │   ├── forms.py         # RegisterForm, LoginForm, ChangePasswordForm
│   │   └── routes.py        # register, login, logout, settings, delete-account
│   ├── vault/
│   │   └── routes.py        # CRUD, reveal, favorite, export, generate-password
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── errors/          # 404.html, 500.html
│   │   ├── auth/            # login, register, settings
│   │   └── vault/           # dashboard, entry_form
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── tests/
│   ├── conftest.py
│   ├── test_crypto.py       # 15 crypto unit tests
│   ├── test_auth.py         # 14 auth integration tests
│   ├── test_vault.py        # 14 vault CRUD + access-control tests
│   └── test_vault_extra.py  # 9 export, error page, edge-case tests
├── .github/
│   ├── workflows/ci.yml     # GitHub Actions CI
│   └── ISSUE_TEMPLATE/
├── Makefile
├── SECURITY.md
├── requirements.txt
├── requirements-dev.txt
├── run.py
└── .env.example
```

---

## Security Architecture

| Layer | Mechanism |
|-------|-----------|
| Secrets at rest | AES-256-GCM; random 96-bit nonce per encryption |
| Key derivation | Scrypt (N=2¹⁴, r=8, p=1) + per-user 128-bit salt |
| Key storage | Session-only; never written to database |
| Password hashing | Argon2id (argon2-cffi) |
| Transport | HTTPS + HSTS in production |
| Sessions | Flask-Login strong protection · 15-min inactivity timeout |
| CSRF | Flask-WTF tokens · 1-hour token lifetime |
| Rate limiting | Flask-Limiter fixed-window on auth endpoints |
| Account lockout | 5 consecutive failures → lock |
| Headers | HSTS · CSP · X-Frame-Options DENY · Permissions-Policy · X-XSS-Protection |
| Request size | 1 MB cap (MAX_CONTENT_LENGTH) |
| Input validation | WTForms validators + strong_password policy enforcement |

---

## Database Schema

```
users
  id · username · email · password_hash · key_salt
  created_at · last_login · failed_logins · is_active

vault_entries
  id · user_id (FK→users CASCADE) · title · category
  site_url · username · secret_ciphertext · notes_ciphertext
  is_favorite · created_at · updated_at
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/auth/register` | Create account |
| GET/POST | `/auth/login` | Authenticate |
| POST | `/auth/logout` | End session |
| GET/POST | `/auth/settings` | Change password |
| POST | `/auth/delete-account` | Delete account + all data |
| GET | `/vault/` | Dashboard (search, filter) |
| GET/POST | `/vault/new` | Create entry |
| GET/POST | `/vault/<id>/edit` | Edit entry |
| POST | `/vault/<id>/reveal` | Decrypt and return secret |
| POST | `/vault/<id>/delete` | Delete entry |
| POST | `/vault/<id>/favorite` | Toggle favorite |
| GET | `/vault/export` | Export all entries as JSON |
| GET | `/vault/generate-password` | Generate strong password |

---

## Technologies

- **Backend:** Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Limiter
- **Database:** SQLite (dev) / any SQLAlchemy-compatible DB (prod)
- **Crypto:** `cryptography` (AES-GCM), `argon2-cffi`, scrypt KDF
- **Frontend:** Jinja2, HTML5, CSS custom properties, Vanilla JS (Web Crypto API)
- **Testing:** pytest · 50+ tests across crypto, auth, and vault modules
- **CI/CD:** GitHub Actions (Python 3.11 & 3.12 matrix)
