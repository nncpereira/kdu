#!/usr/bin/env bash
set -euo pipefail

# Builds and starts the local Docker test environment, then runs
# migrations and collects static files. Run from the project root.
#
# First time only: cp .env.test.example .env.test  (and set a real
# DJANGO_SECRET_KEY in it).

if [ ! -f .env.test ]; then
    echo "Missing .env.test. Run: cp .env.test.example .env.test"
    exit 1
fi

COMPOSE="docker compose -f docker-compose.test.yml"

echo "==> Building images…"
$COMPOSE build

echo "==> Starting db…"
$COMPOSE up -d db

echo "==> Waiting for db to be healthy…"
until [ "$($COMPOSE ps -q db | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
    sleep 1
done

echo "==> Starting backend and frontend…"
$COMPOSE up -d backend frontend

echo "==> Waiting for backend health check…"
sleep 5

echo "==> Running migrations…"
$COMPOSE exec -T backend python manage.py migrate --noinput

echo "==> Test environment is up:"
echo "    Frontend: http://localhost:8080"
echo "    Backend:  http://localhost:8001"
echo "    Postgres: localhost:5433"
echo
echo "    To load your real dev data for cross-checking: scripts/load-test-data.sh"
echo "    To create a superadmin: $COMPOSE exec backend python manage.py createsuperuser"
