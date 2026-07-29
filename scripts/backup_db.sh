#!/bin/sh
set -eu

cd /volume1/docker/1cent
test -f .env
BACKUP_DIR=/volume1/docker/1cent/backups
DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
umask 077
mkdir -p "$BACKUP_DIR"
# The API readiness gate must stat a known backup path from its non-root
# container user. 711 prevents directory listing while allowing traversal;
# dump contents remain owner-only at mode 600.
chmod 711 "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TARGET="$BACKUP_DIR/onecent-$STAMP.sql.gz"
LATEST="$BACKUP_DIR/onecent-latest.sql.gz"
LATEST_TMP="$BACKUP_DIR/.onecent-latest.sql.gz.tmp.$$"

notify_failure() {
  "$DOCKER" compose run --rm --no-deps onecent-bot python -c \
    "import os,urllib.parse,urllib.request; token=os.getenv('TELEGRAM_BOT_TOKEN'); chat=os.getenv('TELEGRAM_REPORT_CHAT_ID'); token and chat and urllib.request.urlopen(urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=urllib.parse.urlencode({'chat_id':chat,'text':'1cent database backup failed'}).encode()),timeout=10).read()" \
    >/dev/null 2>&1 || true
}

if ! "$DOCKER" compose exec -T onecent-db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip -9 >"$TARGET"; then
  rm -f "$TARGET"
  notify_failure
  exit 1
fi
test -s "$TARGET" || { rm -f "$TARGET"; notify_failure; exit 1; }
chmod 600 "$TARGET"
rm -f "$LATEST_TMP"
ln "$TARGET" "$LATEST_TMP"
chmod 600 "$LATEST_TMP"
mv -f "$LATEST_TMP" "$LATEST"
find "$BACKUP_DIR" -type f -name 'onecent-*.sql.gz' \
  ! -name 'onecent-latest.sql.gz' -mtime +14 -delete
echo "backup PASS: $TARGET"
