"""Extract form fields from senaite-addsite page."""
import urllib2, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080'

r = urllib2.Request(base + '/@@senaite-addsite')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

# Extract all input fields
inputs = re.findall(r'<input[^>]*>', html)
for inp in inputs:
    name = re.search(r'name="([^"]*)"', inp)
    value = re.search(r'value="([^"]*)"', inp)
    n = name.group(1) if name else '(no name)'
    v = value.group(1) if value else '(no value)'
    tp = re.search(r'type="([^"]*)"', inp)
    t = tp.group(1) if tp else 'text'
    print("%s = %s [%s]" % (n, v, t))
