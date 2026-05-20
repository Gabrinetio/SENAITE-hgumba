import urllib2, urllib, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def get_form(url):
    r = urllib2.Request(url)
    r.add_header('Authorization', 'Basic %s' % auth)
    return urllib2.urlopen(r).read()

def post_form(url, data):
    r = urllib2.Request(url, urllib.urlencode(data))
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        resp = urllib2.urlopen(r)
        return resp.getcode(), resp.read()[:300]
    except urllib2.HTTPError as e:
        return e.code, e.read()[:300]

# 1. Install senaite.patient
print("=== Installing senaite.patient ===")
html = get_form(base + '/@@prefs_install_products_form')
m = re.search(r'name="_authenticator"[^>]*value="([^"]+)"', html)
if m:
    token = m.group(1)
    code, body = post_form(base + '/install_products', {
        'install_product': 'senaite.patient',
        'form.submitted': 'Install',
        '_authenticator': token
    })
    print("Install:", code, body[:200])
else:
    print("No authenticator")

# 2. Verify Patient FTI now exists
print("\n=== Checking Patient FTI ===")
html2 = get_form(base + '/portal_types/Patient/manage_propertiesForm')
if 'title' in html2:
    print("Patient FTI: EXISTS")
else:
    print("Patient FTI: NOT FOUND")
