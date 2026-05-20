#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check Dockerfile CMD / entrypoint ==="
docker exec $cid cat /docker-entrypoint.sh 2>/dev/null || docker exec $cid cat /entrypoint.sh 2>/dev/null || docker exec $cid cat /app/docker-entrypoint.sh 2>/dev/null || echo "No entrypoint found"

echo "=== Check container config ==="
docker inspect $cid --format '{{.Path}} {{.Args}}' 2>/dev/null

echo "=== Check run.sh ==="
docker exec $cid cat /run.sh 2>/dev/null | head -40 || echo "No run.sh"

echo "=== Restarting container ==="
docker restart $cid

echo "=== Waiting for startup ==="
sleep 10

echo "=== Check if alive ==="
docker ps --filter name=senaite_app --format "{{.ID}} {{.Status}}"

echo "=== Logs ==="
docker logs $cid 2>&1 | tail -30
