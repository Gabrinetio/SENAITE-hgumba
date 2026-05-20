#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
SRC=/home/senaite/senaitelims/src/senaite.hgumba

echo "=== Current structure ==="
docker exec $cid find $SRC -type f | sort

echo "=== Create namespace __init__ ==="
docker exec $cid sh -c "cat > $SRC/src/senaite/__init__.py << 'EOF'
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
EOF"

echo "=== Create setup.py ==="
docker exec $cid sh -c "cat > $SRC/setup.py << 'SETUPEOF'
from setuptools import setup, find_packages

version = '1.0.0'

setup(
    name='senaite.hgumba',
    version=version,
    description='Customizacoes Hospital Geral Umba para SENAITE',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['senaite'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'senaite.core',
        'archetypes.schemaextender',
        'reportlab',
        'matplotlib',
        'Pillow',
    ],
    entry_points={},
)
SETUPEOF"

echo "=== Install as dev egg ==="
docker exec $cid pip install -e $SRC 2>&1 | tail -5

echo "=== Verify import ==="
docker exec $cid python -c 'from senaite import hgumba; print("OK: " + hgumba.__file__)' 2>&1

echo "=== Move ZCML include to right place ==="
docker exec $cid sh -c "cat > /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml << 'ZEOF'
<include package=\"senaite.hgumba\" />
ZEOF"
docker exec $cid cat /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml

echo "=== Done ==="
