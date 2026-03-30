"""
Oracle Database Connector
"""
from typing import Optional
import oracledb

from api.app.services.database.base import BaseDatabaseConnector


class OracleConnector(BaseDatabaseConnector):
    """Oracle database connector using oracledb (python-oracledb)"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str  # This is the service name or SID
    ):
        super().__init__(host, port, username, password, database)
        self._connection: Optional[oracledb.Connection] = None
    
    async def connect(self) -> bool:
        """Establish connection to Oracle"""
        try:
            # Using oracledb thin mode (no Oracle client required)
            oracledb.init_oracle_client(lib_dir=None)  # Thin mode
            
            dsn = f"{self.host}:{self.port or 1521}/{self.database}"
            
            self._connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=dsn
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Oracle: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close Oracle connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test Oracle connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
            version = cursor.fetchone()[0]
            await self.disconnect()
            return True, f"Connected successfully. {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of tables from Oracle"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT table_name FROM user_tables ORDER BY table_name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    async def get_schema(self) -> str:
        """Get Oracle schema DDL"""
        if not self._connection:
            await self.connect()
        
        tables = await self.get_tables()
        schema_ddl = []
        
        cursor = self._connection.cursor()
        
        for table in tables:
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    nullable,
                    data_default
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """, {'table_name': table})
            
            columns = cursor.fetchall()
            ddl = f"CREATE TABLE {table} (\n"
            
            col_defs = []
            for col in columns:
                col_name, data_type, data_len, nullable, default = col
                col_def = f"  {col_name} {data_type}"
                
                if data_type in ('VARCHAR2', 'CHAR'):
                    col_def += f"({data_len})"
                
                if nullable == 'N':
                    col_def += " NOT NULL"
                
                if default:
                    col_def += f" DEFAULT {default.strip()}"
                
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
