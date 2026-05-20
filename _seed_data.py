"""Seed test data into SENAITE via Zope instance run."""
import transaction

site = app.senaite

def ensure_client():
    clients = site.clients
    existing = getattr(clients, 'hgu', None)
    if existing:
        print('Client HGU already exists')
        return existing
    clients.invokeFactory('Client', 'hgu', title='HGU - Hospital Gumarba', ClientID='HGU')
    client = clients['hgu']
    client.reindexObject()
    transaction.commit()
    print('Client HGU created')
    return client

def ensure_services():
    bs = site.bika_setup
    svc_container = bs.bika_analysisservices
    created = []
    specs = [
        ('glicose', 'Glicose', 'GLI001', 'mg/dL'),
        ('hemograma', 'Hemograma', 'HEM001', 'milhoes/mm3'),
        ('lipidograma', 'Lipidograma', 'LIP001', 'mg/dL'),
    ]
    for sid, title, keyword, unit in specs:
        existing = getattr(svc_container, sid, None)
        if existing:
            print('Service %s already exists' % sid)
            created.append(existing)
            continue
        svc_container.invokeFactory('AnalysisService', sid, title=title, Keyword=keyword, Unit=unit)
        svc = svc_container[sid]
        svc.reindexObject()
        transaction.commit()
        print('Service %s created' % sid)
        created.append(svc)
    return created

def ensure_contact(client):
    existing = getattr(client, 'contact-1', None)
    if existing:
        print('Contact contact-1 already exists')
        return existing
        client.invokeFactory('Contact', 'contact-1', title='Dr Teste', Firstname='Teste', Lastname='User')
    contact = client['contact-1']
    contact.reindexObject()
    transaction.commit()
    print('Contact created')
    return contact

def create_ars(client, contact, services):
    svc_map = {s.id: s for s in services}
    specs = [
        ('ar-001', 'GLI001', 'MRN-001', 'Paciente Teste A'),
        ('ar-002', 'HEM001', 'MRN-002', 'Paciente Teste B'),
    ]
    for ar_id, svc_keyword, mrn, fullname in specs:
        existing = getattr(client, ar_id, None)
        if existing:
            print('AR %s already exists' % ar_id)
            continue
        svc = svc_map.get(svc_keyword)
        if not svc:
            print('Service %s not found, skipping %s' % (svc_keyword, ar_id))
            continue
        try:
            client.invokeFactory('AnalysisRequest', ar_id, title=svc_keyword, Analyses=[svc.UID()], Contact=contact.UID())
            ar = client[ar_id]
            if hasattr(ar, 'getField'):
                mrn_field = ar.getField('MedicalRecordNumber')
                if mrn_field:
                    mrn_field.set(ar, {'value': mrn, 'temporary': False})
                name_field = ar.getField('PatientFullName')
                if name_field:
                    parts = fullname.split(None, 2)
                    name_data = {'firstname': parts[0]}
                    if len(parts) > 2:
                        name_data['middlename'] = parts[1]
                        name_data['lastname'] = parts[2]
                    elif len(parts) > 1:
                        name_data['lastname'] = parts[1]
                    name_field.set(ar, name_data)
            ar.reindexObject()
            transaction.commit()
            print('AR %s created with %s' % (ar_id, fullname))
        except Exception as e:
            print('Error creating AR %s: %s' % (ar_id, str(e)))
            transaction.abort()

client = ensure_client()
services = ensure_services()
contact = ensure_contact(client)
create_ars(client, contact, services)
print('Seed complete.')
