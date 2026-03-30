"""
MongoDB Query Adapter
Translates AnalysisIntent to MongoDB aggregation pipelines
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


class MongoDBAdapter(BaseQueryAdapter):
    """
    Adapter for MongoDB.
    Translates AnalysisIntent into MongoDB aggregation pipeline.
    """
    
    # Operator mapping to MongoDB operators
    OPERATOR_MAP = {
        FilterOperator.EQ: "$eq",
        FilterOperator.NE: "$ne",
        FilterOperator.GT: "$gt",
        FilterOperator.LT: "$lt",
        FilterOperator.GTE: "$gte",
        FilterOperator.LTE: "$lte",
        FilterOperator.IN: "$in",
        FilterOperator.NOT_IN: "$nin",
        FilterOperator.LIKE: "$regex",
    }
    
    # Aggregate function mapping
    AGG_FUNC_MAP = {
        AggregateFunction.COUNT: "$sum",  # Use $sum with 1
        AggregateFunction.SUM: "$sum",
        AggregateFunction.AVG: "$avg",
        AggregateFunction.MIN: "$min",
        AggregateFunction.MAX: "$max",
        AggregateFunction.COUNT_DISTINCT: "$addToSet",  # Special handling
    }
    
    def get_query_type(self) -> str:
        return "mongodb"
    
    def build_query(self, intent: AnalysisIntent, schema: dict | None = None) -> str:
        """
        Build MongoDB query from AnalysisIntent.
        Returns a MongoDB shell command string for clean display.
        """
        if intent.intent_type == IntentType.SELECT:
            return self._build_find_string(intent)
        elif intent.intent_type in (IntentType.AGGREGATE, IntentType.TIME_SERIES, IntentType.TOP_N):
            return self._build_aggregate_string(intent)
        else:
            return self._build_find_string(intent)
    
    def _build_find_string(self, intent: AnalysisIntent) -> str:
        """Build MongoDB find query as shell command string"""
        import json
        
        collection = intent.target_entity
        
        # Build filter
        query = {}
        if intent.filters:
            query = self._build_match(intent.filters)
        
        # Build projection
        projection = None
        if intent.fields and intent.fields != ["*"]:
            projection = {f: 1 for f in intent.fields}
        
        # Start building command
        if projection:
            cmd = f"db.{collection}.find({json.dumps(query)}, {json.dumps(projection)})"
        else:
            cmd = f"db.{collection}.find({json.dumps(query)})"
        
        # Add sort
        if intent.order_by:
            sort_obj = {}
            for ob in intent.order_by:
                direction = -1 if ob.direction == SortDirection.DESC else 1
                sort_obj[ob.field] = direction
            cmd += f".sort({json.dumps(sort_obj)})"
        
        # Add limit
        limit = intent.limit or 100
        cmd += f".limit({limit})"
        
        return cmd
    
    def _build_aggregate_string(self, intent: AnalysisIntent) -> str:
        """Build MongoDB aggregation pipeline as shell command string"""
        import json
        
        collection = intent.target_entity
        pipeline = []
        
        # $match stage
        if intent.filters:
            match_stage = {"$match": self._build_match(intent.filters)}
            pipeline.append(match_stage)
        
        # $group stage
        if intent.aggregations or intent.group_by:
            group_stage = self._build_group_stage(intent)
            pipeline.append(group_stage)
        
        # $sort stage
        if intent.order_by:
            sort_stage = {"$sort": {}}
            for ob in intent.order_by:
                direction = -1 if ob.direction == SortDirection.DESC else 1
                sort_stage["$sort"][ob.field] = direction
            pipeline.append(sort_stage)
        
        # $limit stage
        limit = intent.limit or 100
        pipeline.append({"$limit": limit})
        
        # $project stage
        if intent.aggregations:
            project_stage = self._build_project_stage(intent)
            if project_stage:
                pipeline.append(project_stage)
        
        # Format as readable string
        pipeline_str = json.dumps(pipeline, indent=2)
        return f"db.{collection}.aggregate({pipeline_str})"
    
    def _build_aggregate(self, intent: AnalysisIntent) -> dict:
        """Build aggregation pipeline"""
        pipeline = []
        
        # $match stage (filtering)
        if intent.filters:
            match_stage = {"$match": self._build_match(intent.filters)}
            pipeline.append(match_stage)
        
        # $group stage
        if intent.aggregations or intent.group_by:
            group_stage = self._build_group_stage(intent)
            pipeline.append(group_stage)
        
        # $sort stage
        if intent.order_by:
            sort_stage = {"$sort": {}}
            for ob in intent.order_by:
                direction = -1 if ob.direction == SortDirection.DESC else 1
                sort_stage["$sort"][ob.field] = direction
            pipeline.append(sort_stage)
        
        # $limit stage
        limit = intent.limit or 100
        pipeline.append({"$limit": limit})
        
        # $project stage to reshape output
        if intent.aggregations:
            project_stage = self._build_project_stage(intent)
            if project_stage:
                pipeline.append(project_stage)
        
        return {
            "collection": intent.target_entity,
            "operation": "aggregate",
            "pipeline": pipeline
        }
    
    def _build_match(self, filters: list) -> dict:
        """Build $match condition from filters"""
        match = {}
        
        for f in filters:
            field = f.field
            op = f.op
            value = f.value
            
            if op == FilterOperator.EQ:
                match[field] = value
            elif op == FilterOperator.IS_NULL:
                match[field] = None
            elif op == FilterOperator.IS_NOT_NULL:
                match[field] = {"$ne": None}
            elif op == FilterOperator.LIKE:
                # Convert SQL LIKE pattern to regex
                match[field] = {"$regex": value, "$options": "i"}
            else:
                mongo_op = self.OPERATOR_MAP.get(op, "$eq")
                match[field] = {mongo_op: value}
        
        return match
    
    def _build_group_stage(self, intent: AnalysisIntent) -> dict:
        """Build $group stage"""
        group = {"$group": {}}
        
        # Build _id for grouping
        if intent.group_by:
            if len(intent.group_by) == 1:
                group["$group"]["_id"] = f"${intent.group_by[0]}"
            else:
                group["$group"]["_id"] = {
                    f: f"${f}" for f in intent.group_by
                }
        else:
            group["$group"]["_id"] = None  # No grouping, single result
        
        # Add aggregations
        for agg in intent.aggregations:
            if agg.func == AggregateFunction.COUNT:
                group["$group"][agg.alias] = {"$sum": 1}
            elif agg.func == AggregateFunction.COUNT_DISTINCT:
                group["$group"][agg.alias] = {"$addToSet": f"${agg.field}"}
            else:
                mongo_func = self.AGG_FUNC_MAP.get(agg.func, "$sum")
                group["$group"][agg.alias] = {mongo_func: f"${agg.field}"}
        
        return group
    
    def _build_project_stage(self, intent: AnalysisIntent) -> dict | None:
        """Build $project stage to reshape output"""
        # Handle COUNT_DISTINCT - need to convert set to size
        for agg in intent.aggregations:
            if agg.func == AggregateFunction.COUNT_DISTINCT:
                project = {"$project": {"_id": 1}}
                for a in intent.aggregations:
                    if a.func == AggregateFunction.COUNT_DISTINCT:
                        project["$project"][a.alias] = {"$size": f"${a.alias}"}
                    else:
                        project["$project"][a.alias] = 1
                return project
        
        return None
