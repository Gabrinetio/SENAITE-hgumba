"""List available API endpoints on the AR."""
import urllib2, base64, json
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# Try different API patterns
paths = [
    '/@@API/', '/@@API/senaite/v1/', '/@@API/senaite/v1/help',
    '/clients/hgu/ar-001/@@API/', '/clients/hgu/ar-001/',
]
for p in paths:
    r = urllib2.Request(base + p)
    r.add_header('Authorization', 'Basic %s' % auth)
    r.add_header('Accept', 'text/html,application/json,*/*')
    try:
        resp = urllib2.urlopen(r)
        data = resp.read()
        ct = resp.headers.get('Content-Type', '')
        print("%s -> %d (%s) %s..." % (p, resp.getcode(), ct, data[:200].replace('\n', ' ')))
    except urllib2.HTTPError as e:
        print("%s -> %d %s..." % (p, e.code, e.read()[:100].replace('\n', ' ')))
