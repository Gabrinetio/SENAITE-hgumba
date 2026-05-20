print("=== Zope root contents ===")
for oid in app.objectIds():
    obj = app[oid]
    obj_type = getattr(obj, 'meta_type', 'unknown')
    print("  %s (%s)" % (oid, obj_type))
