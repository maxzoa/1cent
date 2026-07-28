#!/bin/sh
set -eu

PROJECT_DIR=${ONECENT_PROJECT_DIR:-/volume1/docker/1cent}
STATE_DIR="$PROJECT_DIR/.state"
MARKER_FILE="$STATE_DIR/public-mainnet-active.env"
FAILURE_FILE="$STATE_DIR/mainnet-health.failures"
MAINTENANCE_FILE="$STATE_DIR/maintenance-until"
LOCK_FILE="$STATE_DIR/mainnet-health.lock"
BASE_URL=${BASE_URL:-https://1cent.maxzoa.ru}
DOCKER=${DOCKER:-/usr/local/bin/docker}
CURL=${CURL:-curl}
FLOCK=${FLOCK:-flock}

cd "$PROJECT_DIR"
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
test -x "$DOCKER" || DOCKER=docker

exec 9>"$LOCK_FILE"
if ! "$FLOCK" -n 9; then
  echo "overlap_blocked=PASS"
  exit 0
fi

atomic_write() {
  target=$1
  value=$2
  temporary="$target.tmp.$$"
  umask 077
  printf '%s\n' "$value" >"$temporary"
  mv -f "$temporary" "$target"
}

runtime_state=$(
  "$DOCKER" compose exec -T onecent-api python -c \
    "from onecent.config import get_settings; s=get_settings(); print('|'.join((s.app_env,s.x402_environment,s.x402_network,str(s.owner_mainnet_approved).lower())))"
)

if [ "$runtime_state" = "development|testnet|eip155:84532|false" ] || \
   [ "$runtime_state" = "production|testnet|eip155:84532|false" ]; then
  atomic_write "$MARKER_FILE" "PUBLIC_MAINNET_ACTIVE=false"
  atomic_write "$FAILURE_FILE" "0"
  rm -f "$STATE_DIR/monitor-force-failure" "$STATE_DIR/monitor-dry-run" \
    "$STATE_DIR/rollback-in-progress"
  echo "testnet_noop=PASS"
  exit 0
fi

marker_valid=false
if [ -f "$MARKER_FILE" ] && \
   [ "$(wc -l <"$MARKER_FILE" | tr -d ' ')" = "1" ] && \
   [ "$(sed -n '1p' "$MARKER_FILE")" = "PUBLIC_MAINNET_ACTIVE=true" ]; then
  marker_valid=true
fi

if [ "$marker_valid" != "true" ] || \
   [ "$runtime_state" != "production|mainnet|eip155:8453|true" ]; then
  echo "rollback_gate=BLOCKED"
  echo "reason=valid marker and actual Base Mainnet runtime required"
  exit 1
fi

if [ -f "$MAINTENANCE_FILE" ]; then
  maintenance_until=$(sed -n '1p' "$MAINTENANCE_FILE")
  now=$(date +%s)
  case "$maintenance_until" in
    ''|*[!0-9]*) rm -f "$MAINTENANCE_FILE" ;;
    *)
      if [ "$maintenance_until" -gt "$now" ] && \
         [ "$maintenance_until" -le $((now + 1200)) ]; then
        echo "maintenance=PASS"
        exit 0
      fi
      rm -f "$MAINTENANCE_FILE"
      ;;
  esac
fi

if "$CURL" -fsS --max-time 10 "$BASE_URL/health" | grep -q '"status":"ok"' && \
   "$CURL" -fsS --max-time 10 "$BASE_URL/info" | grep -q '"network":"eip155:8453"'; then
  atomic_write "$FAILURE_FILE" "0"
  echo "mainnet_health=PASS"
  exit 0
fi

failures=0
if [ -f "$FAILURE_FILE" ]; then
  case "$(sed -n '1p' "$FAILURE_FILE")" in
    ''|*[!0-9]*) failures=0 ;;
    *) failures=$(sed -n '1p' "$FAILURE_FILE") ;;
  esac
fi
failures=$((failures + 1))
atomic_write "$FAILURE_FILE" "$failures"
echo "mainnet_failure_count=$failures"

if [ "$failures" -lt 3 ]; then
  exit 1
fi

atomic_write "$STATE_DIR/rollback-in-progress" "true"
if "$DOCKER" compose exec -T onecent-bot python -c \
  "import os,httpx; httpx.post('https://api.telegram.org/bot'+os.environ['TELEGRAM_BOT_TOKEN']+'/sendMessage', json={'chat_id':os.environ['TELEGRAM_REPORT_CHAT_ID'],'text':'1cent MAINNET unhealthy: automatic rollback to testnet started'}, timeout=10).raise_for_status()" \
  >/dev/null 2>&1; then
  echo "telegram_alert=PASS"
else
  echo "telegram_alert=FAIL"
fi

if CONFIRM_ROLLBACK_TESTNET=true sh scripts/rollback_testnet.sh; then
  atomic_write "$MARKER_FILE" "PUBLIC_MAINNET_ACTIVE=false"
  atomic_write "$FAILURE_FILE" "0"
  rm -f "$STATE_DIR/rollback-in-progress" "$STATE_DIR/monitor-force-failure" \
    "$STATE_DIR/monitor-dry-run"
  echo "rollback=PASS"
  exit 1
fi

echo "rollback=FAIL"
exit 2
