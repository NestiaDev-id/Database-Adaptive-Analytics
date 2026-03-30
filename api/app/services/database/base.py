"""
Base Database Connector
Abstract base class untuk semua database connectors
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseDatabaseConnector(ABC):
    """Abstract base class for database connectors"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to database"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test database connection
        
        Returns:
            Tuple of (success, message)
        """
        pass
    
    @abstractmethod
    async def get_tables(self) -> list[str]:
        """Get list of table names"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> str:
        """Get database schema as DDL statements"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """
        Execute a read-only SQL query
        
        Args:
            query: SQL query to execute
            
        Returns:
            Tuple of (column_names, rows as list of dicts)
        """
        pass
    
    def _validate_read_only(self, query: str) -> bool:
        """Validate that query is read-only (SELECT only)"""
        forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
        query_upper = query.upper().strip()
        
        for keyword in forbidden:
            if keyword in query_upper:
                return False
        
        return query_upper.startswith('SELECT') or query_upper.startswith('WITH')
