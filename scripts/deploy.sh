#!/usr/bin/env bash
set -euo pipefail

echo "==> Pulling latest code…"
git pull origin main

echo "==> Building images…"
docker compose -f docker-compose.prod.yml build

echo "==> Running migrations…"
docker compose -f docker-compose.prod.yml run --rm backend \
    python manage.py migrate --noinput

echo "==> Collecting static…"
docker compose -f docker-compose.prod.yml run --rm backend \
    python manage.py collectstatic --noinput

echo "==> Restarting services…"
docker compose -f docker-compose.prod.yml up -d

echo "==> Waiting for health check…"
sleep 10

if curl -sf http://localhost/health/ > /dev/null; then
    echo "==> Deployment healthy."
else
    echo "==> WARNING: Health check failed. Check logs:"
    echo "    docker compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

echo "==> Cleaning old images…"
docker image prune -f

echo "==> Deployment complete."