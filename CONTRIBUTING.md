# Contributing to SecureVault

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/aabash520/SecureVault.git
cd SecureVault
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Follow PEP 8; max line length 100
- Run `flake8 app/` before submitting a PR
- No secrets, credentials, or `.env` files in commits

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Open a PR with a clear description

## Security

Please report security vulnerabilities privately — see [SECURITY.md](SECURITY.md).
