#!/bin/sh
set -eu

EXPECTED=/volume1/docker/1cent
test "$(pwd)" = "$EXPECTED" || {
  echo "Run from $EXPECTED" >&2
  exit 2
}
test -f .env || {
  echo ".env missing" >&2
  exit 2
}
DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-0}
export DOCKER_BUILDKIT
HOST_PORT=${ONECENT_HOST_PORT:-18013}

"$DOCKER" compose config >/dev/null
"$DOCKER" compose build
"$DOCKER" compose up -d onecent-db

i=0
until "$DOCKER" compose exec -T onecent-db pg_isready -U onecent -d onecent >/dev/null 2>&1; do
  i=$((i + 1))
  test "$i" -lt 60 || { echo "PostgreSQL health timeout" >&2; exit 1; }
  sleep 2
done

"$DOCKER" compose run --rm onecent-api alembic upgrade head
"$DOCKER" compose up -d onecent-api onecent-bot onecent-backup

i=0
until curl -fsS "http://127.0.0.1:$HOST_PORT/health" | grep -q '"status":"ok"'; do
  i=$((i + 1))
  test "$i" -lt 60 || { echo "API health timeout" >&2; exit 1; }
  sleep 2
done

i=0
until "$DOCKER" compose ps onecent-bot | grep -q healthy; do
  i=$((i + 1))
  test "$i" -lt 60 || { echo "Bot health timeout" >&2; exit 1; }
  sleep 2
done

i=0
until "$DOCKER" compose ps onecent-backup | grep -q healthy; do
  i=$((i + 1))
  test "$i" -lt 60 || { echo "Backup scheduler health timeout" >&2; exit 1; }
  sleep 2
done

"$DOCKER" compose ps
BASE_URL="http://127.0.0.1:$HOST_PORT" sh scripts/smoke_local.sh
echo "deploy_nas PASS"
