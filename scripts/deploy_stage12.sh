#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_STAGE12_DEPLOY:-false}" = true || {
  echo "CONFIRM_STAGE12_DEPLOY=true required" >&2
  exit 2
}
test -f .env

DOCKER=${DOCKER:-/usr/local/bin/docker}
STATE_DIR=.state
MAINTENANCE_FILE="$STATE_DIR/maintenance-until"
mkdir -p "$STATE_DIR" logs
chmod 700 "$STATE_DIR"

old_api_image=$($DOCKER inspect -f '{{.Image}}' 1cent-onecent-api-1)
old_bot_image=$($DOCKER inspect -f '{{.Image}}' 1cent-onecent-bot-1)
old_revision=$($DOCKER compose exec -T onecent-api alembic current | awk 'NR==1 {print $1}')
before_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")
switched=false
paused=false
complete=false
built=false

atomic_write() {
  target=$1
  value=$2
  temporary="$target.tmp.$$"
  umask 077
  printf '%s\n' "$value" >"$temporary"
  mv -f "$temporary" "$target"
}

resume_service() {
  $DOCKER compose exec -T onecent-db psql -U onecent -d onecent -v ON_ERROR_STOP=1 \
    -c "UPDATE service_settings SET value='true',updated_at=now(),updated_by='stage12-deploy' WHERE key='service_enabled'" >/dev/null
  paused=false
}

rollback() {
  status=$?
  rm -f "$MAINTENANCE_FILE"
  if [ "$complete" != true ] && [ "$switched" = true ]; then
    $DOCKER compose run --rm onecent-api alembic downgrade "$old_revision" >/dev/null 2>&1 || true
    $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
    $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
    $DOCKER compose up -d --no-deps --force-recreate onecent-api onecent-bot >/dev/null 2>&1 || true
    resume_service || true
    echo "stage12_deploy=FAIL rollback_previous_production=ATTEMPTED" >&2
  elif [ "$complete" != true ] && [ "$built" = true ]; then
    $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
    $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
  elif [ "$paused" = true ]; then
    resume_service || true
  fi
  exit "$status"
}
trap rollback EXIT INT TERM

$DOCKER compose config >/dev/null
sh scripts/backup_db.sh
umask 077
cp .env .env.production.stage12.saved
chmod 600 .env.production.stage12.saved

$DOCKER compose build onecent-api onecent-bot
built=true
$DOCKER compose run --rm --no-deps onecent-api python -c \
  "import asyncio; from onecent import __version__; from onecent.mcp_server import mcp; tools=asyncio.run(mcp.list_tools()); assert __version__=='0.3.0'; assert len(tools)==34; assert [t.name for t in tools[:2]]==['catalog_search','demo_url_pulse']; assert all(t.outputSchema and t.annotations for t in tools); print('candidate_image=PASS')"

atomic_write "$MAINTENANCE_FILE" "$(( $(date +%s) + 1200 ))"
sh scripts/monitor_mainnet_health.sh | grep -q 'maintenance=PASS'
$DOCKER compose exec -T onecent-db psql -U onecent -d onecent -v ON_ERROR_STOP=1 \
  -c "UPDATE service_settings SET value='false',updated_at=now(),updated_by='stage12-deploy' WHERE key='service_enabled'" >/dev/null
paused=true

$DOCKER compose run --rm onecent-api alembic upgrade head
switched=true
$DOCKER compose up -d --no-deps --force-recreate onecent-api

i=0
until curl -fsS http://127.0.0.1:18013/health | grep -q '"status":"ok"'; do
  i=$((i + 1)); test "$i" -lt 120; sleep 2
done
resume_service
$DOCKER compose up -d --no-deps --force-recreate onecent-bot
i=0
until [ "$($DOCKER inspect -f '{{.State.Health.Status}}' 1cent-onecent-bot-1)" = healthy ]; do
  i=$((i + 1)); test "$i" -lt 60; sleep 2
done

BASE_URL=http://127.0.0.1:18013 EXPECTED_X402_NETWORK=eip155:8453 sh scripts/smoke_local.sh
EXPECTED_X402_NETWORK=eip155:8453 sh scripts/smoke_public.sh
EXPECTED_X402_NETWORK=eip155:8453 EXPECTED_X402_AMOUNT=1000 sh scripts/smoke_mcp.sh
curl -fsS http://127.0.0.1:18013/status.json | grep -q '"version":"0.3.0"'
curl -fsS http://127.0.0.1:18013/v1/demo/pulse | grep -q '"network_request_performed":false'
rm -f "$MAINTENANCE_FILE"
sh scripts/monitor_mainnet_health.sh | grep -q 'mainnet_health=PASS'

after_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")
test "$after_payments" = "$before_payments"

complete=true
trap - EXIT INT TERM
echo "stage12_deploy=PASS; successful_settlements_unchanged=$after_payments"
