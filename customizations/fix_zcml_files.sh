#!/bin/sh
set -e
SRC=/opt/senaite/addons/src/senaite/hgumba

# Create missing browser interfaces.py for the ZCML layer reference
cat > $SRC/browser/interfaces.py << 'EOF'
from zope.interface import Interface

class ISenaiteHgumbaLayer(Interface):
    """Browser layer for senaite.hgumba"""
EOF

# Create views/configure.zcml (needed because browser/configure.zcml includes .views)
cat > $SRC/browser/views/configure.zcml << 'ZEOF'
<configure xmlns="http://namespaces.zope.org/zope" />
ZEOF

# Create minimal cdm_report.pt template
cat > $SRC/browser/views/cdm_report.pt << 'PTEOF'
<html xmlns:tal="http://xml.zope.org/namespaces/tal">
<head><title>CDM Report</title></head>
<body tal:content="structure view/render_pdf" />
</html>
PTEOF

# Create hgumba_report.pt template
cat > $SRC/browser/views/hgumba_report.pt << 'PTEOF'
<html xmlns:tal="http://xml.zope.org/namespaces/tal">
<head>
  <title>HGUMBA Report</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    img { max-width: 100%; height: auto; }
  </style>
</head>
<body>
  <h1>Histórico de Resultados</h1>
  <div tal:content="structure view/get_results_chart" />
</body>
</html>
PTEOF

echo "=== Files created ==="
find $SRC/browser -type f | sort

# Remove old structure without src/ prefix if exists
rm -rf /opt/senaite/addons/senaite 2>/dev/null

echo "=== Cleanup done ==="
