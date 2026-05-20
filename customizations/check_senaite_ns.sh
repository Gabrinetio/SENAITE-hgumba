#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check senaite.core structure ==="
docker exec $cid find /home/senaite/senaitelims/src/senaite.core/senaite -maxdepth 1 -type f | sort

echo "=== senaite __init__ ==="
docker exec $cid cat /home/senaite/senaitelims/src/senaite.core/senaite/__init__.py

echo "=== How senaite is imported ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 debug 2>/dev/null << EOF
import senaite
print("senaite location: " + senaite.__file__)
print("senaite path: " + str(senaite.__path__))
EOF'
