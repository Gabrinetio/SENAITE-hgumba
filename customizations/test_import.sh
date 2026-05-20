#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== Check .pth file ==="
docker exec $cid cat /usr/local/lib/python2.7/site-packages/senaite-hgumba.pth

echo "=== Test import ==="
docker exec $cid python -c '
import sys
sys.path.insert(0, "/home/senaite/senaitelims/src/senaite.hgumba")
from senaite import hgumba
print("OK: " + hgumba.__file__)
'

echo "=== Instance interpreter ==="
docker exec $cid sh -c 'cd /home/senaite/senaitelims && bin/instance0 debug 2>/dev/null << EOF
import sys
sys.path.insert(0, "/home/senaite/senaitelims/src/senaite.hgumba")
from senaite import hgumba
print("OK via instance: " + hgumba.__file__)
EOF'
