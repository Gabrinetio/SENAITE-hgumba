app = locals().get("app")
import os
print("PID:", os.getpid())
print("APP type:", type(app).__name__)
print("APP dir:", dir(app)[:20])
print("APP objectIds:", app.objectIds())
# Check if senaite is accessible via traverse
from zope.traversing import api as traversing
try:
    site = app.unrestrictedTraverse("senaite")
    print("Found via traverse: senaite =", type(site).__name__)
except Exception as e:
    print("Cannot traverse to senaite:", e)
# Check storage
from Zope2.App import startup
print("Startup databases:", getattr(startup, 'dbtab', None))
# Check actual file path
from ZODB.FileStorage import FileStorage
db = app._getDB()
storage = db._storage
if hasattr(storage, '_file_name'):
    print("Data.fs:", storage._file_name)
