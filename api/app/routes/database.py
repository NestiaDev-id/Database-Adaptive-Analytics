"""
Database API Routes
Endpoints untuk database connection, schema, dan query execution
"""
from fastapi import APIRouter, HTTPException

from api.app.models.database import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    SchemaResponse,
    QueryExecuteRequest,
    QueryExecuteResponse,
    DbConnection
)
from api.app.services.database.factory import DatabaseFactory

router = APIRouter()


@router.post("/connect", response_model=ConnectionTestResponse)
async def test_database_connection(request: ConnectionTestRequest):
    """
    Test koneksi ke database
    
    Returns:
        Success status, message, dan list tables jika berhasil
    """
    try:
        connector = DatabaseFactory.get_connector(request.connection)
        success, message = await connector.test_connection()
        
        tables = None
        if success:
            await connector.connect()
            tables = await connector.get_tables()
            await connector.disconnect()
        
        return ConnectionTestResponse(
            success=success,
            message=message,
            tables=tables
        )
        
    except ValueError as e:
        return ConnectionTestResponse(
            success=False,
            message=str(e),
            tables=None
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection error: {str(e)}",
            tables=None
        )


@router.post("/schema", response_model=SchemaResponse)
async def get_database_schema(connection: DbConnection):
    """
    Retrieve database schema (DDL statements)
    
    Returns:
        Schema DDL dan list tables dengan struktur
    """
    try:
        connector = DatabaseFactory.get_connector(connection)
        await connector.connect()
        
        schema_ddl = await connector.get_schema()
        tables = await connector.get_tables()
        
        await connector.disconnect()
        
        return SchemaResponse(
            success=True,
            schema_ddl=schema_ddl,
            tables=[{"name": t} for t in tables]
        )
        
    except ValueError as e:
        return SchemaResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return SchemaResponse(
            success=False,
            error=f"Failed to retrieve schema: {str(e)}"
        )


@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_sql_query(request: QueryExecuteRequest):
    """
    Execute a READ-ONLY SQL query
    
    WARNING: Only SELECT queries are allowed!
    
    Returns:
        Query results dengan columns dan rows
    """
    try:
        connector = DatabaseFactory.get_connector(request.connection)
        await connector.connect()
        
        columns, rows = await connector.execute_query(request.query)
        
        await connector.disconnect()
        
        return QueryExecuteResponse(
            success=True,
            columns=columns,
            rows=rows,
            row_count=len(rows)
        )
        
    except ValueError as e:
        return QueryExecuteResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        return QueryExecuteResponse(
            success=False,
            error=f"Query execution failed: {str(e)}"
        )


@router.get("/databases")
async def list_supported_databases():
    """List semua database types yang didukung beserta status konfigurasinya"""
    return {
        "supported": DatabaseFactory.list_supported_databases(),
        "status": DatabaseFactory.get_configuration_status()
    }
