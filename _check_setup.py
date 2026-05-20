import urllib2, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# Check bika_setup ZMI
r = urllib2.Request(base + '/bika_setup/manage_main')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

# Extract object IDs from ZMI folder listing
ids = set()
for m in re.finditer(r'manage_main\?id=([a-zA-Z_]+)', html):
    ids.add(m.group(1))
print('bika_setup folders:', sorted(ids))

# Also check what's directly in AnalysisRequest type
r2 = urllib2.Request(base + '/portal_types/AnalysisRequest/manage_propertiesForm')
r2.add_header('Authorization', 'Basic %s' % auth)
html2 = urllib2.urlopen(r2).read()
schema_fields = re.findall(r'name="([a-zA-Z_]+):', html2)
print('AR schema fields sample:', sorted(set(schema_fields))[:20])
