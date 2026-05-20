"""Check what methods work on the AR via internal HTTP."""
import urllib2, base64, json
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# AR view page - will render AR's own view template
r = urllib2.Request(base + '/clients/hgu/ar-001/view')
r.add_header('Authorization', 'Basic %s' % auth)
try:
    html = urllib2.urlopen(r).read()
    print("VIEW page length:", len(html))
    # Find patient-related section
    import re
    for m in re.findall(r'(?:Patient|patient|Paciente|MRN|mrn)[^<]{0,200}', html):
        print("  ->", m.strip())
except urllib2.HTTPError as e:
    print("VIEW HTTP %d: %s" % (e.code, e.read()[:200]))
