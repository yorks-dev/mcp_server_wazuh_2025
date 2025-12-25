from datetime import datetime, timedelta
from typing import List
from .config import settings
from .schemas import FilterItem

# simple field->type mapping (in a real deploy populate using index mappings)
FIELD_TYPES = {
    # Rule fields
    "rule.id": "keyword",
    "rule.level": "integer",
    "rule.description": "text",
    "rule.mitre.technique": "keyword",
    "rule.mitre.tactic": "keyword",
    # Agent fields
    "agent.name": "keyword",
    "agent.id": "keyword",
    "agent.ip": "ip",
    "agent.os.platform": "keyword",
    # Data fields
    "data.srcip": "ip",
    "data.dstip": "ip",
    "data.srcuser": "keyword",
    "data.dstuser": "keyword",
    "data.srcport": "integer",
    "data.dstport": "integer",
    "data.protocol": "keyword",
    "data.win.eventdata.targetUserName": "keyword",
    "data.win.system.eventID": "keyword",
    "data.win.system.channel": "keyword",
    # Decoder fields
    "decoder.name": "keyword",
    "decoder.parent": "keyword",
    # Other fields
    "@timestamp": "date",
    "timestamp": "date",
    "location": "keyword",
    "full_log": "text",
    "manager.name": "keyword",
    "vulnerability.severity": "keyword",
}
def is_index_allowed(indices: str) -> bool:
    # simple wildcard match
    return any(indices.startswith(allowed.rstrip("*")) for allowed in settings.INDEX_ALLOWLIST)

def field_allowed(field: str) -> bool:
    return field in settings.FIELD_ALLOWLIST

def op_allowed_on_field(op: str, field: str) -> bool:
    ftype = FIELD_TYPES.get(field)
    if not ftype:
        return False
    if op in ("gt","gte","lt","lte") and ftype not in ("integer","date","float"):
        return False
    if op in ("eq","in") and ftype == "text":
        # require .keyword in builder instead
        return False
    return True

def enforce_time_window(from_s: str, to_s: str) -> bool:
    fmt = "%Y-%m-%dT%H:%M:%S"  # expect ISO or allow "now-6h" in builder; keep simple here
    # for safety we allow "now" aliases in plan - building layer will interpret
    try:
        # if plan uses relative "now-6h" etc., accept but check extremes elsewhere
        if from_s.startswith("now") or to_s.startswith("now"):
            return True
        f = datetime.fromisoformat(from_s)
        t = datetime.fromisoformat(to_s)
        delta = t - f
        return delta <= timedelta(days=settings.TIME_MAX_DAYS)
    except Exception:
        # if parse fails, reject plan — builder can allow 'now' style
        return False

def validate_filters(filters: List[FilterItem]):
    for f in filters:
        if not field_allowed(f.field):
            raise ValueError(f"field {f.field} not allowed")
        if not op_allowed_on_field(f.op, f.field):
            raise ValueError(f"op {f.op} not allowed on {f.field}")
        
        
