#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
echo "=== archetypes.schemaextender ==="
docker exec $cid python -c "import archetypes.schemaextender; print('OK')" 2>&1
echo "=== reportlab ==="
docker exec $cid python -c "import reportlab; print('OK')" 2>&1
echo "=== matplotlib ==="
docker exec $cid python -c "import matplotlib; print('OK')" 2>&1
echo "=== PIL ==="
docker exec $cid python -c "from PIL import Image; print('OK')" 2>&1
echo "=== buildout.cfg (head) ==="
docker exec $cid head -50 /home/senaite/senaitelims/buildout.cfg 2>&1
echo "=== etc/zope.conf ==="
docker exec $cid ls /home/senaite/senaitelims/parts/instance/etc/ 2>&1
