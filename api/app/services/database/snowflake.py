"""
Snowflake Database Connector
"""
from typing import Optional
import snowflake.connector

from api.app.services.database.base import BaseDatabaseConnector


class SnowflakeConnector(BaseDatabaseConnector):
    """Snowflake database connector"""
    
    def __init__(
        self,
        host: str,  # account identifier (e.g., xy12345.us-east-1)
        port: int,
        username: str,
        password: str,
        database: str
    ):
        super().__init__(host, port, username, password, database)
        self._connection: Optional[snowflake.connector.SnowflakeConnection] = None
        # Extract warehouse and schema from database if provided
        # Format: database/schema or database/schema/warehouse
        db_parts = self.database.split('/')
        self.db_name = db_parts[0] if db_parts else self.database
        self.schema = db_parts[1] if len(db_parts) > 1 else "PUBLIC"
        self.warehouse = db_parts[2] if len(db_parts) > 2 else None
    
    async def connect(self) -> bool:
        """Establish connection to Snowflake"""
        try:
            conn_params = {
                'user': self.username,
                'password': self.password,
                'account': self.host,
                'database': self.db_name,
                'schema': self.schema,
            }
            
            if self.warehouse:
                conn_params['warehouse'] = self.warehouse
            
            self._connection = snowflake.connector.connect(**conn_params)
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Snowflake: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close Snowflake connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test Snowflake connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            await self.disconnect()
            return True, f"Connected successfully. Snowflake {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of tables from Snowflake"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute(f"SHOW TABLES IN {self.db_name}.{self.schema}")
        tables = [row[1] for row in cursor.fetchall()]  # Column 1 is table name
        return tables
    
    async def get_schema(self) -> str:
        """Get Snowflake schema DDL"""
        if not self._connection:
            await self.connect()
        
        tables = await self.get_tables()
        schema_ddl = []
        
        cursor = self._connection.cursor()
        
        for table in tables:
            cursor.execute(f"DESCRIBE TABLE {self.db_name}.{self.schema}.{table}")
            columns = cursor.fetchall()
            
            ddl = f"CREATE TABLE {table} (\n"
            col_defs = []
            
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                nullable = col[3]
                default = col[4]
                
                col_def = f"  {col_name} {col_type}"
                
                if nullable == 'N':
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
