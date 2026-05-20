"""Create SENAITE site programmatically."""
import urllib2, urllib, base64
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))

# Get authenticator and submit site creation form
base = 'http://127.0.0.1:8080'
r = urllib2.Request(base + '/@@senaite-addsite')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

import re
m = re.search(r'name="_authenticator"[^>]*value="([^"]+)"', html)
token = m.group(1) if m else ''

# Submit form with all required fields
data = urllib.urlencode({
    'site_id': 'senaite',
    'title': 'SENAITE',
    'password': os.environ.get('SENAITE_PASSWORD', 'admin'),
    'form.submitted:boolean': 'True',
    'extension_ids:list': 'senaite.lims:default',
    'setup_content:boolean': 'true',
    '_authenticator': token,
})
r2 = urllib2.Request(base + '/@@senaite-addsite', data)
r2.add_header('Authorization', 'Basic %s' % auth)
try:
    resp = urllib2.urlopen(r2)
    print('Response:', resp.getcode(), resp.url)
    print('Body:', resp.read()[:200])
except urllib2.HTTPError as e:
    print('HTTP %d:' % e.code)
    print(e.read()[:500])
