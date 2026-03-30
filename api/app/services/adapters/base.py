"""
Base Query Adapter
Abstract base class for database-specific query adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from api.app.models.analysis_intent import AnalysisIntent


class BaseQueryAdapter(ABC):
    """
    Abstract base class for query adapters.
    Each database type implements its own adapter.
    """
    
    @abstractmethod
    def build_query(self, intent: AnalysisIntent, schema: dict | None = None) -> Any:
        """
        Convert AnalysisIntent to database-specific query.
        
        Args:
            intent: The analysis intent from LLM
            schema: Optional schema information for validation
            
        Returns:
            Database-specific query (SQL string, MongoDB pipeline, etc.)
        """
        pass
    
    @abstractmethod
    def get_query_type(self) -> str:
        """Return the query type (e.g., 'sql', 'mongodb')"""
        pass
