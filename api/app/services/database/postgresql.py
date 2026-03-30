"""
PostgreSQL Database Connector
"""
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from api.app.services.database.base import BaseDatabaseConnector


class PostgreSQLConnector(BaseDatabaseConnector):
    """PostgreSQL database connector"""
    
    async def connect(self) -> bool:
        """Establish connection to PostgreSQL"""
        try:
            # Check if host is a connection string
            if self.host and (self.host.startswith("postgresql://") or self.host.startswith("postgres://")):
                self._connection = psycopg2.connect(self.host)
            else:
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    database=self.database
                )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    async def test_connection(self) -> tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            await self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            await self.disconnect()
            return True, f"Connected successfully. {version}"
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> list[str]:
        """Get list of table names from PostgreSQL"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    async def get_schema(self) -> str:
        """Get PostgreSQL schema as DDL"""
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor()
        tables = await self.get_tables()
        
        ddl_statements = []
        for table in tables:
            # Get columns
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}' AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            # Build CREATE TABLE statement
            cols_ddl = []
            for col_name, data_type, nullable, default in columns:
                col_def = f"    {col_name} {data_type.upper()}"
                if nullable == 'NO':
                    col_def += " NOT NULL"
                if default:
                    col_def += f" DEFAULT {default}"
                cols_ddl.append(col_def)
            
            ddl = f"CREATE TABLE {table} (\n" + ",\n".join(cols_ddl) + "\n);"
            ddl_statements.append(ddl)
        
        cursor.close()
        return "\n\n".join(ddl_statements)
    
    async def execute_query(self, query: str) -> tuple[list[str], list[dict]]:
        """Execute a read-only SQL query on PostgreSQL"""
        if not self._validate_read_only(query):
            raise ValueError("Only SELECT queries are allowed (read-only mode)")
        
        if not self._connection:
            await self.connect()
        
        cursor = self._connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        return columns, rows
