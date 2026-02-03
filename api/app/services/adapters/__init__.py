"""
Adapters Module
Query adapters for translating AnalysisIntent to database-specific queries
"""
from api.app.services.adapters.base import BaseQueryAdapter
from api.app.services.adapters.sql_adapter import SQLAdapter
from api.app.services.adapters.nosql_adapter import MongoDBAdapter
from api.app.services.adapters.factory import AdapterFactory

__all__ = [
    "BaseQueryAdapter",
    "SQLAdapter", 
    "MongoDBAdapter",
    "AdapterFactory"
]
