app = locals().get("app")
site = app.senaite
bs = site.bika_setup
print("bika_setup objectIds:", bs.objectIds())
print("bika_setup contentIds:", bs.contentIds())
# List all children
for oid in bs.objectIds():
    try:
        obj = bs._getOb(oid)
        print("  %s: %s" % (oid, type(obj).__name__))
    except:
        print("  %s: ERROR" % oid)
