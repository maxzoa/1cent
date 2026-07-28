#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
BASE_URL=${BASE_URL:-http://127.0.0.1:8013}
DOCKER=${DOCKER:-/usr/local/bin/docker}
if [ -x "$DOCKER" ] && "$DOCKER" compose ps --status running onecent-api >/dev/null 2>&1; then
  "$DOCKER" compose exec -T onecent-api \
    python scripts/load_unpaid.py --base-url http://127.0.0.1:8013 --requests 25 --concurrency 5
else
  python scripts/load_unpaid.py --base-url "$BASE_URL" --requests 25 --concurrency 5
fi
