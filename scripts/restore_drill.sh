#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
BACKUP=${1:-}
if [ -z "$BACKUP" ]; then
  BACKUP=$(find backups -type f -name 'onecent-*.sql.gz' -print | sort | tail -1)
fi
test -n "$BACKUP"
test -s "$BACKUP"
case "$BACKUP" in
  *.sql.gz) ;;
  *) echo "restore_drill=FAIL reason=unsupported_backup"; exit 1 ;;
esac

NAME="onecent-restore-drill-$$"
cleanup() {
  "$DOCKER" rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

"$DOCKER" run -d --name "$NAME" --network none \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine >/dev/null

ready=false
attempt=0
while [ "$attempt" -lt 60 ]; do
  # The official image briefly exposes a temporary postmaster during init and
  # then restarts it. pg_isready alone can therefore race with that restart.
  # PID 1 becomes postgres only after the final server is exec'd.
  if "$DOCKER" exec "$NAME" sh -c \
      'test "$(cat /proc/1/comm)" = postgres' >/dev/null 2>&1 && \
     [ "$("$DOCKER" exec "$NAME" psql -At -U postgres -d postgres \
       -c 'SELECT 1' 2>/dev/null)" = "1" ]; then
    ready=true
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done
test "$ready" = true

"$DOCKER" exec "$NAME" psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -c "CREATE ROLE onecent NOLOGIN" >/dev/null
gzip -dc "$BACKUP" | "$DOCKER" exec -i "$NAME" psql \
  -v ON_ERROR_STOP=1 -U postgres -d postgres >/dev/null
tables=$("$DOCKER" exec "$NAME" psql -At -U postgres -d postgres -c \
  "SELECT count(*) FROM pg_catalog.pg_tables WHERE schemaname='public'")
test "$tables" -gt 0
version=$("$DOCKER" exec "$NAME" psql -At -U postgres -d postgres -c \
  "SELECT version_num FROM alembic_version LIMIT 1")
test -n "$version"
echo "restore_drill=PASS tables=$tables migration=$version"
