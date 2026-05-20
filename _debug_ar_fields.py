"""Debug AR fields by making an HTTP request to the API and showing JSON result."""
import urllib2, base64, json
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# Direct HTTP request to traverse the AR and see its dict-like contents
r = urllib2.Request(base + '/clients/hgu/ar-001/manage_main')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

# Parse the ZMI table to find sub-objects
import re
print("=== Sub-objects of ar-001 ===")
for m in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html):
    href = m[0].strip()
    name = m[1].strip()
    if '../' not in href:
        print("  %s -> %s" % (name, href))
