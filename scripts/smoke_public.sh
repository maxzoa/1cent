#!/bin/sh
set -eu

BASE_URL=${1:-https://1cent.maxzoa.ru}
EXPECTED_X402_NETWORK=${EXPECTED_X402_NETWORK:-eip155:84532}
curl -A 'onecent-smoke/1.0' -fsS "$BASE_URL/health" | grep -q '"status":"ok"'
curl -A 'onecent-smoke/1.0' -fsS "$BASE_URL/info" | grep -q "$EXPECTED_X402_NETWORK"
curl -A 'onecent-smoke/1.0' -fsS "$BASE_URL/status.json" | grep -q '"paid_tools":32'
curl -A 'onecent-smoke/1.0' -fsS "$BASE_URL/v1/demo/pulse" | grep -q '"network_request_performed":false'
curl -A 'onecent-smoke/1.0' -fsS "$BASE_URL/.well-known/security.txt" | grep -q '^Contact: mailto:'
code=$(curl -A 'onecent-smoke/1.0' -sS -o /tmp/onecent-public-paid.json -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","fresh":false}' \
  "$BASE_URL/v1/url/pulse")
test "$code" = "402"
code=$(curl -A 'onecent-smoke/1.0' -sS -o /tmp/onecent-internal.json -w '%{http_code}' "$BASE_URL/internal/report")
test "$code" = "404"
echo "smoke_public PASS"
