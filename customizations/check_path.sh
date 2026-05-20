#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Full sys.path ==="
docker exec $cid python -c '
import sys
for p in sys.path:
    print(p)
'

echo "=== Check if senaite.core is importable ==="
docker exec $cid python -c '
from senaite import core
print("senaite.core: " + core.__file__)
'
