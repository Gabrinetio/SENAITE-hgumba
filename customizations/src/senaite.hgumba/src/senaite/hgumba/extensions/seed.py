import transaction
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import setSite
from zope.component import getUtility
from plone.dexterity.utils import createContentInContainer
from plone import api

site = app.senaite
setSite(site)
logger = logging.getLogger('seed')

# Get the client
clients = site.clients
hgu = clients['hgu']

# 1. Create Patient
logger.info("Creating Patient...")
patient = api.content.create(
    container=hgu,
    type='Patient',
    id='patient-p001',
    title='Paciente Teste',
    PatientID='P-001',
)
logger.info("Patient created: %s", patient.absolute_url())

# 2. Get UIDs for references
contact_uid = hgu['contact-1'].UID()
patient_uid = patient.UID()

# 3. Get AnalysisService UIDs
services = site.bika_setup.bika_analysisservices
svc_uids = [services['hemograma'].UID()]

# 4. Create AnalysisRequest via API content creation
logger.info("Creating AnalysisRequest...")
ar = api.content.create(
    container=hgu,
    type='AnalysisRequest',
    id='ar-001',
    title='HMG-001',
    Analyses=['hemograma'],
    Contact=contact_uid,
    Patient=patient_uid,
)
logger.info("AR created: %s", ar.absolute_url())

# Create second AR
ar2 = api.content.create(
    container=hgu,
    type='AnalysisRequest',
    id='ar-002',
    title='HMG-002',
    Analyses=['hemograma'],
    Contact=contact_uid,
    Patient=patient_uid,
)
logger.info("AR2 created: %s", ar2.absolute_url())

transaction.commit()
logger.info("=== SEED COMPLETE ===")
print("Patient:", patient.absolute_url())
print("AR1:", ar.absolute_url())
print("AR2:", ar2.absolute_url())
