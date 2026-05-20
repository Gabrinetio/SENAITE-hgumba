"""Direct Python introspection of AnalysisRequest through HTTP._
Traverse the site and show AR properties."""
import urllib2, base64, json, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# Get the AR properties page from ZMI
r = urllib2.Request(base + '/clients/hgu/ar-001/manage_propertiesForm')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

print("=== Properties of ar-001 ===")
for m in re.findall(r'<tr[^>]*>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>\s*<input[^>]*value="([^"]*)"', html):
    print("  %s = %s" % (m[0].strip(), m[1].strip()))
