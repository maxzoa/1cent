#!/bin/sh
set -eu

cd /volume1/docker/1cent
DOCKER=${DOCKER:-/usr/local/bin/docker}
ENDPOINT=${MCP_ENDPOINT:-https://1cent.maxzoa.ru/mcp}
IMAGE=1cent-onecent-api:latest
SCRIPT=/volume1/docker/1cent/scripts/test_mcp_client.py

if [ "${1:-}" = "--paid" ]; then
  test -f .env.test
  before=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
    "select count(*) from payment_events where settlement_status='success'")
  $DOCKER run --rm --env-file /volume1/docker/1cent/.env.test \
    -v "$SCRIPT:/scripts/test_mcp_client.py:ro" "$IMAGE" \
    python /scripts/test_mcp_client.py --endpoint "$ENDPOINT" --paid
  after=$($DOCKER compose exec -T onecent-db psql -U onecent -d onecent -Atc \
    "select count(*) from payment_events where settlement_status='success'")
  test "$after" -eq $((before + 1))
  echo "smoke_mcp PASS: initialize + tools/list + unpaid + one paid + DB + idempotency"
else
  $DOCKER run --rm \
    -e EXPECTED_X402_NETWORK="${EXPECTED_X402_NETWORK:-eip155:84532}" \
    -e EXPECTED_X402_AMOUNT="${EXPECTED_X402_AMOUNT:-3000}" \
    -v "$SCRIPT:/scripts/test_mcp_client.py:ro" "$IMAGE" \
    python /scripts/test_mcp_client.py --endpoint "$ENDPOINT"
  echo "smoke_mcp PASS: initialize + tools/list + schemas + unpaid"
fi
