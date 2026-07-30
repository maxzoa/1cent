#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_BUYER_ACTIVATION_070_DEPLOY:-false}" = true || {
  echo "CONFIRM_BUYER_ACTIVATION_070_DEPLOY=true required" >&2
  exit 2
}
test -f .env

DOCKER=${DOCKER:-/usr/local/bin/docker}
STATE_DIR=.state
MAINTENANCE_FILE="$STATE_DIR/maintenance-until"
SAVED_ENV=.env.production.buyer-070.saved
KEY_DIR=secrets
KEY_FILE="$KEY_DIR/offer_receipt_ed25519.pem"
mkdir -p "$STATE_DIR" logs "$KEY_DIR"
chmod 700 "$STATE_DIR" "$KEY_DIR"

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
    -c "UPDATE service_settings SET value='true',updated_at=now(),updated_by='buyer-activation-070-deploy' WHERE key='service_enabled'" >/dev/null
  paused=false
}

rollback() {
  status=$?
  rm -f "$MAINTENANCE_FILE"
  if [ "$complete" != true ] && [ "$switched" = true ]; then
    $DOCKER compose stop onecent-api onecent-bot >/dev/null 2>&1 || true
    $DOCKER compose run --rm onecent-api alembic downgrade "$old_revision" >/dev/null 2>&1 || true
    if [ -f "$SAVED_ENV" ]; then
      cp "$SAVED_ENV" .env
      chmod 600 .env
    fi
    $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
    $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
    $DOCKER compose up -d --no-deps --force-recreate onecent-api onecent-bot >/dev/null 2>&1 || true
    resume_service || true
    echo "buyer_activation_070_deploy=FAIL rollback_previous_production=ATTEMPTED" >&2
  elif [ "$complete" != true ] && [ "$built" = true ]; then
    if [ -f "$SAVED_ENV" ]; then
      cp "$SAVED_ENV" .env
      chmod 600 .env
    fi
    $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
    $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
  elif [ "$paused" = true ]; then
    resume_service || true
  fi
  exit "$status"
}
trap rollback EXIT INT TERM

umask 077
cp .env "$SAVED_ENV"
chmod 600 "$SAVED_ENV"
$DOCKER compose config >/dev/null
sh scripts/backup_db.sh
test -s backups/onecent-latest.sql.gz
sh scripts/restore_drill.sh backups/onecent-latest.sql.gz
set_env_value MAINNET_BACKUP_PATH /backups/onecent-latest.sql.gz

$DOCKER compose build onecent-api onecent-bot
built=true
if [ ! -s "$KEY_FILE" ]; then
  $DOCKER run --rm --user 0:0 \
    -v "$PWD/$KEY_DIR:/out" \
    --entrypoint python \
    1cent-onecent-api \
    /app/scripts/generate_offer_receipt_key.py \
    --output /out/offer_receipt_ed25519.pem \
    --owner-uid 10001 --owner-gid 10001 >/dev/null
fi
test -f "$KEY_FILE"
test "$(stat -c '%a' "$KEY_FILE")" = 600
test "$(stat -c '%u:%g' "$KEY_FILE")" = 10001:10001
set_env_value OFFER_RECEIPT_ENABLED true
set_env_value OFFER_RECEIPT_SIGNING_KEY_PATH /run/secrets/offer_receipt_ed25519.pem
set_env_value OFFER_RECEIPT_KID did:web:1cent.maxzoa.ru#offer-receipt-key-1
set_env_value OFFER_RECEIPT_INCLUDE_TRANSACTION false
$DOCKER compose config >/dev/null

$DOCKER compose run --rm --no-deps onecent-api python -c \
  "import asyncio,os; from onecent import __version__; from onecent.config import Settings; from onecent.mcp_server import mcp; from onecent.services.offer_receipt import OfferReceiptSigner; s=Settings(); signer=OfferReceiptSigner.load(s.offer_receipt_signing_key_path,s.offer_receipt_kid); tools=asyncio.run(mcp.list_tools()); prompts=asyncio.run(mcp.list_prompts()); resources=asyncio.run(mcp.list_resources()); assert __version__=='0.7.0'; assert s.app_env=='production' and s.x402_environment=='mainnet' and s.x402_network=='eip155:8453'; assert s.x402_facilitator_url=='https://facilitator.payai.network'; assert s.x402_asset.lower()=='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'; assert s.x402_pay_to.lower()=='0x4798e8401ba3b1566685257c82d06303ab90ea35'; assert not s.development_bypass_enabled; assert not s.mainnet_daily_settlement_limit_enabled and not s.mainnet_daily_revenue_limit_enabled; assert not os.getenv('ONECENT_BUYER_PRIVATE_KEY') and not os.getenv('SELLER_PRIVATE_KEY'); assert len(tools)==35; assert len(prompts)==1; assert len(resources)==1; assert signer.kid.startswith('did:web:'); print('candidate_image=PASS')"
$DOCKER compose run --rm --no-deps onecent-api pip check

atomic_write "$MAINTENANCE_FILE" "$(( $(date +%s) + 1200 ))"
sh scripts/monitor_mainnet_health.sh | grep -q 'maintenance=PASS'
$DOCKER compose exec -T onecent-db psql -U onecent -d onecent -v ON_ERROR_STOP=1 \
  -c "UPDATE service_settings SET value='false',updated_at=now(),updated_by='buyer-activation-070-deploy' WHERE key='service_enabled'" >/dev/null
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
$DOCKER compose exec -T onecent-api python -c \
  "import httpx; from x402.http import decode_payment_required_header; c=httpx.Client(base_url='http://127.0.0.1:8013',timeout=20); r=c.post('/v1/url/status',json={'url':'https://example.com/','fresh':False}); assert r.status_code==402; d=decode_payment_required_header(r.headers['payment-required']); assert d.extensions['offer-receipt']['info']['offers']; assert c.get('/.well-known/did.json').status_code==200; assert len(c.get('/v1/products').json())==4; assert c.get('/try').status_code==200; print('buyer_activation_public_contract=PASS')"
curl -fsS http://127.0.0.1:18013/status.json | grep -q '"version":"0.7.0"'
rm -f "$MAINTENANCE_FILE"
sh scripts/monitor_mainnet_health.sh | grep -q 'mainnet_health=PASS'

after_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")
test "$after_payments" = "$before_payments"

complete=true
trap - EXIT INT TERM
echo "buyer_activation_070_deploy=PASS; successful_settlements_unchanged=$after_payments"
