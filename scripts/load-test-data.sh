#!/usr/bin/env bash
set -euo pipefail

# Copies your native local dev Postgres database into the Docker test
# environment's database, so the test env has real data to cross-check
# against source records. Run from the project root.
#
# Prereqs:
#   - Native dev Postgres running (the one `manage.py runserver` uses)
#   - docker-compose.test.yml's db service up:
#       docker compose -f docker-compose.test.yml up -d db

if [ ! -f .env ]; then
    echo "Missing .env (native dev DB config). Aborting."
    exit 1
fi
if [ ! -f .env.test ]; then
    echo "Missing .env.test (test DB config). Copy .env.test.example first."
    exit 1
fi

# Read values directly rather than `source <(grep ...)`: macOS ships
# bash 3.2 (GPLv3 licensing), where sourcing a process substitution
# under `set -u` unreliably leaves the variables unset.
read_env_var() {
    grep -E "^${1}=" "$2" | tail -1 | cut -d= -f2-
}

DEV_DB=$(read_env_var POSTGRES_DB .env)
DEV_USER=$(read_env_var POSTGRES_USER .env)
DEV_PASSWORD=$(read_env_var POSTGRES_PASSWORD .env)
DEV_HOST=$(read_env_var POSTGRES_HOST .env)
DEV_HOST="${DEV_HOST:-127.0.0.1}"
DEV_PORT=$(read_env_var POSTGRES_PORT .env)
DEV_PORT="${DEV_PORT:-5432}"

TEST_DB=$(read_env_var POSTGRES_DB .env.test)
TEST_USER=$(read_env_var POSTGRES_USER .env.test)
TEST_PASSWORD=$(read_env_var POSTGRES_PASSWORD .env.test)
TEST_HOST=127.0.0.1   # host-side: docker-compose.test.yml maps db to 5433
TEST_PORT=5433

echo "==> This will REPLACE all data in the test database ($TEST_DB @ $TEST_HOST:$TEST_PORT)"
echo "    with a copy of your dev database ($DEV_DB @ $DEV_HOST:$DEV_PORT)."
read -p "Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo "==> Dumping dev database…"
PGPASSWORD="$DEV_PASSWORD" pg_dump -h "$DEV_HOST" -p "$DEV_PORT" -U "$DEV_USER" -d "$DEV_DB" -Fc \
    > /tmp/kdu_dev_snapshot.dump

echo "==> Restoring into test database…"
PGPASSWORD="$TEST_PASSWORD" pg_restore -h "$TEST_HOST" -p "$TEST_PORT" -U "$TEST_USER" -d "$TEST_DB" \
    --clean --if-exists --no-owner \
    < /tmp/kdu_dev_snapshot.dump

rm -f /tmp/kdu_dev_snapshot.dump

echo "==> Done. Test database now mirrors dev."
echo "    If the backend container was already running, restart it:"
echo "    docker compose -f docker-compose.test.yml restart backend"
