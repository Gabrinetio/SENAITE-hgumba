"""Create client, services, contacts for testing."""
import urllib2, urllib, base64, json, os
auth = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))
base = 'http://127.0.0.1:8080/senaite'

def api_create(**params):
    qs = urllib.urlencode(params)
    r = urllib2.Request(base + '/@@API/create?' + qs)
    r.add_header('Authorization', 'Basic %s' % auth)
    try:
        resp = urllib2.urlopen(r)
        d = json.loads(resp.read())
        print("  %s: %s" % (params.get('title', params.get('id', '?')), d.get('success', d)))
        return d
    except urllib2.HTTPError as e:
        body = e.read()[:200]
        print("  %s: HTTP %d %s" % (params.get('title', params.get('id', '?')), e.code, body))
        return None

# 1. Create Analysis Services
print("=== Services ===")
api_create(obj_type='AnalysisService', obj_path='/bika_setup/bika_analysisservices', id='hemograma', title='Hemograma')
api_create(obj_type='AnalysisService', obj_path='/bika_setup/bika_analysisservices', id='urocultura', title='Urocultura')
api_create(obj_type='AnalysisService', obj_path='/bika_setup/bika_analysisservices', id='glicemia', title='Glicemia')

# 2. Create Client
print("\n=== Client ===")
api_create(obj_type='Client', obj_path='/clients', id='hgu', title='Hospital Geral de Umba')

# 3. Create Contact
print("\n=== Contacts ===")
api_create(obj_type='Contact', obj_path='/clients/hgu', title='Dr Exemplo Um')
api_create(obj_type='Contact', obj_path='/clients/hgu', title='Dr Exemplo Dois')
