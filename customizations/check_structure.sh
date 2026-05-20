#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check senaite.core src structure ==="
docker exec $cid find /home/senaite/senaitelims/src/senaite.core/src -type f | head -20

echo "=== senaite __init__ in core ==="
docker exec $cid cat /home/senaite/senaitelims/src/senaite.core/src/senaite/__init__.py 2>&1

echo "=== Check egg-info ==="
docker exec $cid cat /home/senaite/senaitelims/src/senaite.core/src/senaite.core.egg-info/PKG-INFO 2>&1 | head -10

echo "=== setup.py ==="
docker exec $cid cat /home/senaite/senaitelims/src/senaite.core/setup.py 2>&1 | head -30

echo "=== Instance path check ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 debug 2>/dev/null << EOFPYTHON
import sys
for p in sys.path:
    if "senaite.hgumba" in p or "senaite.core" in p:
        print(p)
EOFPYTHON'
