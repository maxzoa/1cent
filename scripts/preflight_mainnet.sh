#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
ENV_FILE=${ENV_FILE:-.env}
test -f "$ENV_FILE" || { echo "BLOCKER: env file missing"; exit 1; }

DOCKER=${DOCKER:-/usr/local/bin/docker}
test -x "$DOCKER" || DOCKER=docker
IMAGE=${ONECENT_IMAGE:-1cent-onecent-api:latest}
BACKUP_FILE=${BACKUP_FILE:-}

# Read-only: env file is mounted, never printed, and no Compose service starts.
if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
  "$DOCKER" run --rm --user "$(id -u):$(id -g)" --network none --read-only \
    -v "$(pwd)/$ENV_FILE:/run/onecent-preflight.env:ro" \
    -v "$BACKUP_FILE:/run/onecent-backup.dump:ro" \
    -e MAINNET_BACKUP_PATH=/run/onecent-backup.dump \
    "$IMAGE" python -m onecent.preflight --env-file /run/onecent-preflight.env
else
  "$DOCKER" run --rm --user "$(id -u):$(id -g)" --network none --read-only \
    -v "$(pwd)/$ENV_FILE:/run/onecent-preflight.env:ro" \
    "$IMAGE" python -m onecent.preflight --env-file /run/onecent-preflight.env
fi
