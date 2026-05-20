#!/bin/sh
cid=$(docker ps --filter name=senaite_app --format "{{.ID}}")

echo "=== sys.path src entries ==="
docker exec $cid python -c '
import sys
for p in sys.path:
    if "src" in p:
        print(p)
'

echo "=== Check import ==="
docker exec $cid python -c '
from senaite import hgumba
print("OK: " + hgumba.__file__)
'

echo "=== ZCML test ==="
docker exec $cid python -c '
from zope.configuration import xmlconfig
import senaite.hgumba
xmlconfig.file("configure.zcml", senaite.hgumba)
print("ZCML loaded OK")
' 2>&1 | head -10

echo "=== Check archetypes import ==="
docker exec $cid python -c '
import archetypes.schemaextender
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.extender import BaseSchemaExtender
print("schemaextender OK")
'
