"""Debug API responses."""
import urllib2, base64, json
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

r = urllib2.Request(base + '/@@API/create?obj_type=AnalysisService&id=test-svc&title=Test')
r.add_header('Authorization', 'Basic %s' % auth)
try:
    resp = urllib2.urlopen(r)
    print(json.dumps(json.loads(resp.read()), indent=2))
except urllib2.HTTPError as e:
    print('HTTP %d:' % e.code)
    print(e.read()[:500])
