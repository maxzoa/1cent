#!/bin/sh
set -eu

cd /volume1/docker/1cent
test "${CONFIRM_BUYER_ACTIVATION_070_CANDIDATE:-false}" = true || {
  echo "CONFIRM_BUYER_ACTIVATION_070_CANDIDATE=true required" >&2
  exit 2
}
test -f .env

DOCKER=${DOCKER:-/usr/local/bin/docker}
CANDIDATE_DIR=.state/candidate-070
KEY_FILE="$CANDIDATE_DIR/offer_receipt_ed25519.pem"
mkdir -p "$CANDIDATE_DIR"
chmod 700 "$CANDIDATE_DIR"

api_id_before=$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-api-1)
api_started_before=$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-api-1)
bot_id_before=$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-bot-1)
bot_started_before=$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-bot-1)
db_id_before=$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-db-1)
db_started_before=$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-db-1)
old_api_image=$($DOCKER inspect -f '{{.Image}}' 1cent-onecent-api-1)
old_bot_image=$($DOCKER inspect -f '{{.Image}}' 1cent-onecent-bot-1)
before_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")

restore_tags() {
  $DOCKER image tag "$old_api_image" 1cent-onecent-api:latest >/dev/null 2>&1 || true
  $DOCKER image tag "$old_bot_image" 1cent-onecent-bot:latest >/dev/null 2>&1 || true
}
trap restore_tags EXIT INT TERM

$DOCKER compose config >/dev/null
$DOCKER compose build onecent-api onecent-bot
$DOCKER image tag 1cent-onecent-api:latest 1cent-onecent-api:candidate-070
$DOCKER image tag 1cent-onecent-bot:latest 1cent-onecent-bot:candidate-070

rm -f "$KEY_FILE"
$DOCKER run --rm --user 0:0 \
  -v "$PWD/$CANDIDATE_DIR:/out" \
  --entrypoint python \
  1cent-onecent-api:candidate-070 \
  /app/scripts/generate_offer_receipt_key.py \
  --output /out/offer_receipt_ed25519.pem \
  --owner-uid 10001 --owner-gid 10001 >/dev/null
test "$(stat -c '%a' "$KEY_FILE")" = 600
test "$(stat -c '%u:%g' "$KEY_FILE")" = 10001:10001

$DOCKER run --rm --env-file .env \
  -e APP_ENV=development \
  -e X402_ENVIRONMENT=testnet \
  -e X402_NETWORK=eip155:84532 \
  -e OWNER_MAINNET_APPROVED=false \
  -e OFFER_RECEIPT_ENABLED=true \
  -e OFFER_RECEIPT_SIGNING_KEY_PATH=/run/secrets/offer_receipt_ed25519.pem \
  -e OFFER_RECEIPT_KID=did:web:1cent.maxzoa.ru#offer-receipt-key-1 \
  -v "$PWD/$KEY_FILE:/run/secrets/offer_receipt_ed25519.pem:ro" \
  --entrypoint python \
  1cent-onecent-api:candidate-070 -c \
  "import asyncio; from onecent import __version__; from onecent.config import Settings; from onecent.mcp_server import mcp; from onecent.services.offer_receipt import OfferReceiptSigner,did_document; s=Settings(); signer=OfferReceiptSigner.load(s.offer_receipt_signing_key_path,s.offer_receipt_kid); tools=asyncio.run(mcp.list_tools()); prompts=asyncio.run(mcp.list_prompts()); resources=asyncio.run(mcp.list_resources()); assert __version__=='0.7.0'; assert len(tools)==35; assert len(prompts)==1; assert len(resources)==1; assert len(did_document(signer)['verificationMethod'])==1; print('candidate_contract=PASS')"
$DOCKER run --rm --entrypoint pip 1cent-onecent-api:candidate-070 check
$DOCKER run --rm --entrypoint alembic 1cent-onecent-api:candidate-070 heads | grep -q '^0008 (head)$'

restore_tags
trap - EXIT INT TERM

test "$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-api-1)" = "$api_id_before"
test "$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-api-1)" = "$api_started_before"
test "$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-bot-1)" = "$bot_id_before"
test "$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-bot-1)" = "$bot_started_before"
test "$($DOCKER inspect -f '{{.Id}}' 1cent-onecent-db-1)" = "$db_id_before"
test "$($DOCKER inspect -f '{{.State.StartedAt}}' 1cent-onecent-db-1)" = "$db_started_before"
curl -fsS http://127.0.0.1:18013/health | grep -q '"status":"ok"'
curl -fsS https://1cent.maxzoa.ru/health | grep -q '"status":"ok"'
after_payments=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
  "select count(id)||'|'||coalesce(sum(amount_atomic),0) from payment_events where settlement_status='success'")
test "$after_payments" = "$before_payments"

echo "candidate_release_070=PASS; runtime_unchanged=PASS; successful_settlements_unchanged=$after_payments"
