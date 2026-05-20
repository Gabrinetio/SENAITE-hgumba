#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
echo "=== Install reportlab ==="
docker exec $cid pip install reportlab 2>&1 | tail -5
echo "=== Install matplotlib ==="
docker exec $cid pip install matplotlib 2>&1 | tail -5
echo "=== Install pillow ==="
docker exec $cid pip install pillow 2>&1 | tail -5
echo "=== Verify all ==="
docker exec $cid python -c "import archetypes.schemaextender; print('OK: schemaextender')" 2>&1
docker exec $cid python -c "import reportlab; print('OK: reportlab')" 2>&1
docker exec $cid python -c "import matplotlib; print('OK: matplotlib')" 2>&1
docker exec $cid python -c "from PIL import Image; print('OK: pillow')" 2>&1
