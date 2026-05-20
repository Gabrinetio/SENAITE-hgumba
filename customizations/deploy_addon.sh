#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")
TMP_SRC=/tmp/senaite.hgumba
DST=/home/senaite/senaitelims/src/senaite.hgumba

echo "=== Create dest dirs in container ==="
docker exec $cid mkdir -p $DST/senaite/hgumba/extensions
docker exec $cid mkdir -p $DST/senaite/hgumba/browser/views
docker exec $cid mkdir -p $DST/senaite/hgumba/profiles/default
docker exec $cid mkdir -p $DST/senaite/hgumba/static

echo "=== Copy files to container ==="
docker cp $TMP_SRC/__init__.py $cid:$DST/senaite/hgumba/__init__.py
docker cp $TMP_SRC/configure.zcml $cid:$DST/senaite/hgumba/configure.zcml
docker cp $TMP_SRC/extensions/__init__.py $cid:$DST/senaite/hgumba/extensions/__init__.py
docker cp $TMP_SRC/extensions/configure.zcml $cid:$DST/senaite/hgumba/extensions/configure.zcml
docker cp $TMP_SRC/extensions/schema.py $cid:$DST/senaite/hgumba/extensions/schema.py
docker cp $TMP_SRC/browser/__init__.py $cid:$DST/senaite/hgumba/browser/__init__.py
docker cp $TMP_SRC/browser/configure.zcml $cid:$DST/senaite/hgumba/browser/configure.zcml
docker cp $TMP_SRC/browser/views/__init__.py $cid:$DST/senaite/hgumba/browser/views/__init__.py
docker cp $TMP_SRC/browser/views/cdm_view.py $cid:$DST/senaite/hgumba/browser/views/cdm_view.py
docker cp $TMP_SRC/browser/views/report_view.py $cid:$DST/senaite/hgumba/browser/views/report_view.py
docker cp $TMP_SRC/profiles/default/metadata.xml $cid:$DST/senaite/hgumba/profiles/default/metadata.xml

echo "=== Files in container ==="
docker exec $cid find $DST -type f | sort

echo "=== site.zcml includes ==="
docker exec $cid grep -n "include" /home/senaite/senaitelims/parts/instance/etc/site.zcml 2>/dev/null | head -20
