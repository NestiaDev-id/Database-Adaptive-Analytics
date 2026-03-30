"""
Adapter Factory
Factory for creating database-specific query adapters
"""
from api.app.services.adapters.base import BaseQueryAdapter
from api.app.services.adapters.sql_adapter import SQLAdapter
from api.app.services.adapters.nosql_adapter import MongoDBAdapter


class AdapterFactory:
    """
    Factory for creating query adapters based on database type.
    """
    
    # SQL databases and their dialects
    SQL_DATABASES = {
        "postgresql": "postgresql",
        "mysql": "mysql",
        "sqlite": "sqlite",
        "sql server": "sqlserver",
        "oracle": "oracle",
        "snowflake": "snowflake",
        "bigquery": "bigquery",
    }
    
    # NoSQL databases
    NOSQL_DATABASES = {
        "mongodb": MongoDBAdapter,
    }
    
    @classmethod
    def get_adapter(cls, db_type: str) -> BaseQueryAdapter:
        """
        Get the appropriate adapter for the given database type.
        
        Args:
            db_type: Database type (e.g., "PostgreSQL", "MongoDB")
            
        Returns:
            Appropriate query adapter instance
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type_lower = db_type.lower()
        
        # Check if it's a SQL database
        if db_type_lower in cls.SQL_DATABASES:
            dialect = cls.SQL_DATABASES[db_type_lower]
            return SQLAdapter(dialect=dialect)
        
        # Check if it's a NoSQL database
        if db_type_lower in cls.NOSQL_DATABASES:
            adapter_class = cls.NOSQL_DATABASES[db_type_lower]
            return adapter_class()
        
        # Default to SQL adapter (PostgreSQL dialect)
        return SQLAdapter(dialect="postgresql")
    
    @classmethod
    def get_supported_databases(cls) -> list[str]:
        """Return list of all supported database types"""
        sql_dbs = list(cls.SQL_DATABASES.keys())
        nosql_dbs = list(cls.NOSQL_DATABASES.keys())
        return sql_dbs + nosql_dbs
    
    @classmethod
    def is_sql_database(cls, db_type: str) -> bool:
        """Check if the database type is a SQL database"""
        return db_type.lower() in cls.SQL_DATABASES
    
    @classmethod
    def is_nosql_database(cls, db_type: str) -> bool:
        """Check if the database type is a NoSQL database"""
        return db_type.lower() in cls.NOSQL_DATABASES
