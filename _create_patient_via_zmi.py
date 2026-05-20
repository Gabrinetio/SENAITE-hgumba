import urllib2, urllib, base64, json, re, httplib, cookielib, os
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

# Use cookiejar for session
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('Authorization', 'Basic %s' % auth)]

def get(url):
    return opener.open(urllib2.Request(base + url)).read()

def post(url, data):
    return opener.open(urllib2.Request(base + url, urllib.urlencode(data))).read()

# 1. Create Patient via portal_factory
print("=== portal_factory: Patient ===")
# First get the authenticator token
html = get('/clients/hgu/manage_main')
m = re.search(r'name="_authenticator"[^>]*value="([^"]+)"', html)
token = m.group(1) if m else ''

# Try portal_factory approach
# Step 1: create via portal_factory
pf = post('/clients/hgu/portal_factory/Patient/patient-p001', {
    'title': 'Paciente Teste',
    'PatientID': 'P-001',
    '_authenticator': token,
})
print('portal_factory:', '302' if '302' in str(dir()) else pf[:100])

# Step 2: Maybe redirect follows... check what was created
r = get('/clients/hgu/patient-p001/manage_main')
if 'title' in r:
    print('Patient created!')
else:
    print('Patient not found:', r[:100])

# List what's in hgu
html = get('/clients/hgu/manage_main')
contents = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)
for href, name in contents:
    if name.strip() and not href.startswith('http'):
        print('  %s: %s' % (name.strip(), href))
