import transaction
import logging
logging.basicConfig(level=logging.INFO)

site = app.senaite
portal_types = site.portal_types
print("Dexterity FTIs:", sorted(portal_types.objectIds()))

bs = site.bika_setup
print("Bika setup contents:", sorted(bs.objectIds()))

clients = site.clients
print("Client IDs:", clients.objectIds())
