#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
SRC=/home/senaite/senaitelims/src/senaite.hgumba

echo "=== Create new structure ==="
docker exec $cid mkdir -p $SRC/src/senaite/hgumba/browser/views
docker exec $cid mkdir -p $SRC/src/senaite/hgumba/extensions
docker exec $cid mkdir -p $SRC/src/senaite/hgumba/profiles/default

echo "=== Move files ==="
docker exec $cid mv $SRC/senaite/hgumba/__init__.py $SRC/src/senaite/hgumba/__init__.py
docker exec $cid mv $SRC/senaite/hgumba/configure.zcml $SRC/src/senaite/hgumba/configure.zcml
docker exec $cid mv $SRC/senaite/hgumba/browser/__init__.py $SRC/src/senaite/hgumba/browser/__init__.py
docker exec $cid mv $SRC/senaite/hgumba/browser/configure.zcml $SRC/src/senaite/hgumba/browser/configure.zcml
docker exec $cid mv $SRC/senaite/hgumba/browser/views/__init__.py $SRC/src/senaite/hgumba/browser/views/__init__.py
docker exec $cid mv $SRC/senaite/hgumba/browser/views/cdm_view.py $SRC/src/senaite/hgumba/browser/views/cdm_view.py
docker exec $cid mv $SRC/senaite/hgumba/browser/views/report_view.py $SRC/src/senaite/hgumba/browser/views/report_view.py
docker exec $cid mv $SRC/senaite/hgumba/extensions/__init__.py $SRC/src/senaite/hgumba/extensions/__init__.py
docker exec $cid mv $SRC/senaite/hgumba/extensions/configure.zcml $SRC/src/senaite/hgumba/extensions/configure.zcml
docker exec $cid mv $SRC/senaite/hgumba/extensions/schema.py $SRC/src/senaite/hgumba/extensions/schema.py
docker exec $cid mv $SRC/senaite/hgumba/profiles/default/metadata.xml $SRC/src/senaite/hgumba/profiles/default/metadata.xml

echo "=== Remove old structure ==="
docker exec $cid rm -rf $SRC/senaite

echo "=== Create namespace __init__ ==="
docker exec $cid sh -c "cat > $SRC/src/senaite/__init__.py << 'NS'
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
NS"

echo "=== Install as dev egg ==="
docker exec $cid pip install -e $SRC 2>&1

echo "=== Verify import ==="
docker exec $cid python -c 'from senaite import hgumba; print("OK: " + hgumba.__file__)'
