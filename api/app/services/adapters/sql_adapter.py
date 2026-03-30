"""
SQL Query Adapter
Translates AnalysisIntent to SQL queries for relational databases
"""
from typing import Any

from api.app.models.analysis_intent import (
    AnalysisIntent,
    IntentType,
    FilterOperator,
    AggregateFunction,
    SortDirection
)
from api.app.services.adapters.base import BaseQueryAdapter


class SQLAdapter(BaseQueryAdapter):
    """
    Adapter for SQL databases (PostgreSQL, MySQL, SQLite, SQL Server, Oracle)
    Translates AnalysisIntent into standard SQL queries.
    """
    
    # Operator mapping to SQL
    OPERATOR_MAP = {
        FilterOperator.EQ: "=",
        FilterOperator.NE: "!=",
        FilterOperator.GT: ">",
        FilterOperator.LT: "<",
        FilterOperator.GTE: ">=",
        FilterOperator.LTE: "<=",
        FilterOperator.IN: "IN",
        FilterOperator.NOT_IN: "NOT IN",
        FilterOperator.LIKE: "LIKE",
        FilterOperator.IS_NULL: "IS NULL",
        FilterOperator.IS_NOT_NULL: "IS NOT NULL",
    }
    
    # Aggregate function mapping
    AGG_FUNC_MAP = {
        AggregateFunction.COUNT: "COUNT",
        AggregateFunction.SUM: "SUM",
        AggregateFunction.AVG: "AVG",
        AggregateFunction.MIN: "MIN",
        AggregateFunction.MAX: "MAX",
        AggregateFunction.COUNT_DISTINCT: "COUNT(DISTINCT",  # Special handling
    }
    
    def __init__(self, dialect: str = "postgresql"):
        """
        Initialize SQL adapter with specific dialect.
        
        Args:
            dialect: Database dialect (postgresql, mysql, sqlite, sqlserver, oracle)
        """
        self.dialect = dialect.lower()
    
    def get_query_type(self) -> str:
        return "sql"
    
    def build_query(self, intent: AnalysisIntent, schema: dict | None = None) -> str:
        """
        Build SQL query from AnalysisIntent.
        
        Args:
            intent: The analysis intent
            schema: Optional schema for validation
            
        Returns:
            SQL query string
        """
        if intent.intent_type == IntentType.SELECT:
            return self._build_select(intent)
        elif intent.intent_type == IntentType.AGGREGATE:
            return self._build_aggregate(intent)
        elif intent.intent_type == IntentType.TIME_SERIES:
            return self._build_time_series(intent)
        elif intent.intent_type == IntentType.TOP_N:
            return self._build_top_n(intent)
        else:
            return self._build_select(intent)
    
    def _build_select(self, intent: AnalysisIntent) -> str:
        """Build simple SELECT query"""
        parts = []
        
        # SELECT clause
        if intent.fields:
            parts.append(f"SELECT {', '.join(intent.fields)}")
        else:
            parts.append("SELECT *")
        
        # FROM clause
        parts.append(f"FROM {intent.target_entity}")
        
        # WHERE clause
        where_clause = self._build_where(intent.filters)
        if where_clause:
            parts.append(f"WHERE {where_clause}")
        
        # ORDER BY clause
        order_clause = self._build_order_by(intent.order_by)
        if order_clause:
            parts.append(f"ORDER BY {order_clause}")
        
        # LIMIT clause
        limit = intent.limit or 100
        parts.append(f"LIMIT {limit}")
        
        return " ".join(parts)
    
    def _build_aggregate(self, intent: AnalysisIntent) -> str:
        """Build aggregate query with GROUP BY"""
        parts = []
        
        # Build SELECT with aggregations and group by fields
        select_cols = []
        
        # Add GROUP BY fields first
        select_cols.extend(intent.group_by)
        
        # Add aggregations
        for agg in intent.aggregations:
            agg_sql = self._build_aggregation(agg)
            select_cols.append(agg_sql)
        
        if not select_cols:
            select_cols = ["*"]
        
        parts.append(f"SELECT {', '.join(select_cols)}")
        
        # FROM clause
        parts.append(f"FROM {intent.target_entity}")
        
        # WHERE clause
        where_clause = self._build_where(intent.filters)
        if where_clause:
            parts.append(f"WHERE {where_clause}")
        
        # GROUP BY clause
        if intent.group_by:
            parts.append(f"GROUP BY {', '.join(intent.group_by)}")
        
        # ORDER BY clause
        order_clause = self._build_order_by(intent.order_by)
        if order_clause:
            parts.append(f"ORDER BY {order_clause}")
        
        # LIMIT clause
        limit = intent.limit or 100
        parts.append(f"LIMIT {limit}")
        
        return " ".join(parts)
    
    def _build_time_series(self, intent: AnalysisIntent) -> str:
        """Build time series query with date truncation"""
        parts = []
        
        # Date truncation based on dialect
        time_expr = self._build_time_truncation(
            intent.time_field,
            intent.time_granularity
        )
        
        # Build SELECT
        select_cols = [f"{time_expr} AS time_period"]
        
        for agg in intent.aggregations:
            agg_sql = self._build_aggregation(agg)
            select_cols.append(agg_sql)
        
        parts.append(f"SELECT {', '.join(select_cols)}")
        
        # FROM clause
        parts.append(f"FROM {intent.target_entity}")
        
        # WHERE clause
        where_clause = self._build_where(intent.filters)
        if where_clause:
            parts.append(f"WHERE {where_clause}")
        
        # GROUP BY time period
        parts.append(f"GROUP BY time_period")
        
        # ORDER BY time
        parts.append("ORDER BY time_period ASC")
        
        # LIMIT
        limit = intent.limit or 100
        parts.append(f"LIMIT {limit}")
        
        return " ".join(parts)
    
    def _build_top_n(self, intent: AnalysisIntent) -> str:
        """Build TOP N query (similar to aggregate but with ordering)"""
        return self._build_aggregate(intent)
    
    def _build_where(self, filters: list) -> str:
        """Build WHERE clause from filters"""
        if not filters:
            return ""
        
        conditions = []
        for f in filters:
            cond = self._build_condition(f)
            if cond:
                conditions.append(cond)
        
        return " AND ".join(conditions)
    
    def _build_condition(self, filter_obj) -> str:
        """Build single filter condition"""
        field = filter_obj.field
        op = filter_obj.op
        value = filter_obj.value
        
        sql_op = self.OPERATOR_MAP.get(op, "=")
        
        # Handle special operators
        if op == FilterOperator.IS_NULL:
            return f"{field} IS NULL"
        elif op == FilterOperator.IS_NOT_NULL:
            return f"{field} IS NOT NULL"
        elif op in (FilterOperator.IN, FilterOperator.NOT_IN):
            if isinstance(value, list):
                formatted_values = ", ".join(self._format_value(v) for v in value)
                return f"{field} {sql_op} ({formatted_values})"
            else:
                return f"{field} {sql_op} ({self._format_value(value)})"
        elif op == FilterOperator.LIKE:
            return f"{field} LIKE {self._format_value(f'%{value}%')}"
        else:
            return f"{field} {sql_op} {self._format_value(value)}"
    
    def _build_aggregation(self, agg) -> str:
        """Build aggregation expression"""
        func_name = self.AGG_FUNC_MAP.get(agg.func, "COUNT")
        
        if agg.func == AggregateFunction.COUNT_DISTINCT:
            return f"COUNT(DISTINCT {agg.field}) AS {agg.alias}"
        else:
            return f"{func_name}({agg.field}) AS {agg.alias}"
    
    def _build_order_by(self, order_by_list: list) -> str:
        """Build ORDER BY clause"""
        if not order_by_list:
            return ""
        
        parts = []
        for ob in order_by_list:
            direction = "DESC" if ob.direction == SortDirection.DESC else "ASC"
            parts.append(f"{ob.field} {direction}")
        
        return ", ".join(parts)
    
    def _build_time_truncation(self, field: str, granularity: str) -> str:
        """Build date truncation expression based on dialect"""
        gran = granularity.lower() if granularity else "day"
        
        if self.dialect == "postgresql":
            return f"DATE_TRUNC('{gran}', {field})"
        elif self.dialect == "mysql":
            if gran == "day":
                return f"DATE({field})"
            elif gran == "month":
                return f"DATE_FORMAT({field}, '%Y-%m-01')"
            elif gran == "year":
                return f"DATE_FORMAT({field}, '%Y-01-01')"
            else:
                return f"DATE({field})"
        elif self.dialect == "sqlite":
            if gran == "day":
                return f"DATE({field})"
            elif gran == "month":
                return f"strftime('%Y-%m', {field})"
            elif gran == "year":
                return f"strftime('%Y', {field})"
            else:
                return f"DATE({field})"
        else:
            # Default to PostgreSQL style
            return f"DATE_TRUNC('{gran}', {field})"
    
    def _format_value(self, value: Any) -> str:
        """Format value for SQL query"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            return f"'{str(value)}'"
