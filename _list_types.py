import urllib2, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'
r = urllib2.Request(base + '/portal_types/manage_main')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()
for m in re.findall(r'typeinfo/([A-Za-z]+)', html):
    print(m)
