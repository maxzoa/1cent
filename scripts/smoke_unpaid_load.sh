#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
BASE_URL=${BASE_URL:-http://127.0.0.1:8013}
python scripts/load_unpaid.py --base-url "$BASE_URL" --requests 25 --concurrency 5
