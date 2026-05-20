#!/bin/sh
set -e
SRC=/opt/senaite/addons/src/senaite/hgumba/browser

echo "=== Move templates to correct location ==="
cp $SRC/views/hgumba_report.pt $SRC/hgumba_report.pt
cp $SRC/views/cdm_report.pt $SRC/cdm_report.pt
echo "Moved templates to browser dir"
ls -la $SRC/*.pt
