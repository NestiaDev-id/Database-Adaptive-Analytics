"""
Database Factory
Factory pattern untuk memilih database connector berdasarkan type
"""
from typing import Optional

from api.app.services.database.base import BaseDatabaseConnector
from api.app.services.database.postgresql import PostgreSQLConnector
from api.app.services.database.mysql import MySQLConnector
from api.app.services.database.mongodb import MongoDBConnector
from api.app.services.database.sqlite import SQLiteConnector
from api.app.services.database.sqlserver import SQLServerConnector
from api.app.services.database.oracle import OracleConnector
from api.app.services.database.snowflake import SnowflakeConnector
from api.app.services.database.bigquery import BigQueryConnector
from api.app.models.database import DbConnection, DatabaseType


class DatabaseFactory:
    """Factory class untuk membuat database connector instances"""
    
    _connectors = {
        DatabaseType.POSTGRESQL: PostgreSQLConnector,
        DatabaseType.MYSQL: MySQLConnector,
        DatabaseType.MONGODB: MongoDBConnector,
        DatabaseType.SQLSERVER: SQLServerConnector,
        DatabaseType.SQLITE: SQLiteConnector,
        DatabaseType.ORACLE: OracleConnector,
        DatabaseType.SNOWFLAKE: SnowflakeConnector,
        DatabaseType.BIGQUERY: BigQueryConnector,
    }
    
    @classmethod
    def get_connector(cls, connection: DbConnection) -> BaseDatabaseConnector:
        """
        Get database connector instance based on database type
        
        Args:
            connection: Database connection configuration
            
        Returns:
            Database connector instance
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type = connection.type
        
        # Handle string values
        if isinstance(db_type, str):
            # Convert string to enum
            for dtype in DatabaseType:
                if dtype.value == db_type:
                    db_type = dtype
                    break
        
        if db_type not in cls._connectors:
            available = ", ".join([dt.value for dt in cls._connectors.keys()])
            raise ValueError(f"Database type '{db_type}' is not yet supported. Available: {available}")
        
        connector_class = cls._connectors[db_type]
        
        # Fallback to settings if fields are empty
        from api.app.utils.config import settings
        
        # Priority 1: Full URI (connection_string from frontend or DB_URI from .env)
        # Handle masked input
        conn_str_input = connection.connection_string
        if conn_str_input and "******" in conn_str_input:
             conn_str_input = None
             
        connection_string = conn_str_input or settings.DB_URI
        
        host = connection.host or settings.DB_HOST
        # If connection_string is available, use it as 'host' for connectors that support it
        if connection_string:
            host = connection_string
            
        port = connection.port or settings.DB_PORT
        username = connection.username or settings.DB_USER
        password = connection.password or settings.DB_PASS
        database = connection.database or settings.DB_NAME
        
        return connector_class(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )
    
    @classmethod
    def list_supported_databases(cls) -> list[str]:
        """List all supported database types"""
        return [dt.value for dt in cls._connectors.keys()]

    @classmethod
    def get_configuration_status(cls) -> dict[str, bool]:
        """
        Get status of availability for each database type based on settings.
        Returns:
            Dict[db_type, is_configured]
        """
        from api.app.utils.config import settings
        
        # Initialize all as False
        status = {dt.value: False for dt in cls._connectors.keys()}
        
        # Check if we have any configuration at all
        has_config = bool(settings.DB_URI or settings.DB_HOST)
        
        if has_config:
            # 1. Check explicit DB_TYPE setting
            config_type = settings.DB_TYPE
            
            # Match config_type against supported types (case-insensitive)
            for dt in cls._connectors.keys():
                if dt.value.lower() == config_type.lower():
                    status[dt.value] = True
            
            # 2. Heuristic: Check DB_URI protocol to detect type regardless of DB_TYPE
            # This helps if user sets DB_URI but forgets to change DB_TYPE
            if settings.DB_URI:
                uri = settings.DB_URI.lower()
                if "mongodb" in uri:
                    status["MongoDB"] = True
                elif "postgres" in uri:
                    status["PostgreSQL"] = True
                elif "mysql" in uri:
                    status["MySQL"] = True
                elif "sqlserver" in uri or "mssql" in uri:
                    status["SQL Server"] = True
                elif "sqlite" in uri:
                    status["SQLite"] = True
                elif "oracle" in uri:
                    status["Oracle"] = True
                    
        return status
