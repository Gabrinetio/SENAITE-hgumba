#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Fix .pth file (add newline) ==="
docker exec $cid sh -c 'printf "/home/senaite/senaitelims/src/senaite.hgumba\n" > /usr/local/lib/python2.7/site-packages/senaite-hgumba.pth'

echo "=== Verify import after fix ==="
docker exec $cid python -c 'from senaite import hgumba; print("OK: " + hgumba.__file__)' 2>&1

echo "=== Restart Zope process ==="
docker exec $cid sh -c 'kill -HUP 1 2>/dev/null; echo "Sent HUP to PID 1"'

echo "=== Wait for restart ==="
sleep 5

echo "=== Check Zope process ==="
docker exec $cid ps aux | grep -i zope | grep -v grep | head -3

echo "=== Done ==="
