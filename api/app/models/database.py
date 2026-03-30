"""
Database Connection Models
Pydantic schemas untuk koneksi database
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "PostgreSQL"
    MYSQL = "MySQL"
    SQLSERVER = "SQL Server"
    SQLITE = "SQLite"
    ORACLE = "Oracle"
    SNOWFLAKE = "Snowflake"
    BIGQUERY = "BigQuery"
    MONGODB = "MongoDB"


class DbConnection(BaseModel):
    """Database connection configuration"""
    host: str = Field(default="", description="Database host address")
    port: int = Field(default=0, description="Database port")
    username: str = Field(default="", description="Database username")
    password: str = Field(default="", description="Database password")
    database: str = Field(default="", description="Database name")
    type: DatabaseType = Field(default=DatabaseType.POSTGRESQL, description="Database type")
    connection_string: Optional[str] = Field(default=None, description="Full connection string (URI) override")
    
    class Config:
        use_enum_values = True


class DbContext(BaseModel):
    """Full database context including connection and schema"""
    connection: DbConnection = Field(default_factory=DbConnection)
    schema: str = Field(default="", description="Database schema DDL statements")
    selectedModel: str = Field(default="Gemini (Google)", description="Selected AI model")
    apiKey: Optional[str] = Field(default=None, description="API key for the selected model")
    
    class Config:
        use_enum_values = True


class ConnectionTestRequest(BaseModel):
    """Request model for testing database connection"""
    connection: DbConnection


class ConnectionTestResponse(BaseModel):
    """Response model for database connection test"""
    success: bool
    message: str
    tables: Optional[list[str]] = None


class SchemaResponse(BaseModel):
    """Response model for schema retrieval"""
    success: bool
    schema_ddl: Optional[str] = None
    tables: Optional[list[dict]] = None
    error: Optional[str] = None


class QueryExecuteRequest(BaseModel):
    """Request model for executing a SQL query"""
    connection: DbConnection
    query: str = Field(..., description="SQL query to execute (READ-ONLY)")


class QueryExecuteResponse(BaseModel):
    """Response model for query execution"""
    success: bool
    columns: Optional[list[str]] = None
    rows: Optional[list[dict]] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
