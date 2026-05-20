#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Install archetypes.schemaextender (no-deps) ==="
docker exec $cid pip install --no-deps archetypes.schemaextender 2>&1

echo "=== Verify ==="
docker exec $cid python -c "import archetypes.schemaextender; print('OK: ' + archetypes.schemaextender.__file__)" 2>&1
docker exec $cid python -c "import reportlab; print('OK: reportlab')" 2>&1
docker exec $cid python -c "import matplotlib; print('OK: matplotlib')" 2>&1
