#!/usr/bin/env bash
set -euo pipefail

echo "==> Lint"
ruff check .

echo "==> Type check"
mypy --ignore-missing-imports .

echo "==> Migrations check"
python manage.py makemigrations --check --dry-run

echo "==> Clear stale coverage data"
coverage erase

echo "==> Smoke tests"
pytest -m smoke --cov-fail-under=0

echo "==> Full test suite with coverage"
pytest -n auto --cov --cov-report=xml

echo "==> Done"