# app/tests/test_dsl_builder.py

import pytest
from app.dsl_builder import build_dsl
from app.schemas import WazuhSearchPlan, TimeRange, Filter

def test_build_dsl_basic():
    """✅ Test a basic DSL construction with one filter."""
    plan = WazuhSearchPlan(
        indices=["alerts-*"],
        time=TimeRange(from_="2025-11-01T00:00:00Z", to="2025-11-05T00:00:00Z"),
        filters=[Filter(field="rule.level", operator="gte", value=5)],
        must_not=[],
        dry_run=False
    )

    dsl = build_dsl(plan)
    assert "query" in dsl
    assert "bool" in dsl["query"]
    assert "range" in str(dsl)
    assert "gte" in str(dsl)

def test_build_dsl_with_multiple_filters():
    """✅ Test multiple filters (AND condition)."""
    plan = WazuhSearchPlan(
        indices=["alerts-*"],
        time=TimeRange(from_="2025-11-01T00:00:00Z", to="2025-11-05T00:00:00Z"),
        filters=[
            Filter(field="rule.level", operator="gte", value=10),
            Filter(field="agent.name", operator="eq", value="WazuhAgent1")
        ],
        must_not=[],
        dry_run=False
    )

    dsl = build_dsl(plan)
    assert "must" in dsl["query"]["bool"]
    assert len(dsl["query"]["bool"]["must"]) == 3  # 2 filters + 1 time range

def test_build_dsl_with_must_not_filters():
    """✅ Test negated filters (NOT condition)."""
    plan = WazuhSearchPlan(
        indices=["alerts-*"],
        time=TimeRange(from_="2025-11-01T00:00:00Z", to="2025-11-05T00:00:00Z"),
        filters=[],
        must_not=[Filter(field="agent.status", operator="eq", value="inactive")],
        dry_run=False
    )

    dsl = build_dsl(plan)
    assert "must_not" in dsl["query"]["bool"]
    assert "inactive" in str(dsl)

def test_build_dsl_invalid_operator():
    """❌ Test unsupported operator should raise exception."""
    plan = WazuhSearchPlan(
        indices=["alerts-*"],
        time=TimeRange(from_="2025-11-01T00:00:00Z", to="2025-11-05T00:00:00Z"),
        filters=[Filter(field="rule.id", operator="invalid_op", value=1001)],
        must_not=[],
        dry_run=False
    )

    with pytest.raises(ValueError):
        build_dsl(plan)
