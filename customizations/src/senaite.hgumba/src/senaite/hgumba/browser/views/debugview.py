from Products.Five.browser import BrowserView
import json


class DebugView(BrowserView):
    def __call__(self):
        ctx = self.context
        info = {
            "meta_type": getattr(ctx, 'meta_type', ''),
            "portal_type": getattr(ctx, 'portal_type', ''),
            "type_name": type(ctx).__name__,
            "id": ctx.getId(),
        }
        # Schema fields
        schemas = []
        if hasattr(ctx, 'schemaFieldNames'):
            try:
                schemas = list(ctx.schemaFieldNames())
            except Exception as e:
                schemas = ["error: %s" % e]
        info["schema_fields"] = schemas

        # Patient-related attrs
        pat_attrs = []
        for x in dir(ctx):
            if 'Patient' in x or 'patient' in x or 'getSample' in x or 'getPatient' in x:
                pat_attrs.append(x)
        info["pat_attrs"] = pat_attrs[:20]

        # Analyses
        if hasattr(ctx, 'getAnalyses'):
            try:
                info["analyses"] = [a.Title() for a in ctx.getAnalyses()]
            except Exception as e:
                info["analyses"] = "error: %s" % e

        # Contact
        if hasattr(ctx, 'getContact'):
            try:
                c = ctx.getContact()
                info["contact"] = c.Title() if c else None
            except Exception as e:
                info["contact"] = "error: %s" % e

        return json.dumps(info, indent=2, ensure_ascii=False)
