#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Package includes ==="
docker exec $cid ls -la /home/senaite/senaitelims/parts/instance/etc/package-includes/ 2>&1

echo "=== ZCML content ==="
docker exec $cid cat /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml 2>&1

echo "=== Logs for hgumba ==="
docker logs $cid 2>&1 | grep -i "hgumba" | head -10

echo "=== Ready check ==="
docker logs $cid 2>&1 | grep "Ready" | tail -3

echo "=== sys.path addons ==="
docker exec $cid python -c 'import sys; print([x for x in sys.path if "addons" in x])'

echo "=== Quick import check ==="
docker exec $cid python -c 'from senaite import hgumba; print("IMPORT OK: " + hgumba.__file__)'
