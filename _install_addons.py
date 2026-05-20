"""Install senaite.hgumba and senaite.patient addons."""
import urllib2, urllib, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def post_form(url, data):
    r = urllib2.Request(url, urllib.urlencode(data))
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        resp = urllib2.urlopen(r)
        return resp.getcode(), resp.url
    except urllib2.HTTPError as e:
        return e.code, e.read()[:200]

# Get authenticator
r = urllib2.Request(base + '/@@prefs_install_products_form')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()
m = re.search(r'name="_authenticator"[^>]*value="([^"]+)"', html)
token = m.group(1) if m else ''

# Install senaite.hgumba
print("=== Installing senaite.hgumba ===")
code, body = post_form(base + '/install_products', {
    'install_product': 'senaite.hgumba',
    'form.submitted': 'Install',
    '_authenticator': token,
})
print("hgumba:", code)

# Install senaite.patient
print("=== Installing senaite.patient ===")
code, body = post_form(base + '/install_products', {
    'install_product': 'senaite.patient',
    'form.submitted': 'Install',
    '_authenticator': token,
})
print("patient:", code)

# Verify addon views are registered
print("\n=== Testing addon views ===")
for view in ['hgumba-seed', 'cdm-pdf']:
    r = urllib2.Request(base + '/clients/@@%s' % view)
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        resp = urllib2.urlopen(r)
        print("%s -> %d" % (view, resp.getcode()))
    except urllib2.HTTPError as e:
        print("%s -> #d %s" % (view, e.code, e.read()[:80]))
