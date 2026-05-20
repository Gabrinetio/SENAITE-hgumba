"""Populate SENAITE test data via HTTP JSON API"""
import os, base64
import json
import urllib
import urllib2
import urlparse

BASE = "http://127.0.0.1:8080/senaite/@@API"
AUTH = base64.b64encode(os.environ.get(b"SENAITE_AUTH", b"admin:admin"))

def api_create(**params):
    """GET to @@API/create with query params"""
    qs = urllib.urlencode(params)
    url = BASE.replace("/@@API", "/@@API/create") + "?" + qs
    r = urllib2.Request(url)
    r.add_header("Authorization", "Basic %s" % AUTH)
    try:
        resp = urllib2.urlopen(r)
        data = json.loads(resp.read())
        if data.get("error"):
            print("    ERROR: %s" % data["error"])
        return data
    except urllib2.HTTPError as e:
        body = e.read()
        print("    HTTP %d: %s" % (e.code, body[:200]))
        return {"error": str(e)}
    except Exception as e:
        print("    EXCEPTION: %s" % str(e))
        return {"error": str(e)}

# 1. Analysis Categories
print("=== Creating Analysis Categories ===")
for cid, ctitle in [
    ("hematologia", "Hematologia"),
    ("bioquimica", "Bioquimica"),
    ("microbiologia", "Microbiologia"),
]:
    r = api_create(obj_type="AnalysisCategory",
                   obj_path="/bika_setup/bika_analysiscategories",
                   title=ctitle, obj_id=cid)
    ok = r.get("success", False) or r.get("obj_id", "")
    print("  %s: %s" % (ctitle, "OK" if ok else r.get("error", r)))

# 2. Analysis Services
print("\n=== Creating Analysis Services ===")
services = [
    ("hemograma", "Hemograma completo", "hematologia", "10^3/mm3", "4.5", "11.0", "12.50", "HEM"),
    ("glicemia", "Glicemia em jejum", "bioquimica", "mg/dL", "70.0", "99.0", "8.90", "GLI"),
    ("urocultura", "Urocultura", "microbiologia", "", "", "", "35.00", "URO"),
    ("creatinina", "Creatinina", "bioquimica", "mg/dL", "0.7", "1.2", "15.00", "CRE"),
    ("hba1c", "Hemoglobina Glicada", "bioquimica", "%", "4.0", "5.6", "45.00", "HBA1C"),
]
for sid, stitle, scat, sunit, smin, smax, sprice, skw in services:
    r = api_create(obj_type="AnalysisService",
                   obj_path="/bika_setup/bika_analysisservices",
                   title=stitle, obj_id=sid,
                   Unit=sunit, Keyword=skw, Price=sprice)
    ok = r.get("success", False) or r.get("obj_id", "")
    print("  %s: %s" % (stitle, "OK" if ok else r.get("error", r)))

# 3. Client
print("\n=== Creating Client ===")
r = api_create(obj_type="Client", obj_path="/clients",
               title="Hospital Geral de Umba", obj_id="hgu")
print("  Client: %s" % ("OK" if r.get("success") else r.get("error", r)))

# 4. Doctors under client
print("\n=== Creating Doctors ===")
r1 = api_create(obj_type="Doctor", obj_path="/clients/hgu",
                title="Dr. Exemplo Um", obj_id="dr-exemplo-1",
                DoctorID="CRM-00001", DoctorType="medico")
print("  Dr. Exemplo Um: %s" % ("OK" if r1.get("success") else r1.get("error", r1)))
r2 = api_create(obj_type="Doctor", obj_path="/clients/hgu",
                title="Dr. Exemplo Dois", obj_id="dr-exemplo-2",
                DoctorID="CRM-00002", DoctorType="medico")
print("  Dr. Exemplo Dois: %s" % ("OK" if r2.get("success") else r2.get("error", r2)))

# 5. Patient under client
print("\n=== Creating Patient ===")
r = api_create(obj_type="Patient", obj_path="/clients/hgu",
               title="Paciente Teste", obj_id="P-001",
               PatientID="P-001")
print("  Patient: %s" % ("OK" if r.get("success") else r.get("error", r)))

print("\n=== DONE ===")
