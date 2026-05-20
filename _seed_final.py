"""Seed SENAITE test data - runs via instance run"""
import transaction, logging
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

logging.basicConfig(level=logging.INFO)

app = locals().get("app")
site = app.senaite

def make(parent, ptype, id_, **kw):
    if id_ in parent.objectIds():
        logging.info("EXISTS: %s", id_)
        return parent[id_]
    obj = parent[parent.invokeFactory(type_name=ptype, id=id_, title=kw.pop("title", id_))]
    for k, v in kw.items():
        if v is not None:
            mutator = getattr(obj, "set" + k[0].upper() + k[1:], None)
            if mutator:
                mutator(v)
    obj.unmarkCreationFlag()
    from Products.Archetypes.event import ObjectInitializedEvent
    from zope import event
    event.notify(ObjectInitializedEvent(obj))
    obj.reindexObject()
    logging.info("CREATED: %s/%s (%s)", parent.getId(), id_, ptype)
    return obj

# Navigate SENAITE tree
bs = site.bika_setup
logging.info("bika_setup id: %s", bs.getId())
logging.info("bika_setup children: %s", [o for o in bs.objectIds() if 'analysis' in o.lower()])

cat_folder = bs._getOb('bika_analysiscategories')
svc_folder = bs._getOb('bika_analysisservices')

cats = {
    cid: make(cat_folder, "AnalysisCategory", cid, title=ct)
    for cid, ct in [("hematologia","Hematologia"),("bioquimica","Bioquimica"),("microbiologia","Microbiologia")]
}

svcs_data = [
    ("hemograma","Hemograma completo","hematologia","10^3/mm3",4.5,11.0,"12.50","HEM"),
    ("glicemia","Glicemia em jejum","bioquimica","mg/dL",70.0,99.0,"8.90","GLI"),
    ("creatinina","Creatinina","bioquimica","mg/dL",0.7,1.2,"15.00","CRE"),
    ("hba1c","Hemoglobina Glicada","bioquimica","%",4.0,5.6,"45.00","HBA1C"),
    ("urocultura","Urocultura","microbiologia","",None,None,"35.00","URO"),
]
svcs = {}
for sid,st,sc,su,smin,smax,sp,sk in svcs_data:
    s = make(svc_folder, "AnalysisService", sid, title=st,
             Unit=su, Keyword=sk, Price=sp)
    s.setCategory(cats[sc])
    if smin is not None: s.setMinRef(float(smin))
    if smax is not None: s.setMaxRef(float(smax))
    s.setKeyword(sk)
    s.reindexObject()
    svcs[sid] = s

client = make(site.clients, "Client", "hgu", title="Hospital Geral de Umba")
doctor = make(client, "Contact", "dr-exemplo", title="Dr. Exemplo",
              DoctorID="CRM-00000", DoctorType="medico")
patient = make(client, "Patient", "P-001", title="Paciente Exemplo",
               PatientID="P-001", BirthDate=DateTime("1990-01-01"))

# Analysis Request
def create_ar(client, doctor, patient, svc_results, days_ago):
    ts = DateTime() - days_ago
    ar_id = "AR-" + ts.strftime("%Y%m%d-%H%M%S")
    ar = make(client, "AnalysisRequest", ar_id, Patient=patient, Doctor=doctor)
    for svc, result in svc_results:
        an = make(ar, "Analysis", "%s-%s" % (ar_id, svc.getId()),
                  Service=svc, Result=str(result))
        an.setResult(str(result))
        if svc.getMinRef() is not None:
            an.setMinRef(float(svc.getMinRef()))
        if svc.getMaxRef() is not None:
            an.setMaxRef(float(svc.getMaxRef()))
        an.reindexObject()
    wf = getToolByName(site, "portal_workflow")
    wf.doActionFor(ar, "publish")
    ar.reindexObject()
    logging.info("AR created: %s", ar_id)

create_ar(client, doctor, patient, [
    (svcs["hemograma"],6.2),(svcs["glicemia"],85),(svcs["creatinina"],0.9),(svcs["hba1c"],5.1)], 0)
create_ar(client, doctor, patient, [
    (svcs["hemograma"],5.8),(svcs["glicemia"],142),(svcs["creatinina"],0.8)], 30)
create_ar(client, doctor, patient, [
    (svcs["hemograma"],7.1),(svcs["glicemia"],92)], 60)
create_ar(client, doctor, patient, [
    (svcs["hemograma"],3.8),(svcs["glicemia"],78),(svcs["creatinina"],1.1),(svcs["hba1c"],5.5),(svcs["urocultura"],"Negativo")], 90)

transaction.commit()
logging.info("=== SEEDING COMPLETE ===")
