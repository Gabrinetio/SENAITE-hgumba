#!/bin/sh
set -e

echo "=== Update startup wrapper with --no-deps ==="
cat > /opt/senaite/addons/startup.sh << 'EOF'
#!/bin/bash
set -e
echo "=== Installing senaite.hgumba dependencies ==="
pip install --no-deps numpy==1.16.6 Pillow matplotlib==2.2.5 reportlab archetypes.schemaextender cycler kiwisolver 2>&1
echo "=== Chaining to original entrypoint ==="
exec /docker-entrypoint.sh "$@"
EOF
chmod +x /opt/senaite/addons/startup.sh
echo "Wrapper updated"
cat /opt/senaite/addons/startup.sh
