import urllib2, base64, json, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def api_get(path):
    r = urllib2.Request(base + path)
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        return json.loads(urllib2.urlopen(r).read())
    except:
        return str(urllib2.urlopen(r).read()[:2000])

# Check what types are in the portal_types tool
data = api_get('/portal_types/manage_propertiesForm')
types = set(re.findall(r'value="([A-Z][a-zA-Z]+)"', str(data)))
print("Portal types:", sorted(types))
print("---")

# Check bika_setup contents
r = urllib2.Request(base + '/bika_setup/manage_main')
r.add_header('Authorization', 'Basic %s' % auth)
contents = urllib2.urlopen(r).read()
folders = re.findall(r'href="([^"]+)"[^>]*>([^<]+)<', contents)
for url, name in folders:
    if 'manage' not in url:
        print("  %s -> %s" % (name.strip(), url))
