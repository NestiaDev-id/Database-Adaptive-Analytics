"""
SQL Server Database Connector
"""
from typing import Optional
import pymssql

from api.app.services.database.base import BaseDatabaseConnector


class SQLServerConnector(BaseDatabaseConnector):
    """SQL Server database connector using pymssql"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str
    ):
        super().__init__(host, port, username, password, database)
        self._connection: Optional[pymssql.Connection] = None
    
    async def connect(self) -> bool:
        """Establish connection to SQL Server"""
        try:
            self._connection = pymssql.connect(
                server=self.host,
                port=str(self.port) if self.port else "1433",
                user=self.username,
                password=self.password,
                database=self.database
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close SQL Server connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test SQL Server connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0]
            # Extract simpler version info
            version = version_info.split('\n')[0][:50]
            await self.disconnect()
            return True, f"Connected successfully. {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of tables from SQL Server"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    async def get_schema(self) -> str:
        """Get SQL Server schema DDL"""
        if not self._connection:
            await self.connect()
        
        tables = await self.get_tables()
        schema_ddl = []
        
        cursor = self._connection.cursor()
        
        for table in tables:
            # Get table schema
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (table,))
            
            columns = cursor.fetchall()
            ddl = f"CREATE TABLE {table} (\n"
            
            col_defs = []
            for col in columns:
                col_name, data_type, max_len, is_null, default = col
                col_def = f"  {col_name} {data_type}"
                
                if max_len:
                    col_def += f"({max_len})"
                
                if is_null == 'NO':
                    col_def += " NOT NULL"
                
                if default:
                    col_def += f" DEFAULT {default}"
                
                col_defs.append(col_def)
            
            ddl += ",\n".join(col_defs) + "\n)"
            schema_ddl.append(ddl)
        
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
