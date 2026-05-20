#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Add src to sys.path via .pth file ==="
docker exec $cid sh -c 'echo "/home/senaite/senaitelims/src/senaite.hgumba" > /usr/local/lib/python2.7/site-packages/senaite-hgumba.pth'

echo "=== Verify import now ==="
docker exec $cid python -c 'from senaite import hgumba; print("OK: " + hgumba.__file__)'

echo "=== Register ZCML via site.zcml override ==="
docker exec $cid sh -c 'mkdir -p /home/senaite/senaitelims/parts/instance/etc/package-includes'
docker exec $cid sh -c 'cat > /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml << ZEOF
<include package="senaite.hgumba" />
ZEOF'

echo "=== site.zcml includes ==="
docker exec $cid grep -n "include" /home/senaite/senaitelims/parts/instance/etc/site.zcml

echo "=== Done - Restart Zope needed ==="
echo "PID to kill:"
docker exec $cid ps aux | grep Zope | grep -v grep | awk '{print $2}'
