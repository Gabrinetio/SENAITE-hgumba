#!/bin/sh
set -e

echo "=== Create startup wrapper ==="
cat > /opt/senaite/addons/startup.sh << 'EOF'
#!/bin/bash
set -e
echo "=== Installing senaite.hgumba dependencies ==="
pip install --no-deps matplotlib==2.2.5 reportlab Pillow archetypes.schemaextender 2>&1
echo "=== Chaining to original entrypoint ==="
exec /docker-entrypoint.sh "$@"
EOF
chmod +x /opt/senaite/addons/startup.sh

echo "=== Wrapper created ==="
ls -la /opt/senaite/addons/startup.sh

echo "=== Current compose.yaml ==="
cat /tmp/senaite-compose.yaml
