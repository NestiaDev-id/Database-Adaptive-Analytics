"""
SQLite Database Connector
"""
import sqlite3
from typing import Optional

from api.app.services.database.base import BaseDatabaseConnector


class SQLiteConnector(BaseDatabaseConnector):
    """SQLite database connector"""
    
    def __init__(
        self,
        host: str,  # For SQLite, this is the database file path
        port: int,
        username: str,
        password: str,
        database: str
    ):
        # For SQLite, we use database parameter as the file path
        # or if host is provided, use that
        self.db_path = host if host else database
        self._connection: Optional[sqlite3.Connection] = None
    
    async def connect(self) -> bool:
        """Establish connection to SQLite"""
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQLite: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close SQLite connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test SQLite connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            await self.disconnect()
            return True, f"Connected successfully. SQLite {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of tables from SQLite"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    async def get_schema(self) -> str:
        """Get SQLite schema DDL"""
        if not self._connection:
            await self.connect()
        
        tables = await self.get_tables()
        schema_ddl = []
        
        cursor = self._connection.cursor()
        for table in tables:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
            ddl = cursor.fetchone()
            if ddl:
                schema_ddl.append(ddl[0])
        
        return ";\n\n".join(schema_ddl) + ";"
    
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """Execute a read-only SQL query"""
        self._validate_read_only(query)
        
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = []
        
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))
        
        return columns, rows
