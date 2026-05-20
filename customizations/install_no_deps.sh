#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
SRC=/home/senaite/senaitelims/src/senaite.hgumba

echo "=== Install dev egg (no-deps) ==="
docker exec $cid pip install -e $SRC --no-deps 2>&1

echo "=== Verify import ==="
docker exec $cid python -c 'from senaite import hgumba; print("OK: " + hgumba.__file__)'

echo "=== Check structure ==="
docker exec $cid find $SRC -type f | sort

echo "=== Done ==="
