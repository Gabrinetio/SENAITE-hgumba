#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Find senaite.core on filesystem ==="
docker exec $cid find /home/senaite -name "core" -path "*/senaite/*" -type d 2>/dev/null | head -5

echo "=== senaite.egg-info ==="
docker exec $cid find /home/senaite -name "senaite*.egg-info" -type d 2>/dev/null | head -10

echo "=== Python importable paths from instance ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 debug 2>/dev/null << EOF
import sys
for p in sys.path:
    print(p)
EOF'
