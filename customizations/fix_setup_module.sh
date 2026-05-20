#!/bin/sh
set -e
SRC=/opt/senaite/addons/src/senaite/hgumba/extensions

cat > $SRC/setup.py << 'EOF'
def handle_post_install(context):
    """Post-install handler for GenericSetup profile."""
    pass
EOF

echo "Created extensions/setup.py"
ls -la $SRC/
