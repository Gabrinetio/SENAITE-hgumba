#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check Zope processes ==="
docker exec $cid ps aux | grep -i zope | grep -v grep

echo "=== Check available scripts ==="
docker exec $cid ls -la /home/senaite/senaitelims/bin/ 2>&1 | head -20

echo "=== Try restart ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 restart' 2>&1

echo "=== Wait 5s ==="
sleep 5

echo "=== Check if Zope running ==="
docker exec $cid ps aux | grep -i zope | grep -v grep | head -5

echo "=== Check logs tail ==="
docker exec $cid tail -20 /home/senaite/senaitelims/var/log/instance0.log 2>&1 | head -20
