"""Create test data via HTTP simulating Plone form submissions"""
import urllib2, urllib, base64, json, os
AUTH = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
BASE = 'http://127.0.0.1:8080/senaite'

def post_form(url, data):
    r = urllib2.Request(url, urllib.urlencode(data))
    r.add_header('Authorization', 'Basic %s' % AUTH)
    try:
        resp = urllib2.urlopen(r)
        return resp.getcode(), resp.read()[:200]
    except urllib2.HTTPError as e:
        return e.code, e.read()[:200]

# 1. Create Patient
print("=== Creating Patient ===")
code, body = post_form(
    BASE + '/clients/hgu/portal_factory/Patient/P-001',
    {'form.submitted': '1', 'title': 'Paciente Teste', 'PatientID': 'P-001',
     'BirthDate': '1985-03-15'}
)
print("Patient:", code, body)

# 2. Create Doctor (Contact)
print("\n=== Creating Doctors ===")
code, body = post_form(
    BASE + '/clients/hgu/portal_factory/Contact/dr-silva',
    {'form.submitted': '1', 'title': 'Dr. Exemplo Um',
     'DoctorID': 'CRM-12345', 'DoctorType': 'medico'}
)
print("Dr Silva:", code, body)

code, body = post_form(
    BASE + '/clients/hgu/portal_factory/Contact/dr-santos',
    {'form.submitted': '1', 'title': 'Dr. Exemplo Dois',
     'DoctorID': 'CRM-67890', 'DoctorType': 'medico'}
)
print("Dr Santos:", code, body)

# 3. Check what exists
print("\n=== Checking created objects ===")
for path in ['/clients/hgu']:
    r = urllib2.Request(BASE + path + '/manage_main')
    r.add_header('Authorization', 'Basic %s' % AUTH)
    try:
        resp = urllib2.urlopen(r)
        import re
        items = re.findall(r'href="([^"]+)"[^>]*>([^<]+)<', resp.read())
        for url, name in items:
            if url.startswith('/') and 'manage' not in url and 'resource' not in url:
                print("  %s -> %s" % (name.strip(), url))
    except Exception as e:
        print("  Error:", e)
