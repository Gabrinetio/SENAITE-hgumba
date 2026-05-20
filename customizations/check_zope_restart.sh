#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check Zope PID ==="
docker exec $cid ps aux | grep serve.py | grep -v grep

echo "=== Check if package-includes exists ==="
docker exec $cid ls -la /home/senaite/senaitelims/parts/instance/etc/package-includes/ 2>&1

echo "=== Check ZCML include ==="
docker exec $cid cat /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml 2>&1

echo "=== Try docker restart ==="
docker restart $cid 2>&1

echo "=== Wait 5s ==="
sleep 5

echo "=== Check status ==="
docker ps --filter name=senaite_app --format "table {{.ID}}\t{{.Status}}\t{{.Names}}" 2>&1 | cat
