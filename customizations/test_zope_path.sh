#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check import via instance interpreter ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 debug 2>/dev/null << EOF
from senaite import hgumba
print("OK: " + hgumba.__file__)
import senaite.hgumba.configure
print("ZCML available")
EOF'
