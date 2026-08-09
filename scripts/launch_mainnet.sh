#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_PUBLIC_MAINNET:-false}" = "true" || {
  echo "Set CONFIRM_PUBLIC_MAINNET=true to launch" >&2
  exit 2
}
test -f .env.mainnet.production
test -f .env.testnet.saved
test "$(stat -c %a .env.mainnet.production)" = "600"
test "$(stat -c %a .env.testnet.saved)" = "600"

DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
STATE_DIR=/volume1/docker/1cent/.state
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
exec 9>"$STATE_DIR/mainnet-health.lock"
flock -x 9

switched=false
on_exit() {
  rc=$?
  trap - EXIT
  if [ "$rc" -ne 0 ] && [ "$switched" = "true" ]; then
    echo "launch failed; automatic testnet rollback" >&2
    CONFIRM_ROLLBACK_TESTNET=true sh scripts/rollback_testnet.sh || true
  fi
  exit "$rc"
}
trap on_exit EXIT

stamp=$(date -u +%Y%m%dT%H%M%SZ)
cp -p .env ".env.pre-mainnet-$stamp"
chmod 600 ".env.pre-mainnet-$stamp"
cp -p .env.mainnet.production .env
chmod 600 .env
switched=true

"$DOCKER" compose config >/dev/null
"$DOCKER" compose up -d onecent-db onecent-api onecent-bot onecent-backup

attempt=0
until curl -fsS --max-time 5 http://127.0.0.1:18013/health | grep -q '"status":"ok"' && \
      curl -fsS --max-time 5 http://127.0.0.1:18013/info | grep -q '"network":"eip155:8453"'; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 36 ] || exit 1
  sleep 5
done

marker_tmp="$STATE_DIR/public-mainnet-active.env.tmp.$$"
umask 077
printf '%s\n' 'PUBLIC_MAINNET_ACTIVE=true' >"$marker_tmp"
mv -f "$marker_tmp" "$STATE_DIR/public-mainnet-active.env"
printf '%s\n' '0' >"$STATE_DIR/mainnet-health.failures.tmp.$$"
mv -f "$STATE_DIR/mainnet-health.failures.tmp.$$" "$STATE_DIR/mainnet-health.failures"
echo "public_mainnet_switch=PASS"
trap - EXIT
