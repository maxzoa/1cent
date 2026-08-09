#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_ROLLBACK_TESTNET:-false}" = "true" || {
  echo "Set CONFIRM_ROLLBACK_TESTNET=true to perform rollback" >&2
  exit 2
}
test -f .env.testnet.saved || { echo ".env.testnet.saved missing" >&2; exit 2; }
test -f .env || { echo ".env missing" >&2; exit 2; }

stamp=$(date -u +%Y%m%dT%H%M%SZ)
cp -p .env ".env.pre-rollback-$stamp"
chmod 600 ".env.pre-rollback-$stamp"
cp -p .env.testnet.saved .env
chmod 600 .env

DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
"$DOCKER" compose config >/dev/null
"$DOCKER" compose up -d onecent-db onecent-api onecent-bot onecent-backup
STATE_DIR=/volume1/docker/1cent/.state
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
marker_tmp="$STATE_DIR/public-mainnet-active.env.tmp.$$"
umask 077
printf '%s\n' 'PUBLIC_MAINNET_ACTIVE=false' >"$marker_tmp"
mv -f "$marker_tmp" "$STATE_DIR/public-mainnet-active.env"
echo "rollback initiated; run local/public/MCP smoke before declaring success"
