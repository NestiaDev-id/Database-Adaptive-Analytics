"""
Analysis Intent Model
Database-agnostic analysis specification for LAM architecture
"""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class FilterOperator(str, Enum):
    """Supported filter operators"""
    EQ = "eq"      # equals
    NE = "ne"      # not equals
    GT = "gt"      # greater than
    LT = "lt"      # less than
    GTE = "gte"    # greater than or equal
    LTE = "lte"    # less than or equal
    IN = "in"      # in list
    NOT_IN = "not_in"  # not in list
    LIKE = "like"  # contains/pattern (SQL LIKE)
    IS_NULL = "is_null"  # is null
    IS_NOT_NULL = "is_not_null"  # is not null


class AggregateFunction(str, Enum):
    """Supported aggregate functions"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"


class SortDirection(str, Enum):
    """Sort direction"""
    ASC = "asc"
    DESC = "desc"


class IntentType(str, Enum):
    """Types of analysis intent"""
    SELECT = "select"        # Simple data retrieval
    AGGREGATE = "aggregate"  # Aggregation with GROUP BY
    TIME_SERIES = "time_series"  # Time-based analysis
    TOP_N = "top_n"         # Top N records


class Filter(BaseModel):
    """Single filter condition"""
    field: str
    op: FilterOperator
    value: Any


class Aggregation(BaseModel):
    """Single aggregation specification"""
    func: AggregateFunction
    field: str = "*"  # Use "*" for COUNT(*)
    alias: str  # Output column name


class OrderBy(BaseModel):
    """Single order by specification"""
    field: str
    direction: SortDirection = SortDirection.ASC


class AnalysisIntent(BaseModel):
    """
    Database-agnostic analysis specification.
    LLM generates this, adapters translate to SQL/NoSQL.
    """
    intent_type: IntentType = Field(
        description="Type of analysis: select, aggregate, time_series, top_n"
    )
    target_entity: str = Field(
        description="Table or collection name"
    )
    fields: Optional[list[str]] = Field(
        default=[],
        description="Columns/fields to select. Empty means SELECT *"
    )
    filters: Optional[list[Filter]] = Field(
        default=[],
        description="WHERE conditions"
    )
    aggregations: Optional[list[Aggregation]] = Field(
        default=[],
        description="Aggregate functions to apply"
    )
    group_by: Optional[list[str]] = Field(
        default=[],
        description="Fields to group by"
    )
    order_by: Optional[list[OrderBy]] = Field(
        default=[],
        description="Sort specification"
    )
    limit: Optional[int] = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return"
    )
    # Time series specific
    time_field: Optional[str] = Field(
        default=None,
        description="Date/timestamp field for time series analysis"
    )
    time_granularity: Optional[str] = Field(
        default=None,
        description="Time grouping: hour, day, week, month, quarter, year"
    )


class AnalysisResponse(BaseModel):
    """Complete LLM response with analysis intent"""
    interpretation: str = Field(
        description="Brief explanation of what user wants"
    )
    analysis_intent: AnalysisIntent = Field(
        description="Structured analysis specification"
    )
    visualization: str = Field(
        default="table",
        description="Recommended visualization: table, bar, line, pie, scatter"
    )
    insights: str = Field(
        default="",
        description="Expected business insights from this analysis"
    )
