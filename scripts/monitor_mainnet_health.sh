#!/bin/sh
set -eu

PROJECT_DIR=${ONECENT_PROJECT_DIR:-/volume1/docker/1cent}
STATE_DIR="$PROJECT_DIR/.state"
MARKER_FILE="$STATE_DIR/public-mainnet-active.env"
FAILURE_FILE="$STATE_DIR/mainnet-health.failures"
PUBLIC_FAILURE_FILE="$STATE_DIR/public-health.failures"
PUBLIC_ALERTED_FILE="$STATE_DIR/public-health.alerted"
MAINTENANCE_FILE="$STATE_DIR/maintenance-until"
LOCK_FILE="$STATE_DIR/mainnet-health.lock"
BASE_URL=${BASE_URL:-https://1cent.maxzoa.ru}
LOCAL_BASE_URL=${LOCAL_BASE_URL:-http://127.0.0.1:18013}
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

runtime_state_raw=$(
  "$DOCKER" compose exec -T onecent-api sh -c \
    'printf "%s|%s|%s|%s\n" "$APP_ENV" "$X402_ENVIRONMENT" "$X402_NETWORK" "$OWNER_MAINNET_APPROVED"' \
    | tr -d '\r'
)

# Older saved testnet profiles omitted OWNER_MAINNET_APPROVED.  Missing approval
# is always equivalent to false; it must never turn testnet monitoring into a
# rollback candidate.
old_ifs=$IFS
IFS='|'
set -- $runtime_state_raw
IFS=$old_ifs
runtime_state="${1:-}|${2:-}|${3:-}|${4:-false}"

if [ "$runtime_state" = "development|testnet|eip155:84532|false" ] || \
   [ "$runtime_state" = "production|testnet|eip155:84532|false" ]; then
  atomic_write "$MARKER_FILE" "PUBLIC_MAINNET_ACTIVE=false"
  atomic_write "$FAILURE_FILE" "0"
  atomic_write "$PUBLIC_FAILURE_FILE" "0"
  rm -f "$STATE_DIR/monitor-force-failure" "$STATE_DIR/monitor-dry-run" \
    "$STATE_DIR/rollback-in-progress" "$PUBLIC_ALERTED_FILE"
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

probe_mainnet() {
  probe_base=$1
  "$CURL" -fsS --max-time 10 "$probe_base/health" | grep -q '"status":"ok"' && \
    "$CURL" -fsS --max-time 10 "$probe_base/info" | grep -q '"network":"eip155:8453"'
}

if probe_mainnet "$LOCAL_BASE_URL"; then
  atomic_write "$FAILURE_FILE" "0"
  if probe_mainnet "$BASE_URL"; then
    atomic_write "$PUBLIC_FAILURE_FILE" "0"
    rm -f "$PUBLIC_ALERTED_FILE"
    echo "mainnet_health=PASS"
    exit 0
  fi

  # Public TLS/tunnel failures cannot be repaired by replacing a healthy API.
  # Track and alert separately; never roll back a healthy Mainnet runtime for
  # a Cloudflare/network-only incident.
  public_failures=0
  if [ -f "$PUBLIC_FAILURE_FILE" ]; then
    case "$(sed -n '1p' "$PUBLIC_FAILURE_FILE")" in
      ''|*[!0-9]*) public_failures=0 ;;
      *) public_failures=$(sed -n '1p' "$PUBLIC_FAILURE_FILE") ;;
    esac
  fi
  public_failures=$((public_failures + 1))
  atomic_write "$PUBLIC_FAILURE_FILE" "$public_failures"
  echo "local_mainnet_health=PASS"
  echo "public_probe=DEGRADED"
  echo "public_failure_count=$public_failures"
  if [ "$public_failures" -ge 3 ] && [ ! -f "$PUBLIC_ALERTED_FILE" ]; then
    if "$DOCKER" compose exec -T onecent-bot python -c \
      "import os,httpx; httpx.post('https://api.telegram.org/bot'+os.environ['TELEGRAM_BOT_TOKEN']+'/sendMessage', json={'chat_id':os.environ['TELEGRAM_REPORT_CHAT_ID'],'text':'1cent public endpoint degraded; local Mainnet API remains healthy; rollback blocked'}, timeout=10).raise_for_status()" \
      >/dev/null 2>&1; then
      atomic_write "$PUBLIC_ALERTED_FILE" "true"
      echo "telegram_public_alert=PASS"
    else
      echo "telegram_public_alert=FAIL"
    fi
  fi
  exit 1
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
  atomic_write "$PUBLIC_FAILURE_FILE" "0"
  rm -f "$STATE_DIR/rollback-in-progress" "$STATE_DIR/monitor-force-failure" \
    "$STATE_DIR/monitor-dry-run" "$PUBLIC_ALERTED_FILE"
  echo "rollback=PASS"
  exit 1
fi

echo "rollback=FAIL"
exit 2
