# Pydantic Plan Schema
from pydantic import BaseModel, Field    
from typing import List, Optional, Literal, Any

OpEnum = Literal["eq","neq","gt","gte","lt","lte","contains","in"]

class TimeRange(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    timezone: Optional[str] = None

class FilterItem(BaseModel):
    field: str
    op: OpEnum
    value: Any

class AggregationTerm(BaseModel):
    type: Literal["terms"]
    field: str
    size: Optional[int] = Field(10, le=50)

class AggregationCount(BaseModel):
    type: Literal["count"]

Aggregation = Optional[dict]  # we validate aggregation server-side (see validators)

class WazuhSearchPlan(BaseModel):
    indices: str
    time: TimeRange
    filters: Optional[List[FilterItem]] = []
    must_not: Optional[List[FilterItem]] = []
    query_string: Optional[str] = None
    aggregation: Optional[dict] = None
    limit: Optional[int] = Field(50, le=200)
    dry_run: Optional[bool] = False

    model_config = {
        "populate_by_name": True
    }


        

        
