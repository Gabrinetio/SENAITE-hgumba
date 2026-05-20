#!/bin/sh
set -e

echo "=== Check profiles dir ==="
find /opt/senaite/addons/src -name "profiles" -type d
echo "---"
find /opt/senaite/addons/src -name "metadata.xml"

echo "=== Redeploy ==="
docker stack deploy -c /tmp/senaite-compose.yaml senaite --with-registry-auth

echo "=== Status ==="
docker stack services senaite
