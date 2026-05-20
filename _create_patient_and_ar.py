import urllib2, urllib, base64, json, re
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def api_create(**params):
    qs = urllib.urlencode(params)
    r = urllib2.Request(base + '/@@API/create?' + qs)
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        resp = urllib2.urlopen(r)
        return json.loads(resp.read())
    except urllib2.HTTPError as e:
        return {'error': e.code, 'body': e.read()[:300]}

# 1. Create Patient
print("=== Creating Patient ===")
r = api_create(obj_type='Patient', obj_path='/clients/hgu',
               title='Paciente Teste', PatientID='P-001')
print('Patient:', r.get('success'), r.get('obj_id', r.get('error', '')))

# 2. Create ARs
# First get the doctor and patient UIDs
import re
def get_uid(path):
    r = urllib2.Request(base + path + '/manage_main')
    r.add_header('Authorization', 'Basic %s' % auth)
    html = urllib2.urlopen(r).read()
    m = re.search(r'uid=([a-f0-9]{32})', html)
    return m.group(1) if m else None

print("\n=== Creating Analysis Requests ===")
# Get UIDs for references
for attempt in range(3):
    r = api_create(
        obj_type='AnalysisRequest',
        Client='portal_type:Client|id:hgu',
        Contact='portal_type:Contact|title:Dr Exemplo Um',
        Patient='portal_type:Patient|title:Paciente Teste',
        Services='portal_type:AnalysisService|id:hemograma',
    )
    print('AR attempt %d:' % attempt, json.dumps(r)[:200])

print("\n=== DONE ===")
