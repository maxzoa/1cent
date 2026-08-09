#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
ENV_FILE=${ENV_FILE:-.env}
test -f "$ENV_FILE" || { echo "BLOCKER: env file missing"; exit 1; }

DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
IMAGE=${ONECENT_IMAGE:-1cent-onecent-api:latest}
BACKUP_FILE=${BACKUP_FILE:-}
EXPECTED_RUNTIME_BACKUP=/backups/onecent-latest.sql.gz
CONFIGURED_BACKUP=$(sed -n 's/^MAINNET_BACKUP_PATH=//p' "$ENV_FILE" | tail -n 1)
test "$CONFIGURED_BACKUP" = "$EXPECTED_RUNTIME_BACKUP" || {
  echo "BLOCKER: MAINNET_BACKUP_PATH must match the API container mount" >&2
  exit 1
}

# Read-only: env file is mounted, never printed, and no Compose service starts.
if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
  "$DOCKER" run --rm --user "$(id -u):$(id -g)" --network none --read-only \
    -v "$(pwd)/$ENV_FILE:/run/onecent-preflight.env:ro" \
    -v "$BACKUP_FILE:$EXPECTED_RUNTIME_BACKUP:ro" \
    -e MAINNET_BACKUP_PATH="$EXPECTED_RUNTIME_BACKUP" \
    "$IMAGE" python -m onecent.preflight --env-file /run/onecent-preflight.env
else
  "$DOCKER" run --rm --user "$(id -u):$(id -g)" --network none --read-only \
    -v "$(pwd)/$ENV_FILE:/run/onecent-preflight.env:ro" \
    "$IMAGE" python -m onecent.preflight --env-file /run/onecent-preflight.env
fi
