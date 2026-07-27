# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in SecureVault, please report it
responsibly by emailing **shambhukapadi43@gmail.com** rather than opening a
public GitHub issue.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any proof-of-concept code if applicable

You can expect an acknowledgement within 48 hours and a status update within
7 days.

## Security Architecture

- **Zero-knowledge encryption**: AES-256-GCM per entry; master password never stored
- **Key derivation**: Scrypt (N=2¹⁴, r=8, p=1) with a per-user 16-byte random salt
- **Password hashing**: Argon2id via argon2-cffi
- **Brute-force protection**: Account locked after 5 consecutive failed logins
- **Rate limiting**: Flask-Limiter on registration (10/hr) and login (20/hr) endpoints
- **CSRF protection**: Flask-WTF on all state-changing requests
- **Security headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy
- **Session security**: HttpOnly, SameSite=Lax, 15-minute inactivity timeout
