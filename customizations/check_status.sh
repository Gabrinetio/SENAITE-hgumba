#!/bin/sh
set -e

echo "=== Stack services ==="
docker stack services senaite 2>&1

echo "=== Stack tasks ==="
docker stack ps senaite 2>&1 | head -10

cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
echo "CID=$cid"

if [ -n "$cid" ]; then
  echo "=== Logs tail ==="
  docker logs $cid 2>&1 | tail -40
else
  echo "No running container found"
fi
