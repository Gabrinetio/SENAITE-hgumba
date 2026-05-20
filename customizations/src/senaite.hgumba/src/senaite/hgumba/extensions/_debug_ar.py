import logging as _lg
_lg.getLogger("cdm_debug").info("--- DEBUG ANALYSISREQUEST ---")

ctx = self.context
_lg.getLogger("cdm_debug").info("dir:" + ",".join([x for x in dir(ctx) if 'Patient' in x or 'patient' in x or 'getP' in x]))
_lg.getLogger("cdm_debug").info("SchemaFields:" + ",".join(ctx.schemaFieldNames() if hasattr(ctx, 'schemaFieldNames') else ['no']))
_lg.getLogger("cdm_debug").info("meta_type=%s portal_type=%s", ctx.meta_type, getattr(ctx, 'portal_type', 'none'))

# Check if AnalysisRequest has UID
_lg.getLogger("cdm_debug").info("UID=%s", getattr(ctx, 'UID', lambda: 'none')())

# Check raw data
try:
    _lg.getLogger("cdm_debug").info("patient_field=%s", getattr(ctx, 'Patient', 'NO_PATIENT_FIELD'))
except:
    _lg.getLogger("cdm_debug").info("patient_field=error")
