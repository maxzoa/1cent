#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
test -f .env
DOCKER=${DOCKER:-/usr/local/bin/docker}
BASE_URL=${BASE_URL:-http://127.0.0.1:8013}
EXPECTED_X402_NETWORK=${EXPECTED_X402_NETWORK:-eip155:84532}
test -x "$DOCKER" || DOCKER=docker

"$DOCKER" compose ps --status running
"$DOCKER" compose exec -T onecent-api alembic current
curl -fsS "$BASE_URL/health" | grep -q '"status":"ok"'
curl -fsS "$BASE_URL/info" | grep -q "$EXPECTED_X402_NETWORK"
curl -fsS "$BASE_URL/status.json" | grep -q '"paid_tools":32'
curl -fsS "$BASE_URL/v1/demo/pulse" | grep -q '"network_request_performed":false'

code=$(curl -A 'onecent-smoke/1.0' -sS -o /tmp/onecent-unpaid.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fresh":false}' \
  "$BASE_URL/v1/url/pulse")
test "$code" = "402"

if [ "$EXPECTED_X402_NETWORK" = "eip155:84532" ]; then
  "$DOCKER" compose exec -T onecent-api python -c "import os,httpx; h={'X-Development-Bypass':os.environ['INTERNAL_API_TOKEN']}; c=httpx.Client(timeout=20); r=c.post('http://127.0.0.1:8013/v1/url/pulse',headers=h,json={'url':'http://127.0.0.1','fresh':True}); assert r.status_code==400, r.status_code; r=c.post('http://127.0.0.1:8013/v1/url/pulse',headers=h,json={'url':'https://example.com','fresh':True}); assert r.status_code==200, (r.status_code,r.text); assert r.json()['reachable'] is True"
fi

"$DOCKER" compose ps onecent-bot | grep -q 'healthy'
echo "smoke_local PASS"
