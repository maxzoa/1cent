#!/bin/sh
set -eu

BACKUP_DIR=${BACKUP_DIR:-/backups}
BACKUP_INTERVAL_SECONDS=${BACKUP_INTERVAL_SECONDS:-21600}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-14}
POSTGRES_HOST=${POSTGRES_HOST:-onecent-db}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

case "$BACKUP_INTERVAL_SECONDS" in
  ''|*[!0-9]*) echo "invalid backup interval" >&2; exit 2 ;;
esac
case "$BACKUP_RETENTION_DAYS" in
  ''|*[!0-9]*) echo "invalid backup retention" >&2; exit 2 ;;
esac
test "$BACKUP_INTERVAL_SECONDS" -ge 3600 || {
  echo "backup interval must be at least one hour" >&2
  exit 2
}

umask 077
mkdir -p "$BACKUP_DIR"
chmod 711 "$BACKUP_DIR"

backup_once() {
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  target="$BACKUP_DIR/onecent-$stamp.sql.gz"
  latest="$BACKUP_DIR/onecent-latest.sql.gz"
  latest_tmp="$BACKUP_DIR/.onecent-latest.sql.gz.tmp.$$"
  if ! pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip -9 >"$target"; then
    rm -f "$target"
    echo "backup=FAIL" >&2
    return 1
  fi
  test -s "$target" || { rm -f "$target"; echo "backup=EMPTY" >&2; return 1; }
  chmod 600 "$target"
  rm -f "$latest_tmp"
  ln "$target" "$latest_tmp"
  chmod 600 "$latest_tmp"
  mv -f "$latest_tmp" "$latest"
  find "$BACKUP_DIR" -type f -name 'onecent-*.sql.gz' \
    ! -name 'onecent-latest.sql.gz' -mtime "+$BACKUP_RETENTION_DAYS" -delete
  echo "backup=PASS timestamp=$stamp"
}

while :; do
  backup_once || true
  sleep "$BACKUP_INTERVAL_SECONDS"
done
