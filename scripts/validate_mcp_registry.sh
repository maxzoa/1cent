#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
schema_url=https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
curl -fsS "$schema_url" -o "$tmp_dir/server.schema.json"
chmod 755 "$tmp_dir"
chmod 644 "$tmp_dir/server.schema.json"
DOCKER=${DOCKER:-/usr/local/bin/docker}
if python -c 'import jsonschema' >/dev/null 2>&1; then
  PYTHON='python'
  schema_path="$tmp_dir/server.schema.json"
else
  test -x "$DOCKER" || DOCKER=docker
  PYTHON="$DOCKER run --rm -v $PWD:/work:ro -v $tmp_dir:/schema:ro -w /work 1cent-onecent-api:latest python"
  schema_path=/schema/server.schema.json
fi
$PYTHON -c 'import json,jsonschema,sys; schema=json.load(open(sys.argv[1],encoding="utf-8")); document=json.load(open("server.json",encoding="utf-8")); jsonschema.validate(document,schema); print("server.json schema=PASS")' "$schema_path"
$PYTHON -c 'import json; d=json.load(open("server.json",encoding="utf-8")); assert d["name"]=="ru.maxzoa/1cent"; assert d["version"]=="0.6.0"; assert d["remotes"]==[{"type":"streamable-http","url":"https://1cent.maxzoa.ru/mcp"}]; print("remote metadata=PASS; version=0.6.0")'
