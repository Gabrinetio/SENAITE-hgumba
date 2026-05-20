import urllib2, urllib, base64, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

r = urllib2.Request(base + '/@@prefs_install_products_form')
r.add_header('Authorization', 'Basic %s' % auth)
html = urllib2.urlopen(r).read()

# Find install forms
forms = re.findall(r'<form[\s\S]*?</form>', html)
for f in forms:
    if 'senaite.patient' in f:
        m = re.search(r'action="([^"]+)"', f)
        action = m.group(1) if m else '?'
        print("Action:", action)
        inputs = {}
        for name, val in re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', f):
            inputs[name] = val
        for name, val in inputs.items():
            print("  %s = %s" % (name, val))
        
        # Submit the form
        post_url = base.rstrip('/') + '/install_products'
        data = urllib.urlencode(inputs)
        r2 = urllib2.Request(post_url, data)
        r2.add_header('Authorization', 'Basic %s' % auth)
        try:
            resp = urllib2.urlopen(r2)
            print("Submit SUCCESS:", resp.getcode())
        except urllib2.HTTPError as e:
            print("Submit HTTP %d: %s" % (e.code, e.read()[:200]))
        break
else:
    print("No patient form")
    # List all addon names available for install
    for f in forms:
        names = re.findall(r'value="([^"]+)"', f)
        for n in names:
            if n.startswith('senaite.'):
                print("  Addon:", n)
