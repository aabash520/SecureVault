.PHONY: install run test lint clean

install:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt

run:
	.venv/bin/python run.py

test:
	.venv/bin/python -m pytest tests/ -v

lint:
	.venv/bin/python -m flake8 app/ --max-line-length=100

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f securevault.db
