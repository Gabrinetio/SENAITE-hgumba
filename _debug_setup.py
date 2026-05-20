app = locals().get("app")
site = app.senaite
print("site.id:", site.getId())
bs = site.bika_setup
print("bika_setup.id:", bs.getId())
print("bika_setup dir:", [x for x in dir(bs) if not x.startswith('_')][:30])
print("bika_setup objectIds:", bs.objectIds())
