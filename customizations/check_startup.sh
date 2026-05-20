#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
echo "CID=$cid"
docker logs $cid 2>&1 | grep -E "Ready|ERROR|Traceback" | tail -10
echo "=== Health ==="
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8083/ 2>&1
