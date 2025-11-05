# app/tests/test_schema.py

import pytest
from pydantic import ValidationError
from app.schemas import WazuhSearchPlan, TimeRange, Filter

def test_valid_schema():
    """✅ Should create a valid WazuhSearchPlan instance."""
    data = {
        "indices": ["alerts-*"],
        "time": {"from_": "2025-11-01T00:00:00Z", "to": "2025-11-05T00:00:00Z"},
        "filters": [{"field": "rule.level", "operator": "gte", "value": 5}],
        "must_not": [],
        "dry_run": False
    }
    plan = WazuhSearchPlan(**data)
    assert plan.indices == ["alerts-*"]
    assert plan.filters[0].field == "rule.level"
    assert plan.filters[0].operator == "gte"

def test_missing_time_field():
    """❌ Missing 'time' field should raise ValidationError."""
    data = {
        "indices": ["alerts-*"],
        "filters": [{"field": "rule.level", "operator": "gte", "value": 5}],
        "must_not": []
    }
    with pytest.raises(ValidationError):
        WazuhSearchPlan(**data)

def test_invalid_operator_type():
    """❌ Operator must be a string."""
    data = {
        "indices": ["alerts-*"],
        "time": {"from_": "2025-11-01T00:00:00Z", "to": "2025-11-05T00:00:00Z"},
        "filters": [{"field": "rule.level", "operator": 123, "value": 5}],
        "must_not": []
    }
    with pytest.raises(ValidationError):
        WazuhSearchPlan(**data)

def test_time_range_format():
    """❌ Invalid ISO time format should raise error."""
    data = {
        "indices": ["alerts-*"],
        "time": {"from_": "Nov 1 2025", "to": "Nov 5 2025"},
        "filters": [],
        "must_not": []
    }
    with pytest.raises(ValidationError):
        WazuhSearchPlan(**data)
