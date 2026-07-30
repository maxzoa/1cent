#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_MARKETPLACE_061_DEPLOY:-false}" = true || {
  echo "CONFIRM_MARKETPLACE_061_DEPLOY=true required" >&2
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
old_revision=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "SELECT version_num FROM alembic_version")
test -n "$old_revision"
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

set_env_value() {
  key=$1
  value=$2
  temporary=".env.tmp.$$"
  umask 077
  awk -v key="$key" -v value="$value" '
    BEGIN { found = 0 }
    index($0, key "=") == 1 { print key "=" value; found = 1; next }
    { print }
    END { if (!found) print key "=" value }
  ' .env >"$temporary"
  chmod 600 "$temporary"
  mv -f "$temporary" .env
}

resume_service() {
  $DOCKER compose exec -T onecent-db psql -U onecent -d onecent -v ON_ERROR_STOP=1 \
    -c "UPDATE service_settings SET value='true',updated_at=now(),updated_by='marketplace-061-deploy' WHERE key='service_enabled'" >/dev/null
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
    echo "marketplace_061_deploy=FAIL rollback_previous_production=ATTEMPTED" >&2
  elif [ "$complete" != true ] && [ "$built" = true ]; then
    $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
    $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
  elif [ "$paused" = true ]; then
    resume_service || true
  fi
  exit "$status"
}
trap rollback EXIT INT TERM

umask 077
cp .env .env.production.marketplace-061.saved
chmod 600 .env.production.marketplace-061.saved
$DOCKER compose config >/dev/null
sh scripts/backup_db.sh
test -s backups/onecent-latest.sql.gz
sh scripts/restore_drill.sh backups/onecent-latest.sql.gz
set_env_value MAINNET_BACKUP_PATH /backups/onecent-latest.sql.gz
$DOCKER compose config >/dev/null

$DOCKER compose build onecent-api onecent-bot
built=true
$DOCKER compose run --rm --no-deps onecent-api python -c \
  "import asyncio; from onecent import __version__; from onecent.mcp_server import mcp; tools=asyncio.run(mcp.list_tools()); prompts=asyncio.run(mcp.list_prompts()); resources=asyncio.run(mcp.list_resources()); assert __version__=='0.6.1'; assert len(tools)==35; assert [t.name for t in tools[:3]]==['catalog.tools.search','demo.url.pulse','demo.live.pulse']; assert all(t.outputSchema and t.annotations for t in tools); assert all(p.get('description') for t in tools for p in t.inputSchema.get('properties',{}).values()); assert [p.name for p in prompts]==['choose_url_tool']; assert [str(r.uri) for r in resources]==['onecent://buyer-guide']; print('candidate_image=PASS')"
$DOCKER compose run --rm --no-deps onecent-api pip check

atomic_write "$MAINTENANCE_FILE" "$(( $(date +%s) + 1200 ))"
sh scripts/monitor_mainnet_health.sh | grep -q 'maintenance=PASS'
$DOCKER compose exec -T onecent-db psql -U onecent -d onecent -v ON_ERROR_STOP=1 \
  -c "UPDATE service_settings SET value='false',updated_at=now(),updated_by='marketplace-061-deploy' WHERE key='service_enabled'" >/dev/null
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
BASE_URL=http://127.0.0.1:18013 sh scripts/smoke_unpaid_load.sh
$DOCKER compose exec -T onecent-api python scripts/verify_public_release.py \
  --base-url http://127.0.0.1:8013
curl -fsS http://127.0.0.1:18013/status.json | grep -q '"version":"0.6.1"'
rm -f "$MAINTENANCE_FILE"
sh scripts/monitor_mainnet_health.sh | grep -q 'mainnet_health=PASS'

after_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")
test "$after_payments" = "$before_payments"

complete=true
trap - EXIT INT TERM
echo "marketplace_061_deploy=PASS; successful_settlements_unchanged=$after_payments"
