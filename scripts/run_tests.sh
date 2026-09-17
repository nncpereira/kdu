#!/usr/bin/env bash
set -euo pipefail

# Ensure Postgres is available
: "${POSTGRES_HOST:=127.0.0.1}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_TEST_DB:=kdu_test}"

echo "Running full KDU test suite…"
pytest -n auto -m "not slow" "$@"