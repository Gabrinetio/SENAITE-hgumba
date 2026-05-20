"""Explore AR via direct SENAITE API calls."""
import urllib2, base64, json
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def api_get(path):
    r = urllib2.Request(base + path)
    r.add_header('Authorization', 'Basic %s' % auth)
    r.add_header('Accept', 'application/json')
    try:
        return json.loads(urllib2.urlopen(r).read())
    except urllib2.HTTPError as e:
        return {"error": e.code, "body": e.read()[:300]}

# Try senaite's v1 JSON API
print("=== API v1 on AR ===")
r = api_get('/@@API/senaite/v1/')
print(json.dumps(r, indent=2)[:1000])

print("\n=== API v1 get on clients ===")
r = api_get('/clients/@@API/senaite/v1/get')
print(json.dumps(r, indent=2)[:1000])

print("\n=== API v1 get on ar-001 ===")
r = api_get('/clients/hgu/ar-001/@@API/senaite/v1/get')
print(json.dumps(r, indent=2)[:1000])
