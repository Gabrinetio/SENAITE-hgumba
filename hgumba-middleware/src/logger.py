import logging
import logging.handlers
import json
from datetime import datetime, timezone


class JSONAuditFormatter(logging.Formatter):
    """Formatter que serializa logs em JSON estruturado para auditoria."""

    def format(self, record) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "audit_data"):
            log_obj["audit_data"] = record.audit_data
        return json.dumps(log_obj, ensure_ascii=False)


audit_logger = logging.getLogger("HGUMBA-Audit")
_audit_stream = logging.StreamHandler()
_audit_stream.setFormatter(JSONAuditFormatter())
audit_logger.addHandler(_audit_stream)
_audit_file = logging.handlers.RotatingFileHandler(
    "audit.log", maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
)
_audit_file.setFormatter(JSONAuditFormatter())
audit_logger.addHandler(_audit_file)
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False
